from discord import app_commands, Embed, Color, Interaction
from discord.ext import commands

from utils.utils import user_has_role


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows all StandUP commands available to you.")
    async def help(self, interaction: Interaction):
        is_standup_mod = await user_has_role(interaction, "StandupMod")
        is_ticket_mod = await user_has_role(interaction, "TicketMod")

        embed = Embed(
            title="🛠️ StandUP Help",
            description="Here’s a list of commands available to you:",
            color=Color.green()
        )

        # StandupMod commands
        if is_standup_mod:
            embed.add_field(
                name="🌟 Standup Commands",
                value=(
                    "`/preview` – Shows a preview of the standup card\n"
                    "`/toggle` – Enables or disables the standup\n"
                    "`/config` – Displays current standup configuration\n"
                    "`/summary` – View recorded standup responses (by date or last N entries)"
                ),
                inline=False
            )

            embed.add_field(
                name="🕒 Schedule Setup",
                value=(
                    "`/time` – Set the daily standup time\n"
                    "`/timezone` – Set your timezone (e.g., UTC+2, UTC-5:30)\n"
                    "`/days` – Choose which days the standup runs"
                ),
                inline=False
            )

            embed.add_field(
                name="📢 Role & Channel Setup",
                value=(
                    "`/role` – Set the role that receives standup notifications\n"
                    "`/channel` – Set the channel where standup is posted"
                ),
                inline=False
            )

            embed.add_field(
                name="📅 Announcements",
                value=(
                    "`/announce` – Announce the next standup manually"
                ),
                inline=False
            )

            embed.add_field(
                name="📝 Content Configuration",
                value=(
                    "Use the `✏️ Edit Content` button in `/preview` to:\n"
                    "- Set title, description, and questions for the standup"
                ),
                inline=False
            )

        # TicketMod commands
        if is_ticket_mod:
            embed.add_field(
                name="🎟️ Ticket Management",
                value=(
                    "`/assign` – Assign a ticket to members or roles\n"
                    "`/ticketchannel` – Set the channel where ticket threads will be created"
                ),
                inline=False
            )

        # Commands accessible to all users
        embed.add_field(
            name="🙋 General Commands",
            value=(
                "`/ticket` – Submit a ticket to the moderators\n"
                "`/help` – Show this help message"
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Help(bot))
