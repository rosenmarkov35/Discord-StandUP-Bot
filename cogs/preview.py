import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button

from cogs.standupconfig import validate_and_handle_toggle
from utils import user_has_role
from config_utils import *

cfg = load_config()


def build_preview_embed():
    embed = discord.Embed(
        title=(f"📃 {cfg['standup_title']}" if cfg['standup_title'] else "**-no title set-**"),
        description=(cfg['standup_desc'] if cfg['standup_desc'] else "**-no description set-** *not required"),
        colour=discord.Color.blurple()
    )

    if cfg["standup_title"] and cfg["standup_desc"] and len(cfg["standup_questions"]) > 0:
        embed.set_footer(text="This is a standup preview.\n *standup members don't see the ✏️ Edit Content button.*")
    else:
        embed.set_footer(
            text="Use the '✏️ Edit Content' button to set the content of the"
                 " standup.\n *standup members don't see the ✏️ Edit Content button.*")

    if len(cfg["standup_questions"]) <= 0:
        embed.add_field(name=f"**No questions added!**", value="", inline=False)
    else:
        for i, q in enumerate(cfg['standup_questions'][:3], 1):
            embed.add_field(name=f"Q{i}", value=q, inline=False)

    return embed


class EditContentModal(Modal, title="Edit Standup Content"):
    def __init__(self):
        super().__init__()

        self.title_input = TextInput(
            label="Title",
            placeholder="Standup Title",
            required=False,
            default=(cfg['standup_title'] if cfg['standup_title'] else "")
        )
        self.desc_input = TextInput(
            label="Description",
            placeholder="Standup Description",
            required=False,
            default=(cfg['standup_desc'] if cfg['standup_desc'] else "")
        )
        self.questions_input = TextInput(
            label="Questions (one per line)",
            style=discord.TextStyle.paragraph,
            placeholder="What did you do yesterday?\nWhat will you do today?\nAny blockers?",
            required=False,
            default=("\n".join(cfg['standup_questions']) if cfg['standup_questions'] else "")
        )

        self.add_item(self.title_input)
        self.add_item(self.desc_input)
        self.add_item(self.questions_input)

    async def on_submit(self, interaction: discord.Interaction):
        was_valid_before, _ = validate_standup_config(cfg)

        cfg["standup_title"] = self.title_input.value or None
        cfg["standup_desc"] = self.desc_input.value or None
        cfg["standup_questions"] = [q.strip() for q in self.questions_input.value.strip().split("\n") if
                                    q.strip()] or []

        save_config_changes(cfg)

        response_sent = await validate_and_handle_toggle(interaction, cfg, was_valid_before)

        if not response_sent:
            try:
                await interaction.response.send_message("✅ Standup content updated!", ephemeral=True)
            except discord.errors.InteractionResponded:
                # Interaction was already responded to, so do nothing or send a followup
                pass


class PreviewAnswerStandupView(View):
    @discord.ui.button(label="📝 Answer Standup", style=discord.ButtonStyle.primary)
    async def answer_standup(self, interaction: discord.Interaction, button: Button):  # USE THIS TO OPEN THE MODAL FOR
        await interaction.response.send_modal(
            PreviewAnswerModal(questions=cfg["standup_questions"]))  # ANSWERING THE QUESTIONS

    @discord.ui.button(label="✏️ Edit Content", style=discord.ButtonStyle.gray)
    async def edit_content(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            EditContentModal()
        )


class PreviewAnswerModal(Modal, title="Standup Answers"):
    def __init__(self, questions):
        super().__init__()
        for i, q in enumerate(cfg["standup_questions"][:3], 0):
            self.add_item(TextInput(label=q, custom_id=f"q{i}", style=discord.TextStyle.paragraph, required=False))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Thanks for your standup! | preview", ephemeral=True)


class Preview(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="preview", description="Shows a preview of the standup card.")
    async def preview(self, interaction: Interaction):
        if not await user_has_role(interaction, "StandupMod"):
            await interaction.response.send_message(
                "❌ You need the **StandupMod** role to use this command.", ephemeral=True
            )
            return
        is_valid, missing = validate_standup_config(cfg)

        embed = build_preview_embed()

        # Append warning to the footer if the config is incomplete
        if not is_valid:
            missing_fields = ", ".join(missing)
            warning_footer = f"⚠️ Missing required content: {missing_fields}"
            embed.set_footer(
                text=f"{embed.footer.text}\n\n{warning_footer}" if embed.footer else warning_footer
            )

        await interaction.response.send_message(
            embed=embed,
            view=PreviewAnswerStandupView(),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Preview(bot))
