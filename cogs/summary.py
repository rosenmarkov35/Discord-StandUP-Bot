import json
from datetime import datetime

import discord
from discord import Embed, app_commands
from discord.ext import commands
from discord.ui import View, Button

from utils.utils import user_has_role


class StandupPaginator(View):
    def __init__(self, bot: commands.Bot, data: dict, dates: list):
        super().__init__(timeout=180)
        self.bot = bot
        self.data = data
        self.dates = dates
        self.day_index = 0
        self.page_index = 0
        self.entries_per_page = 3

        self.update_button_states()

    def update_button_states(self):
        current_date = self.dates[self.day_index]
        total_entries = len(self.data.get(current_date, {}))
        total_pages = max(1, -(-total_entries // self.entries_per_page))  # Ceiling division

        # Day navigation
        self.previous_day_button.disabled = self.day_index == 0
        self.next_day_button.disabled = self.day_index >= len(self.dates) - 1

        # Entry pagination
        self.previous_page_button.disabled = self.page_index == 0
        self.next_page_button.disabled = self.page_index >= total_pages - 1

    async def get_embed(self):
        date = self.dates[self.day_index]
        date_data = self.data.get(date, {})
        embed = Embed(title=f"📅 Standup for {date}", color=discord.Color.blurple())

        if not date_data:
            embed.description = "No answers recorded for this date."
        else:
            user_ids = list(date_data.keys())
            start = self.page_index * self.entries_per_page
            end = start + self.entries_per_page
            paged_users = user_ids[start:end]

            for user_id in paged_users:
                user_data = date_data[user_id]
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    user_name = f"@{user.name}"
                except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                    user_name = f"User {user_id}"
                answers = user_data.get("answers", {})
                questions = user_data.get("questions_snapshot", {})

                answer_lines = []
                for key in answers:
                    question = questions.get(key, "Unknown Question")
                    answer = answers.get(key, "No answer.")
                    answer_lines.append(f"**{question}**\n{answer or '*No answer*'}")

                field_value = "\n\n".join(answer_lines) or "*No answers*"
                embed.add_field(name=f"🗨 {user_name}", value=field_value, inline=False)

        embed.set_footer(
            text=f"Date {self.day_index + 1}/{len(self.dates)} • Page {self.page_index + 1}"
        )
        return embed

    @discord.ui.button(label="⬅ Day", style=discord.ButtonStyle.secondary)
    async def previous_day_button(self, interaction: discord.Interaction, button: Button):
        self.day_index -= 1
        self.page_index = 0
        self.update_button_states()
        await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    @discord.ui.button(label="➡ Day", style=discord.ButtonStyle.secondary)
    async def next_day_button(self, interaction: discord.Interaction, button: Button):
        self.day_index += 1
        self.page_index = 0
        self.update_button_states()
        await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    @discord.ui.button(label="⬅ Page", style=discord.ButtonStyle.primary)
    async def previous_page_button(self, interaction: discord.Interaction, button: Button):
        self.page_index -= 1
        self.update_button_states()
        await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    @discord.ui.button(label="➡ Page", style=discord.ButtonStyle.primary)
    async def next_page_button(self, interaction: discord.Interaction, button: Button):
        self.page_index += 1
        self.update_button_states()
        await interaction.response.edit_message(embed=await self.get_embed(), view=self)


class Summary(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="summary", description="Show standup summaries for a date or last N days")
    @app_commands.describe(input="Enter a date (dd-mm-yyyy) or number of days (e.g. 3)")
    async def summary(self, interaction: discord.Interaction, input: str = None):
        if not await user_has_role(interaction, "StandupMod"):
            await interaction.response.send_message(
                "❌ You need the **StandupMod** role to use this command.", ephemeral=True
            )
            return

        try:
            with open("standup_answers.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            await interaction.response.send_message("No standup answers found.", ephemeral=True)
            return

        all_dates = sorted(data.keys())

        # Determine which dates to show
        selected_dates = []

        if input:
            try:
                # Try to parse as specific date
                input_date = datetime.strptime(input, "%Y-%m-%d").strftime("%Y-%m-%d")
                if input_date in data:
                    selected_dates = [input_date]
            except ValueError:
                try:
                    # Try to parse as number of entries
                    num_entries = min(int(input), 14)
                    selected_dates = all_dates[-num_entries:]
                except ValueError:
                    await interaction.response.send_message(
                        "⚠ Please provide a valid date (dd-mm-yyyy) or a number (1–14).",
                        ephemeral=True,
                    )
                    return
        else:
            selected_dates = all_dates[-1:]  # default: last available date

        if not selected_dates:
            await interaction.response.send_message("No matching standup entries found.", ephemeral=True)
            return

        filtered_data = {date: data[date] for date in selected_dates}
        view = StandupPaginator(self.bot, filtered_data, selected_dates)
        await interaction.response.send_message(embed=await view.get_embed(), view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Summary(bot))
