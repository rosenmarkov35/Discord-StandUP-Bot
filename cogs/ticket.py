import json
import os
from datetime import datetime

import discord
from discord import app_commands, Interaction, Embed, ui
from discord.ext.commands import Cog

from config_utils import load_config, save_config_changes
from utils import user_has_role, get_timezone_from_string

cfg = load_config()
OPEN_TICKETS_FILE = 'open_tickets.json'
tz = get_timezone_from_string(cfg["timezone"])


# ------------------- Utilities -------------------
def load_open_tickets():
    if not os.path.exists(OPEN_TICKETS_FILE):
        return []
    with open(OPEN_TICKETS_FILE, 'r') as f:
        return json.load(f).get("tickets", [])


def save_open_tickets(tickets):
    with open(OPEN_TICKETS_FILE, 'w') as f:
        json.dump({"tickets": tickets}, f, indent=2)


def generate_ticket_id():
    now = datetime.now(tz=tz)
    return f"{now.year}-{now.strftime('%m%d%H%M%S')}"


def validate_ticket_creation():
    tickets = load_open_tickets()
    return len(tickets) < 60


def build_ticket_embed(ticket, assign=False, color=discord.Color.orange()):
    title = f"Ticket: {ticket['title']}"
    if isinstance(assign, str):
        title = assign
    elif not assign:
        title = f"📩 New Ticket: {ticket['title']}"
    elif assign:
        # If assigned
        title = f"❗ Ticket Assigned: {ticket['title']}"

    embed = Embed(
        title=title,
        description=ticket["description"],
        color=color
    )
    embed.add_field(name="🆔 Ticket ID", value=ticket["id"], inline=True)
    embed.add_field(name="📂 Category", value=ticket["category"], inline=True)
    embed.add_field(name="🎯 Priority", value=str(ticket["priority"]), inline=True)
    embed.add_field(name="👤 Submitted by", value=f"<@{ticket['created_by']}>", inline=False)
    embed.add_field(name="🚨 Status", value=ticket.get("status", "Unassigned"), inline=True)

    if ticket.get("assigned_to") or ticket.get("assigned_role"):
        assigned_mentions = []
        if ticket.get("assigned_to"):
            assigned_mentions += [f"<@{uid}>" for uid in ticket["assigned_to"]]
        if ticket.get("assigned_role"):
            assigned_mentions += [f"<@&{rid}>" for rid in ticket["assigned_role"]]
        embed.add_field(name="👥 Assigned To", value=", ".join(assigned_mentions), inline=False)

    if ticket.get("updates"):
        embed.add_field(name="💬 Comments", value="\n".join(ticket.get("updates", [])), inline=False)

    if not assign:
        embed.set_footer(text="Use moderation tools to manage this ticket.")
    embed.timestamp = datetime.now(tz=tz)
    return embed


class CommentModal(ui.Modal, title="💬 Edit Comments"):
    def __init__(self, ticket, message_callback):
        super().__init__()
        self.ticket = ticket
        self.message_callback = message_callback

        # Extract plain comment lines (remove mentions if any)
        existing_comments = "\n".join(
            line.split("**: ", 1)[-1] if "**: " in line else line
            for line in ticket.get("updates", [])
        )

        self.comment_input = ui.TextInput(
            label="Edit Comments",
            style=discord.TextStyle.paragraph,
            placeholder="Each line will be saved as a separate comment.",
            default=existing_comments,
            max_length=1500,
            required=False
        )
        self.add_item(self.comment_input)

    async def on_submit(self, interaction: Interaction):
        comment_text = self.comment_input.value.strip()
        comment_lines = [line.strip() for line in comment_text.splitlines() if line.strip()]

        # Replace updates entirely with the new comments
        self.ticket["updates"] = comment_lines

        # Save updated ticket
        tickets = load_open_tickets()
        for i, t in enumerate(tickets):
            if t["id"] == self.ticket["id"]:
                tickets[i] = self.ticket
                break
        save_open_tickets(tickets)

        await self.message_callback(interaction, self.ticket, f"💬 {interaction.user.mention} updated comments.")


