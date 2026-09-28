"""Rules gate + onboarding for drift-setup."""
from __future__ import annotations

import discord

from helpers import find_member_role, find_text_by_base

RULES_AGREE_CUSTOM_ID = "drift_setup:rules_agree"


class RulesAgreeView(discord.ui.View):
    """Persistent rules gate — custom_id survives bot restarts."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="I agree",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id=RULES_AGREE_CUSTOM_ID,
    )
    async def agree(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return
        role = find_member_role(interaction.guild)
        if not role:
            await interaction.response.send_message(
                "Member/Viewer role missing — re-run `/setup`.", ephemeral=True
            )
            return
        if role in interaction.user.roles:
            await interaction.response.send_message("You're already verified ✅", ephemeral=True)
            return
        try:
            await interaction.user.add_roles(role, reason="Accepted server rules")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I can't assign that role — move my role **above** Member/Viewer "
                "and ensure I have **Manage Roles**.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Couldn't assign role: {e}", ephemeral=True)
            return
        await interaction.response.send_message(
            f"Welcome — you now have **{role.name}**. Enjoy the server!", ephemeral=True
        )


async def lock_gated_categories(
    guild: discord.Guild,
    public_categories: tuple[str, ...],
    member_role: discord.Role,
    reason: str,
    created: list[str],
) -> None:
    everyone = guild.default_role
    public = {c.upper() for c in public_categories}
    for cat in guild.categories:
        if cat.name.upper() in public:
            continue
        try:
            await cat.set_permissions(everyone, view_channel=False, reason=reason)
            await cat.set_permissions(member_role, view_channel=True, reason=reason)
        except discord.HTTPException:
            continue
    created.append(f"gate:{member_role.name}")


async def post_onboarding(
    guild: discord.Guild, member_role_name: str, reason: str, created: list[str]
) -> None:
    welcome = find_text_by_base(guild, "welcome", "intro")
    rules = find_text_by_base(guild, "rules")

    if welcome:
        try:
            await welcome.edit(
                topic="Start here — then accept the rules to unlock the server.",
                reason=reason,
            )
        except discord.HTTPException:
            pass
        already = False
        async for msg in welcome.history(limit=15):
            if msg.author == guild.me and msg.embeds and msg.embeds[0].title == "Welcome!":
                already = True
                break
        if not already:
            embed = discord.Embed(
                title="Welcome!",
                description=(
                    "Glad you're here.\n\n"
                    f"1. Read **#{rules.name if rules else '📜-rules'}**\n"
                    "2. Tap **I agree** to unlock chat, voice, and the rest\n"
                    "3. Say hi once you're in\n\n"
                    "Links & socials unlock after you verify."
                ),
                color=discord.Color.blurple(),
            )
            try:
                await welcome.send(embed=embed)
                created.append(f"embed:#{welcome.name}")
            except discord.HTTPException:
                pass

    if rules:
        try:
            await rules.edit(
                topic="Accept the rules to get Member/Viewer access.",
                reason=reason,
            )
        except discord.HTTPException:
            pass
        already = False
        async for msg in rules.history(limit=15):
            if msg.author == guild.me and msg.components:
                already = True
                break
        if not already:
            embed = discord.Embed(
                title="Server Rules",
                description=(
                    "1. Be respectful — no hate, harassment, or toxicity.\n"
                    "2. Keep it clean — no NSFW or illegal content.\n"
                    "3. No spam, scams, or random self-promo.\n"
                    "4. Follow Discord's Terms of Service.\n\n"
                    f"Tap **I agree** below to receive **{member_role_name}** "
                    "and unlock the server."
                ),
                color=discord.Color.green(),
            )
            try:
                await rules.send(embed=embed, view=RulesAgreeView())
                created.append(f"rules-gate:#{rules.name}")
            except discord.HTTPException:
                pass
