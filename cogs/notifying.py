from datetime import datetime

import discord
from discord import app_commands, Interaction, Embed
from discord.ext.commands import Cog

from config_utils import load_config
from utils import get_timezone_from_string, get_time_until_next_standup, user_has_role

cfg = load_config()


def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    else:
        return f"{minutes}m {seconds}s"


def build_schedule_embed(guild=None, updated: bool = False):
    missing_values = []

    if cfg["standup_time"]:
        time = cfg["standup_time"]
    else:
        time = None
        missing_values.append("standup time")

    if cfg["timezone"]:
        timezone = cfg["timezone"]
    else:
        timezone = None
        missing_values.append("timezone")

    if cfg["standup_days"]:
        days = ", ".join(day.capitalize() for day in cfg["standup_days"])
    else:
        days = None
        missing_values.append("standup days")

    if cfg["standup_role_id"]:
        role = guild.get_role(cfg["standup_role_id"])
        role_display = role.mention
    else:
        role_display = None
        missing_values.append("standup role")

    remaining = get_time_until_next_standup(cfg)
    formatted_remaining = format_timedelta(remaining) if remaining else "Unknown"

    embed = Embed(
        title="📢 Standup Schedule Updated" if updated else "⏰ Upcoming Standup Reminder",
        color=discord.Color.red() if updated else discord.Color.green(),
        timestamp=(datetime.now(tz=get_timezone_from_string(timezone)) if timezone else None)
    )

    embed.add_field(name="🕒 Time", value=f"{time[2]}", inline=True)
    embed.add_field(name="🌍 Timezone", value=f"{timezone}", inline=True)
    embed.add_field(name="📆 Days", value=f"{days}", inline=True)
    embed.add_field(name="👥 Role", value=f"{role_display}", inline=False)
    embed.add_field(
        name="🔄 Next Standup",
        value=f"In {formatted_remaining}",
        inline=False
    )
    embed.set_footer(
        text="Please make sure you're available at the scheduled time. Standups will be sent via DM."
        if updated else "Please be ready — you'll receive a DM shortly to complete your standup check-in.")

    return embed, missing_values


class Notifying(Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="announce",
        description="Announce the next standup or updated schedule to the channel."
    )
    @app_commands.describe(updated="Mark this announcement as a schedule update.")
    async def announce(self, interaction: Interaction, updated: bool = False):
        if not await user_has_role(interaction, "StandupMod"):
            await interaction.response.send_message(
                "❌ You need the **StandupMod** role to use this command.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        embed, missing_values = build_schedule_embed(guild=guild, updated=updated)

        if missing_values:
            await interaction.response.send_message(
                f"❌ Cannot announce the standup. These required values are missing: {', '.join(missing_values)}",
                ephemeral=True
            )
            return

        channel = guild.get_channel(cfg['standup_channel_id'])
        if channel is None:
            await interaction.response.send_message(
                "❌ The configured standup channel ID is invalid or not accessible.",
                ephemeral=True
            )
            return

        role_mention = guild.get_role(cfg["standup_role_id"]).mention if cfg.get("standup_role_id") else ""
        await channel.send(content=role_mention, embed=embed)
        await interaction.response.send_message(
            f"✅ {'Schedule update' if updated else 'Standup reminder'} sent successfully.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Notifying(bot))