# ------------------- Ticket Actions View -------------------
class TicketActions(ui.View):
    def __init__(self, ticket_id):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id

    @ui.button(label="Assign (Copy Command)", style=discord.ButtonStyle.primary, custom_id="assign_ticket")
    async def assign(self, interaction: Interaction, button: ui.Button):
        command_example = f"/assign ticket_id:{self.ticket_id} assignees:   "
        await interaction.response.send_message(
            f"📋 Copy and paste this command below, using autocomplete to tag people/roles:\n```{command_example}```",
            ephemeral=True
        )

    @ui.button(label="Reject Ticket", style=discord.ButtonStyle.danger, custom_id="reject_ticket")
    async def reject(self, interaction: Interaction, button: ui.Button):
        tickets = load_open_tickets()
        ticket = next((t for t in tickets if t["id"] == self.ticket_id), None)

        if not ticket:
            await interaction.response.send_message("❌ Ticket not found.", ephemeral=True)
            return

        channel_id = ticket.get("mod_channel_id")
        if not channel_id:
            await interaction.response.send_message("⚠️ Failed to locate the mod tickets channel.", ephemeral=True)
            return

        # Fetch channel object
        mod_channel = interaction.client.get_channel(channel_id)
        if mod_channel is None:
            try:
                mod_channel = await interaction.client.fetch_channel(channel_id)
            except Exception as e:
                await interaction.response.send_message(f"⚠️ Could not fetch mod channel: {e}", ephemeral=True)
                return

        ticket["status"] = "Rejected"
        try:
            msg = await mod_channel.fetch_message(ticket["mod_message_id"])
            new_embed = build_ticket_embed(ticket, assign=f"❌ Rejected Ticket", color=discord.Color.red())
            await msg.edit(embed=new_embed, view=None)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Failed to update the original ticket message: {e}", ephemeral=True)

        tickets.remove(ticket)
        save_open_tickets(tickets)

        await interaction.response.send_message(
            f"❌ Rejected ticket `{self.ticket_id}`",
            ephemeral=True
        )

    @ui.button(label="Comment", style=discord.ButtonStyle.secondary, custom_id="comment_ticket")
    async def comment(self, interaction: Interaction, button: ui.Button):
        tickets = load_open_tickets()
        ticket = next((t for t in tickets if t["id"] == self.ticket_id), None)

        if not ticket:
            await interaction.response.send_message("❌ Ticket not found.", ephemeral=True)
            return

        async def after_comment_submit(interaction: Interaction, updated_ticket, new_comment: str):
            try:
                # Update mod message
                mod_channel = interaction.guild.get_channel(updated_ticket["mod_channel_id"])
                mod_message = await mod_channel.fetch_message(updated_ticket["mod_message_id"])
                embed = build_ticket_embed(updated_ticket, assign=False)
                await mod_message.edit(embed=embed)

                # Post to thread if exists
                thread_id = updated_ticket.get("thread_id")
                if thread_id:
                    try:
                        thread = await interaction.guild.fetch_channel(thread_id)
                        await thread.send(f"💬 **New Comment from {interaction.user.mention}:**\n{new_comment}")
                    except:
                        pass
                await interaction.response.send_message("✅ Comment added to the ticket.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(
                    f"⚠️ Failed to update the ticket: {e}", ephemeral=True
                )

        await interaction.response.send_modal(CommentModal(ticket, after_comment_submit))


# ------------------- Assigned Ticket View -------------------

