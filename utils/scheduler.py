import asyncio
import os
from datetime import datetime

import discord
from discord.ext import tasks, commands
from discord.ui import View, Button, Modal, TextInput

from cogs.notifying import build_schedule_embed
from utils.config_utils import *
from utils.utils import get_timezone_from_string, get_time_until_next_standup

align_running = False

cfg = load_config()
bot = None

ANSWERS_FILE = "../storage/standup_answers.json"


def save_standup_answer(user_id: int, answers: dict, questions_snapshot: dict, tz):
    # Load existing answers
    user_id = str(user_id)

    if os.path.exists(ANSWERS_FILE):
        # If file is empty or corrupt, catch and default to empty dict
        try:
            with open(ANSWERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}
    else:
        data = {}

    today = datetime.now(tz=tz).strftime("%Y-%m-%d")

    if today not in data:
        data[today] = {}

    # Store both answers and the questions snapshot
    data[today][user_id] = {
        "answers": answers,
        "questions_snapshot": questions_snapshot,
    }

    if len(data) > 14:
        oldest_day = sorted(data.keys())[0]  # Ensures lexicographic order
        data.pop(oldest_day)

    # Save back
    with open(ANSWERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def set_bot(bot_instance):
    global bot
    bot = bot_instance


async def send_standup_announcement(bot: commands.Bot):
    channel = bot.get_channel(cfg["standup_channel_id"])
    if not channel:
        print("❌ Could not find the standup channel.")
        return

    guild = channel.guild  # get guild here
    role = guild.get_role(cfg["standup_role_id"])
    role_mention = role.mention if role else ""

    embed, _ = build_schedule_embed(guild=guild, updated=False)
    await channel.send(content=role_mention, embed=embed)


class StandupAnswerModal(Modal, title="Standup Answers"):
    def __init__(self, questions, view=None):
        super().__init__()
        self.view = view
        # Build questions as (id, label) pairs from passed questions list (limit 3)
        self.questions = [(f"q{i}", q) for i, q in enumerate(questions[:3])]

        for qid, qlabel in self.questions:
            self.add_item(TextInput(label=qlabel, custom_id=qid, style=discord.TextStyle.paragraph, required=False))

    async def on_submit(self, interaction: discord.Interaction):
        answers = {}
        questions_snapshot = {}

        for child in self.children:
            qid = child.custom_id
            answers[qid] = child.value
            # get label from self.questions
            label = next(label for (id_, label) in self.questions if id_ == qid)
            questions_snapshot[qid] = label

        save_standup_answer(interaction.user.id, answers, questions_snapshot,
                            tz=get_timezone_from_string(cfg["timezone"]))

        if self.view:
            for item in self.view.children:
                if isinstance(item, Button):
                    item.disabled = True
            if self.view.message:
                await self.view.message.edit(view=self.view)
            else:
                print("No message to edit!")

        await interaction.response.send_message("✅ Thanks for your standup!", ephemeral=True)


class StandupAnswerView(View):
    @discord.ui.button(label="📝 Answer Standup", style=discord.ButtonStyle.primary)
    async def answer_standup(self, interaction: discord.Interaction, button: Button):  # USE THIS TO OPEN THE MODAL FOR
        await interaction.response.send_modal(
            StandupAnswerModal(questions=cfg["standup_questions"], view=self))  # ANSWERING THE QUESTIONS


def build_standup_embed():
    embed = discord.Embed(
        title=(f"📃 {cfg['standup_title']}" if cfg['standup_title'] else "**-no title set-**"),
        description=(cfg['standup_desc'] if cfg['standup_desc'] else "**-no description set-**"),
        colour=discord.Color.blurple()
    )

    if len(cfg["standup_questions"]) <= 0:
        embed.add_field(name=f"**No questions added!**", value="", inline=False)
    else:
        for i, q in enumerate(cfg['standup_questions'][:3], 1):
            embed.add_field(name=f"Q{i}", value=q, inline=False)

    return embed


last_announcement_date = None


@tasks.loop(minutes=1.0)
async def schedule_standup():
    global last_announcement_date

    if not cfg.get("toggled"):
        return

    tz = get_timezone_from_string(cfg["timezone"])
    standup_hour = cfg["standup_time"][0]
    standup_minute = cfg["standup_time"][1]
    now = datetime.now(tz)
    print(f" ➤ Check executed {now.hour}:{now.minute}")

    time_until = get_time_until_next_standup(cfg)

    if time_until is None:
        print("Standup config incomplete.")
        return

    minutes_until = time_until.total_seconds() / 60

    # Send announcement 20 minutes before, only once per day
    if 19 <= minutes_until <= 20:
        if last_announcement_date != now.date():
            await send_standup_announcement(bot)
            last_announcement_date = now.date()

    # Send standup DMs at standup time (0-1 minute window)
    if now.hour == standup_hour and now.minute == standup_minute:
        channel = bot.get_channel(cfg["standup_channel_id"])
        guild = channel.guild
        role = guild.get_role(cfg["standup_role_id"])

        # fe 2025-07-31 - - 2025-08-07 on this day remove in FIFO order - aka remove 07-31 add 08-07
        # 01,  02,  03,  04,  05,  06,  07,  08,  09,  10,  11,  12
        # 31,  28,  31,  30,  31,  30,  31,  31,  30,  31,  30,  31

        for member in role.members:
            try:
                view = StandupAnswerView()
                message = await member.send(embed=build_standup_embed(), view=view)
                view.message = message
            except discord.Forbidden:
                print(f"❌ - Could not DM {member.name}")

        # Reset announcement flag for next cycle
        last_announcement_date = None


async def align_and_start_standup():
    global align_running
    if align_running:
        print("⚠️ Align already running. Skipping...")
        return

    if not cfg.get("toggled", False):
        print("⛔ Standup is toggled off. Not aligning.")
        return

    align_running = True
    try:
        if schedule_standup.is_running():
            schedule_standup.cancel()

        tz = get_timezone_from_string(cfg["timezone"])
        now = datetime.now(tz)
        seconds = now.second
        delay = 60 - seconds if seconds > 0 else 0

        print(f"⌛ Aligning to next minute in {delay} seconds...")
        await asyncio.sleep(delay)
        await schedule_standup.start()
    finally:
        align_running = False
