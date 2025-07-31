import re
from datetime import datetime, timedelta

import discord
from discord import app_commands, Interaction, Embed, Color
from discord.ext import commands

from config_utils import *
from scheduler import align_and_start_standup, schedule_standup
from utils import user_has_role

cfg = load_config()
VALID_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


async def validate_and_handle_toggle(interaction: Interaction, cfg: dict, was_valid_before: bool):
    # Validate config after the change
    is_valid, missing = validate_standup_config(cfg)

    # If config just became invalid (was valid before, now invalid)
    if not is_valid and was_valid_before:
        # Disable standups if they were enabled
        if cfg.get('toggled'):
            cfg['toggled'] = False
            save_config_changes(cfg)
            if schedule_standup.is_running():
                schedule_standup.cancel()

        missing_list = "\n - " + "\n - ".join(missing)
        await interaction.response.send_message(
            f"⚠️ Standup config is now invalid after this change and standups have been disabled.\n"
            f"Missing config:\n{missing_list}",
            ephemeral=True
        )
        return

    # If still invalid but was invalid before, don't spam message
    if not is_valid and not was_valid_before:
        # optionally do nothing or silently fail
        return


class StandupConfig(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="time",
                          description="Sets the time (24H format) when"
                                      " the standup check-in occurs. (e.g., /time 09:30 for 9:30 AM)")
    async def time(self, interaction: Interaction, time_str: str):
        if not await user_has_role(interaction, "StandupMod"):
            await interaction.response.send_message(
                "❌ You need the **StandupMod** role to use this command.", ephemeral=True
            )
            return

        try:
            parsed_time = datetime.strptime(time_str, "%H:%M").time()
            was_valid_before, _ = validate_standup_config(cfg)
            cfg["standup_time"] = [parsed_time.hour, parsed_time.minute, parsed_time.strftime("%H:%M")]
            save_config_changes(cfg)

            await validate_and_handle_toggle(interaction, cfg, was_valid_before)

            await interaction.response.send_message(f"✅ Standup time set to **{cfg['standup_time'][2]}**.",
                                                    ephemeral=True)
            await align_and_start_standup()
        except ValueError:
            await interaction.response.send_message("❌ Please use the 24-hour format: 'HH:MM' (e.g. '09:30').",
                                                    ephemeral=True)

    @app_commands.command(name="timezone",
                          description="Sets the UTC timezone for scheduling. "
                                      "(e.g., /timezone UTC+2 or /timezone UTC-5:30)")
    async def timezone(self, interaction: Interaction, utc_offset: str):
        if not await user_has_role(interaction, "StandupMod"):
            await interaction.response.send_message(
                "❌ You need the **StandupMod** role to use this command.", ephemeral=True
            )
            return

        match = re.match(r"^UTC([+-])(\d{1,2})(?::([03]0))?$", utc_offset)
        if not match:
            await interaction.response.send_message("❌ Please use the format like `UTC+3`, `UTC-5:30`, or `UTC+0`.")
            return

        sign, hours_str, minutes_str = match.groups()
        hours = int(hours_str)
        minutes = int(minutes_str) if minutes_str else 0
        total_offset = hours + minutes / 60
        if sign == "-":
            total_offset = -total_offset

        if total_offset < -12 or total_offset > 14:
            await interaction.response.send_message(
                "❌ Offset out of valid range. UTC offset must be between -12:00 and +14:00.")
            return

        total_minutes = hours * 60 + minutes
        if sign == "-":
            total_minutes = -total_minutes

        offset = timedelta(minutes=total_minutes)
        was_valid_before, _ = validate_standup_config(cfg)

        cfg["timezone"] = utc_offset
        save_config_changes(cfg)

        await validate_and_handle_toggle(interaction, cfg, was_valid_before)

        await interaction.response.send_message(f"✅ Timezone set to **{utc_offset}**.")
        await align_and_start_standup()

    @app_commands.command(name="days",
                          description="Sets the days  when the standup check-in will be sent out.")
    async def days(self, interaction: Interaction, day_names: str):
        if not await user_has_role(interaction, "StandupMod"):
            await interaction.response.send_message(
                "❌ You need the **StandupMod** role to use this command.", ephemeral=True
            )
            return
        if not day_names:
            await interaction.response.send_message(
                "❌ You must specify at least one day. Example: `/setstandupdays monday friday`",
                ephemeral=True)
            return

        lowercase_days = [day.lower() for day in day_names.split()]
        invalid_days = [day for day in lowercase_days if day not in VALID_DAYS]

        if invalid_days:
            await interaction.response.send_message(
                f"❌ Invalid day(s): {', '.join(invalid_days)}.\n"
                f"Please use full weekday names like: `monday`, `tuesday`, etc.",
                ephemeral=True)
            return
        was_valid_before, _ = validate_standup_config(cfg)
        cfg["standup_days"] = lowercase_days
        save_config_changes(cfg)

        await validate_and_handle_toggle(interaction, cfg, was_valid_before)

        await interaction.response.send_message(f"✅ Standup days set to: {', '.join(lowercase_days).title()}.",
                                                ephemeral=True)

    @app_commands.command(
        name="config",
        description="Displays all current settings and configurations for your standup."
    )
    async def config(self, interaction: Interaction):
        if not await user_has_role(interaction, "StandupMod"):
            await interaction.response.send_message(
                "❌ You need the **StandupMod** role to use this command.", ephemeral=True
            )
            return
        is_valid, missing = validate_standup_config(cfg)
        toggled = cfg.get("toggled", False)

        def format_value(value, fallback="❌ Not set"):
            return value if value else fallback

        embed = discord.Embed(
            title="⚙️ Standup Configuration",
            description="Here's the current setup for standup check-ins:",
            color=discord.Color.green() if is_valid else discord.Color.red()
        )

        time = cfg.get("standup_time")
        embed.add_field(
            name="🕒 Standup Time",
            value=format_value(time[2] if time else None),
            inline=True
        )

        embed.add_field(
            name="🌍 Timezone",
            value=format_value(cfg.get("timezone")),
            inline=True
        )

        days = ", ".join(cfg.get("standup_days", [])).title()
        embed.add_field(
            name="📆 Days",
            value=format_value(days),
            inline=True
        )

        channel = interaction.guild.get_channel(cfg.get("standup_channel_id"))
        embed.add_field(
            name="📢 Announcement Channel",
            value=format_value(channel.mention if channel else None),
            inline=True
        )

        role = interaction.guild.get_role(cfg.get("standup_role_id"))
        embed.add_field(
            name="🏅 Standup Role",
            value=format_value(role.mention if role else None),
            inline=True
        )

        embed.add_field(
            name="🔁 Standup Toggled",
            value="✅ Enabled" if toggled else "❌ Disabled",
            inline=True
        )

        # Missing fields warning (if any)
        if not is_valid:
            embed.add_field(
                name="⚠️ Missing Required Settings",
                value=", ".join(missing),
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="channel",
                          description="Sets the text channel where the standup reminders "
                                      "and schedule changes will be publicly announced.")
    async def channel(self, interaction: Interaction, channel: discord.TextChannel):
        if not await user_has_role(interaction, "StandupMod"):
            await interaction.response.send_message(
                "❌ You need the **StandupMod** role to use this command.", ephemeral=True
            )
            return
        was_valid_before, _ = validate_standup_config(cfg)

        cfg["standup_channel_id"] = channel.id
        save_config_changes(cfg)

        await validate_and_handle_toggle(interaction, cfg, was_valid_before)

        await interaction.response.send_message(
            f"📢 Standup reminders and schedule changes will now be posted in {channel.mention}",
            ephemeral=True)

    @channel.error
    async def channel_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        # You can inspect the error type and respond accordingly
        await interaction.response.send_message(
            "❗Something went wrong. Make sure you mention a valid channel like '#general'.",
            ephemeral=True
        )

    @app_commands.command(name="role",
                          description="Sets which Discord role will be DM'd the daily standup check-ins."
                                      " (e.g., /role @TeamMembers)")
    async def role(self, interaction: Interaction, role_str: discord.Role):
        if not await user_has_role(interaction, "StandupMod"):
            await interaction.response.send_message(
                "❌ You need the **StandupMod** role to use this command.", ephemeral=True
            )
            return
        if role_str.name == "@everyone":
            await interaction.response.send_message(
                "❌ You can't set the role to @everyone.", ephemeral=True
            )
            return
        print(role_str.name)
        was_valid_before, _ = validate_standup_config(cfg)

        cfg["standup_role_id"] = role_str.id
        save_config_changes(cfg)

        await validate_and_handle_toggle(interaction, cfg, was_valid_before)

        await interaction.response.send_message(f"☑️ Standup role set to {role_str.mention}")

    @app_commands.command(name="toggle", description="Activate or deactivate standup check-ins.")
    async def toggle(self, interaction: Interaction):
        if not await user_has_role(interaction, "StandupMod"):
            await interaction.response.send_message(
                "❌ You need the **StandupMod** role to use this command.", ephemeral=True
            )
            return
        is_valid, missing = validate_standup_config(cfg)

        if is_valid:
            cfg['toggled'] = not cfg['toggled']
            save_config_changes(cfg)

            state = "enabled ✅" if cfg['toggled'] else "disabled ❌"
            await interaction.response.send_message(f"Standup {state}", ephemeral=True)

            if cfg['toggled']:
                await align_and_start_standup()

            else:
                if schedule_standup.is_running():
                    schedule_standup.cancel()
                    print("🛑 Standup schedule cancelled.")

                # Send embed to announcement channel to notify standups are off
                channel = self.bot.get_channel(cfg["standup_channel_id"])
                if channel:
                    embed = Embed(
                        title="🛑 Standup Disabled",
                        description="Standup check-ins have been disabled and will not occur until re-enabled.",
                        color=Color.red()
                    )
                    try:
                        await channel.send(embed=embed)
                    except Exception as e:
                        print(f"❌ Failed to send standup disabled message: {e}")

        else:
            missing_list = "\n - " + "\n - ".join(missing)
            await interaction.response.send_message(
                f"❗ Can't toggle standup check-ins because of missing config/content:{missing_list}\n"
                f"Set the missing parameters to toggle.",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(StandupConfig(bot))