class AssignedTicketActions(ui.View):
    def __init__(self, ticket_id):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id

    @ui.button(label="Assign (Copy Command)", style=discord.ButtonStyle.primary, custom_id="assign_ticket")
    async def assign(self, interaction: Interaction, button: ui.Button):
        command_example = f"/assign ticket_id:{self.ticket_id} assignees:   "
        await interaction.response.send_message(
            f"📋 Copy and paste this command below, using autocomplete to tag people/roles:\n```{command_example}```",
            ephemeral=True
        )

    @ui.button(label="✅ Mark as Solved", style=discord.ButtonStyle.success, custom_id="solve_ticket")
    async def solve(self, interaction: Interaction, button: ui.Button):
        tickets = load_open_tickets()
        ticket = next((t for t in tickets if t["id"] == self.ticket_id), None)

        if not ticket:
            await interaction.response.send_message("❌ Ticket not found.", ephemeral=True)
            return

        ticket["status"] = "Solved"

        try:
            mod_channel = interaction.guild.get_channel(ticket["mod_channel_id"])
            mod_message = await mod_channel.fetch_message(ticket["mod_message_id"])
            embed = build_ticket_embed(ticket, assign="✅ Solved Ticket", color=discord.Color.green())
            await mod_message.edit(embed=embed, view=None)

            if thread_id := ticket.get("thread_id"):
                thread = await interaction.guild.fetch_channel(thread_id)
                await thread.send("✅ Ticket marked as **solved**. This thread will now be archived.")
                await thread.edit(archived=True, locked=True)

            tickets.remove(ticket)
            save_open_tickets(tickets)

            await interaction.response.send_message("✅ Ticket marked as solved and closed.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error updating ticket: {e}", ephemeral=True)

    @ui.button(label="❌ Close (Unsolved)", style=discord.ButtonStyle.danger, custom_id="close_unsolved_ticket")
    async def close_unsolved(self, interaction: Interaction, button: ui.Button):
        tickets = load_open_tickets()
        ticket = next((t for t in tickets if t["id"] == self.ticket_id), None)

        if not ticket:
            await interaction.response.send_message("❌ Ticket not found.", ephemeral=True)
            return

        ticket["status"] = "Closed"

        try:
            mod_channel = interaction.guild.get_channel(ticket["mod_channel_id"])
            mod_message = await mod_channel.fetch_message(ticket["mod_message_id"])
            embed = build_ticket_embed(ticket, assign="🔒 Closed Ticket", color=discord.Color.dark_gray())
            await mod_message.edit(embed=embed, view=None)

            if thread_id := ticket.get("thread_id"):
                thread = await interaction.guild.fetch_channel(thread_id)
                await thread.send("🔒 Ticket closed without resolution. This thread will now be archived.")
                await thread.edit(archived=True, locked=True)

            tickets.remove(ticket)
            save_open_tickets(tickets)

            await interaction.response.send_message("🔒 Ticket closed (unsolved).", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error closing ticket: {e}", ephemeral=True)


# ------------------- Ticket Form -------------------
class TicketModal(ui.Modal, title="Submit a Ticket"):
    title_input = ui.TextInput(label="Ticket Title", placeholder="Short title", max_length=100)
    description = ui.TextInput(label="Description", placeholder="Describe the issue/request",
                               style=discord.TextStyle.paragraph)
    priority = ui.TextInput(label="Priority (1–10)", placeholder="e.g. 5")
    category = ui.TextInput(label="Category (Bug/Feature/Support/Other)", placeholder="e.g. Bug")

    def __init__(self, interaction: Interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: Interaction):
        try:
            prio = int(self.priority.value)
            if not 1 <= prio <= 10:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Priority must be an integer between 1 and 10.", ephemeral=True)
            return

        ticket = {
            "id": generate_ticket_id(),
            "title": self.title_input.value,
            "description": self.description.value,
            "created_at": datetime.now(tz=tz).isoformat(),
            "created_by": interaction.user.id,
            "status": "Open",
            "priority": prio,
            "category": self.category.value.capitalize(),
            "assigned_to": None,
            "assigned_role": None,
            "thread_id": None,
            "updates": [],
            "mod_message_id": None,
            "mod_channel_id": None
        }

        mod_channel = discord.utils.get(interaction.guild.text_channels, name="mod-tickets")
        if not mod_channel:
            await interaction.response.send_message("❌ Cannot find moderation ticket channel.", ephemeral=True)
            return

        embed = build_ticket_embed(ticket)
        view = TicketActions(ticket["id"])
        mod_msg = await mod_channel.send(embed=embed, view=view)
        ticket["mod_message_id"] = mod_msg.id
        ticket["mod_channel_id"] = mod_channel.id

        tickets = load_open_tickets()
        tickets.append(ticket)
        save_open_tickets(tickets)

        await interaction.response.send_message(f"✅ Ticket created! Your ticket ID is `{ticket['id']}`.",
                                                ephemeral=True)


async def add_ticket_mods_to_thread(thread: discord.Thread, guild: discord.Guild):
    ticket_mod_role = discord.utils.get(guild.roles, name="TicketMod")
    if not ticket_mod_role:
        return
    for mod in ticket_mod_role.members:
        try:
            await thread.add_user(mod)
        except discord.Forbidden:
            pass  # Bot lacks permission


# ------------------- Ticket Cog -------------------
class Ticket(Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticketchannel", description="Set the channel where ticket threads will be created.")
    @app_commands.describe(channel="The text channel for ticket threads")
    async def ticket_channel(self, interaction: Interaction, channel: discord.TextChannel):
        # Check if user has the TicketMod role
        if not await user_has_role(interaction, "TicketMod"):
            await interaction.response.send_message(
                "❌ You need the **TicketMod** role to use this command.", ephemeral=True
            )
            return

        # Check bot permissions in the channel
        bot_perms = channel.permissions_for(interaction.guild.me)
        if not (bot_perms.view_channel and bot_perms.send_messages and bot_perms.create_public_threads):
            await interaction.response.send_message(
                f"❌ I don't have the correct permissions in {channel.mention} (need View, Send, and Thread creation).",
                ephemeral=True
            )
            return

        try:
            # Store the ID in config (assuming global `cfg` dict and `save_config_changes()` exist)
            if "tickets_channel_id" not in cfg:
                cfg["tickets_channel_id"] = None
            cfg["tickets_channel_id"] = channel.id
            save_config_changes(cfg)

            await interaction.response.send_message(
                f"📨 Ticket threads will now be created in {channel.mention}.", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Failed to set ticket channel: `{str(e)}`", ephemeral=True
            )

    @app_commands.command(name="ticket", description="Submit a ticket to the moderators.")
    async def ticket(self, interaction: Interaction):
        if not validate_ticket_creation():
            await interaction.response.send_message("❌ Too many open tickets. Please wait for tickets to be solved.",
                                                    ephemeral=True)
            return
        await interaction.response.send_modal(TicketModal(interaction))

    @app_commands.command(name="assign", description="Assign users or roles to a ticket and create a thread.")
    @app_commands.describe(ticket_id="Ticket ID", assignees="Mention users or roles (e.g. @User @Role)")
    async def assign(self, interaction: Interaction, ticket_id: str, assignees: str):
        await interaction.response.defer(ephemeral=True)
        if not await user_has_role(interaction, "TicketMod"):
            await interaction.followup.send(
                "❌ You need the **TicketMod** role to use this command.", ephemeral=True
            )
            return

        tickets = load_open_tickets()
        ticket = next((t for t in tickets if t["id"] == ticket_id), None)

        def assignees_parser():
            ids = []
            for word in assignees.split():
                if word.startswith("<@") or word.startswith("<@&"):
                    try:
                        ids.append(int(word.strip("<@!&>")))
                    except ValueError:
                        continue

            members = [interaction.guild.get_member(i) for i in ids if interaction.guild.get_member(i)]
            roles = [interaction.guild.get_role(i) for i in ids if interaction.guild.get_role(i)]
            return members, roles

        members, roles = assignees_parser()

        if not ticket:
            await interaction.followup.send("❌ Ticket not found.", ephemeral=True)
            return

        if ticket.get("thread_id"):
            thread = await interaction.guild.fetch_channel(ticket["thread_id"])
            fetched_members = await thread.fetch_members()
            already_in_thread = [
                interaction.guild.get_member(m.id)
                for m in fetched_members
                if interaction.guild.get_member(m.id)
            ]

            # ADD MEMBERS AND ROLES IF THEY ARE NOT IN THE THREAD ALREADY AND THE THREAD EXISTS
            await add_ticket_mods_to_thread(thread=thread, guild=interaction.guild)
            added = []
            for member in members:
                if member not in already_in_thread:
                    try:
                        await thread.add_user(member)
                        added.append(member)
                    except discord.Forbidden:
                        continue

            for role in roles:
                for member in role.members:
                    if member not in already_in_thread and member not in added:
                        try:
                            await thread.add_user(member)
                            added.append(member)
                        except discord.Forbidden:
                            continue

            # ✅ UPDATE TICKET DATA AND EMBED EVEN IF THREAD ALREADY EXISTS
            if members or roles:
                ticket["assigned_to"] = list(set(ticket.get("assigned_to", []) + [m.id for m in members]))
                ticket["assigned_role"] = list(set(ticket.get("assigned_role", []) + [r.id for r in roles]))
                ticket["status"] = "Assigned/In Progress"
                save_open_tickets(tickets)

                mod_channel_id = ticket.get("mod_channel_id")
                if mod_channel_id:
                    mod_channel = interaction.guild.get_channel(mod_channel_id)
                    if mod_channel:
                        try:
                            msg = await mod_channel.fetch_message(ticket["mod_message_id"])
                            new_embed = build_ticket_embed(ticket, assign=True,
                                                           color=discord.Color.from_rgb(52, 152, 219))
                            await msg.edit(embed=new_embed, view=AssignedTicketActions(ticket["id"]))
                        except Exception as e:
                            await interaction.followup.send(
                                f"⚠️ Failed to update the original ticket message: {e}", ephemeral=True
                            )

            if added:
                mention_str = " ".join(user.mention for user in added)
                await thread.send(f"🔧 Newly assigned to: {mention_str}")
                await interaction.followup.send(
                    f"✅ Added {len(added)} new assignees to thread `{thread.name}`.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "ℹ️ No new members or roles were added to the thread (they may already be present).",
                    ephemeral=True
                )
            return

        # If no thread yet
        if not members and not roles:
            await interaction.followup.send("❌ No valid users or roles found in your mentions.", ephemeral=True)
            return

        ticket["assigned_to"] = list(set((ticket.get("assigned_to") or []) + [m.id for m in members]))
        ticket["assigned_role"] = list(set((ticket.get("assigned_role") or []) + [r.id for r in roles]))

        channel_id = cfg.get("tickets_channel_id")
        if not channel_id:
            await interaction.followup.send("❌ Cannot find the ticket assigning/threads channel.",
                                            ephemeral=True)
            return

        parent_channel = interaction.guild.get_channel(channel_id)
        if not parent_channel:
            await interaction.followup.send("❌ Ticket channel not found or deleted.", ephemeral=True)
            return

        # Create a private thread
        thread = await parent_channel.create_thread(
            name=f"Ticket: {ticket['title']}",
            type=discord.ChannelType.private_thread,
            invitable=False  # only mods can invite
        )

        await add_ticket_mods_to_thread(thread=thread, guild=interaction.guild)

        # Add members and roles to the thread
        for member in members:
            try:
                await thread.add_user(member)
            except discord.Forbidden:
                pass

        for role in roles:
            for member in role.members:
                try:
                    await thread.add_user(member)
                except discord.Forbidden:
                    pass

        ticket["thread_id"] = thread.id
        ticket["status"] = "Assigned/In Progress"
        save_open_tickets(tickets)

        # 2. Edit the original ticket message in the mod-tickets channel
        mod_channel_id = ticket.get("mod_channel_id")
        if not mod_channel_id:
            await interaction.followup.send(
                "⚠️ Ticket is missing `mod_channel_id`. Cannot update the original message.", ephemeral=True)
            return

        mod_channel = interaction.guild.get_channel(mod_channel_id)
        if not mod_channel:
            await interaction.followup.send("⚠️ Failed to locate the mod tickets channel.", ephemeral=True)
            return

        try:
            msg = await mod_channel.fetch_message(ticket["mod_message_id"])
            new_embed = build_ticket_embed(ticket, assign=True, color=discord.Color.from_rgb(52, 152, 219))
            await msg.edit(embed=new_embed, view=AssignedTicketActions(ticket["id"]))
        except Exception as e:
            await interaction.followup.send(f"⚠️ Failed to update the original ticket message: {e}", ephemeral=True)

        embed = build_ticket_embed(ticket, assign=True)
        mention_str = " ".join(obj.mention for obj in members + roles)
        await thread.send(content=f"🔧 Assigned to: {mention_str}", embed=embed)

        await interaction.followup.send(f"✅ Ticket `{ticket_id}` assigned and private thread created.",
                                        ephemeral=True)


async def setup(bot):
    await bot.add_cog(Ticket(bot)) 
