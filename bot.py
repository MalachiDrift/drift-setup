#!/usr/bin/env python3
"""
drift-setup — invite the bot, then scaffold a Discord from templates.

Flow:
  1) Streamer makes you (or their mods) admin
  2) Invite this bot with Manage Channels + Manage Roles (Administrator is easiest)
  3) Run /setup template:streamer  (or /setup template:basic, /build <description>)

Env:
  DISCORD_BOT_TOKEN   required
  OWNER_IDS           optional comma-separated Discord user IDs allowed to /setup anywhere
  GROQ_API_KEY        optional — enables /build invent-from-description
  GROQ_MODEL          optional
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

import discord
from discord import app_commands
from discord.ext import commands

from templates.streamer import STREAMER_ROLES, STREAMER_STRUCTURE, STREAMER_VOICE
from templates.basic import BASIC_ROLES, BASIC_STRUCTURE, BASIC_VOICE


def env(name: str) -> str:
    return (os.environ.get(name, "") or "").strip().strip('"').strip("'")


TOKEN = env("DISCORD_BOT_TOKEN")
GROQ_API_KEY = env("GROQ_API_KEY")
GROQ_MODEL = env("GROQ_MODEL") or "openai/gpt-oss-20b"
OWNER_IDS = {int(x) for x in env("OWNER_IDS").split(",") if x.strip().isdigit()}

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

BUILD_SYSTEM = (
    'Return ONLY valid JSON, no markdown. Schema:\n'
    '{"categories":[{"name":"CATEGORY","text":["channel-a"],"voice":["Voice"]}],'
    '"roles":["RoleA"]}\n'
    "3-6 categories, under 20 text channels, lowercase-dash channel names."
)

PRESETS = {
    "streamer": {
        "label": "Streamer community",
        "structure": STREAMER_STRUCTURE,
        "voice": STREAMER_VOICE,
        "roles": STREAMER_ROLES,
    },
    "basic": {
        "label": "Basic community",
        "structure": BASIC_STRUCTURE,
        "voice": BASIC_VOICE,
        "roles": BASIC_ROLES,
    },
}


def slug(name: str) -> str:
    name = name.strip().lower().replace(" ", "-")
    name = re.sub(r"[^a-z0-9\-_]+", "", name)
    return name[:90] or "channel"


def can_setup(member: discord.Member) -> bool:
    if member.id in OWNER_IDS:
        return True
    perms = member.guild_permissions
    return perms.administrator or (perms.manage_guild and perms.manage_channels and perms.manage_roles)


async def apply_preset(guild: discord.Guild, key: str, reason: str) -> str:
    preset = PRESETS[key]
    created: list[str] = []

    for name, color in preset["roles"]:
        if discord.utils.get(guild.roles, name=name):
            continue
        await guild.create_role(name=name, colour=color, reason=reason)
        created.append(f"role:{name}")

    for cat_name, channels in preset["structure"].items():
        cat = discord.utils.get(guild.categories, name=cat_name)
        if not cat:
            cat = await guild.create_category(cat_name, reason=reason)
            created.append(f"cat:{cat_name}")
        for ch in channels:
            if discord.utils.get(guild.text_channels, name=ch):
                continue
            await guild.create_text_channel(ch, category=cat, reason=reason)
            created.append(f"#{ch}")
        if cat_name.upper() == "VOICE":
            for vn in preset["voice"]:
                if discord.utils.get(guild.voice_channels, name=vn):
                    continue
                await guild.create_voice_channel(vn, category=cat, reason=reason)
                created.append(f"voice:{vn}")

    if not created:
        return f"**{preset['label']}** already looks set up — nothing new created."
    return f"**{preset['label']}** applied. Created: " + ", ".join(created[:50])


async def apply_plan(guild: discord.Guild, plan: dict, reason: str) -> str:
    created: list[str] = []
    for role_name in plan.get("roles") or []:
        role_name = str(role_name).strip()[:100]
        if not role_name or discord.utils.get(guild.roles, name=role_name):
            continue
        await guild.create_role(name=role_name, reason=reason)
        created.append(f"role:{role_name}")

    for cat in plan.get("categories") or []:
        if not isinstance(cat, dict):
            continue
        cat_name = str(cat.get("name") or "Category").strip()[:90]
        if not cat_name:
            continue
        category = discord.utils.get(guild.categories, name=cat_name)
        if not category:
            category = await guild.create_category(cat_name, reason=reason)
            created.append(f"cat:{cat_name}")
        for ch in cat.get("text") or []:
            ch_name = slug(str(ch))
            if discord.utils.get(guild.text_channels, name=ch_name):
                continue
            await guild.create_text_channel(ch_name, category=category, reason=reason)
            created.append(f"#{ch_name}")
        for vn in cat.get("voice") or []:
            vname = str(vn).strip()[:90]
            if not vname or discord.utils.get(guild.voice_channels, name=vname):
                continue
            await guild.create_voice_channel(vname, category=category, reason=reason)
            created.append(f"voice:{vname}")

    if not created:
        return "Nothing new to create (empty plan or everything existed)."
    return "Created: " + ", ".join(created[:50])


def ask_groq(description: str) -> str:
    if not GROQ_API_KEY:
        return ""
    req = urllib.request.Request(
        GROQ_URL,
        data=json.dumps(
            {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": BUILD_SYSTEM},
                    {"role": "user", "content": f"Build a Discord layout for: {description}"},
                ],
                "temperature": 0.7,
            }
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "User-Agent": "drift-setup/1.0 (+https://github.com/MalachiDrift/drift-setup)",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def parse_plan(raw: str) -> dict | None:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "categories" in data:
            return data
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
                if isinstance(data, dict) and "categories" in data:
                    return data
            except json.JSONDecodeError:
                return None
    return None


class DriftSetup(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self.tree.sync()


bot = DriftSetup()


@bot.event
async def on_ready():
    print(f"drift-setup online as {bot.user} ({bot.user.id})")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="/setup streamer")
    )


@bot.tree.command(name="setup", description="Scaffold this server from a template")
@app_commands.describe(template="Which layout to apply")
@app_commands.choices(
    template=[
        app_commands.Choice(name="Streamer (Twitch/community ready)", value="streamer"),
        app_commands.Choice(name="Basic community", value="basic"),
    ]
)
async def setup_cmd(interaction: discord.Interaction, template: app_commands.Choice[str]):
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("Use this in a server.", ephemeral=True)
        return
    if not can_setup(interaction.user):
        await interaction.response.send_message(
            "Need Administrator (or Manage Server + Channels + Roles), or be in OWNER_IDS.",
            ephemeral=True,
        )
        return
    me = interaction.guild.me
    if not me or not (me.guild_permissions.manage_channels and me.guild_permissions.manage_roles):
        await interaction.response.send_message(
            "I need **Manage Channels** and **Manage Roles**. Re-invite with those perms.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(thinking=True)
    result = await apply_preset(
        interaction.guild, template.value, f"drift-setup /setup by {interaction.user}"
    )
    await interaction.followup.send(result)


@bot.tree.command(name="build", description="Invent + create a layout from a short description")
@app_commands.describe(description="e.g. cozy horror streamer community with art channels")
async def build_cmd(interaction: discord.Interaction, description: str):
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("Use this in a server.", ephemeral=True)
        return
    if not can_setup(interaction.user):
        await interaction.response.send_message("Not allowed to build here.", ephemeral=True)
        return
    if not GROQ_API_KEY:
        await interaction.response.send_message(
            "GROQ_API_KEY not set — use `/setup` presets, or add the key to enable `/build`.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(thinking=True)
    try:
        raw = ask_groq(description)
    except Exception as e:
        await interaction.followup.send(f"Brain offline: {e}")
        return
    plan = parse_plan(raw)
    if not plan:
        await interaction.followup.send("Could not parse a layout. Try `/setup streamer` instead.")
        return
    result = await apply_plan(interaction.guild, plan, f"drift-setup /build by {interaction.user}")
    await interaction.followup.send(result)


@bot.tree.command(name="invite", description="How to invite this bot to a streamer's server")
async def invite_cmd(interaction: discord.Interaction):
    client_id = bot.user.id if bot.user else "YOUR_CLIENT_ID"
    # Administrator bit 8 = 0x8; Manage Channels 16; Manage Roles 268435456
    perms = 8  # Administrator
    url = (
        f"https://discord.com/api/oauth2/authorize?client_id={client_id}"
        f"&permissions={perms}&scope=bot%20applications.commands"
    )
    await interaction.response.send_message(
        "**Streamer Discord setup flow**\n"
        "1. They create the server (or use an empty one)\n"
        "2. They make you an admin\n"
        "3. You invite the bot (link below) with Administrator\n"
        "4. Run `/setup` → **Streamer**\n"
        "5. Optional: `/build cozy FPS streamer hub` for a custom layout\n\n"
        f"Invite: {url}",
        ephemeral=True,
    )


@bot.command(name="ping")
async def ping(ctx: commands.Context):
    await ctx.reply(f"pong · {round(bot.latency * 1000)}ms", mention_author=False)


def main() -> None:
    if not TOKEN:
        raise SystemExit("Set DISCORD_BOT_TOKEN")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
