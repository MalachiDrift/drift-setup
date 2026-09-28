"""Shared helpers for drift-setup."""
from __future__ import annotations

import os
import re

import discord


def env(name: str) -> str:
    return (os.environ.get(name, "") or "").strip().strip('"').strip("'")


def slug(name: str) -> str:
    name = name.strip().lower().replace(" ", "-")
    name = re.sub(r"[^a-z0-9\-_]+", "", name)
    return name[:90] or "channel"


def channel_base(name: str) -> str:
    """ASCII slug tail of a channel name (strips leading emoji / decoration)."""
    return slug(re.sub(r"^[^\w]+", "", name, flags=re.UNICODE))


def find_text_by_base(guild: discord.Guild, *bases: str) -> discord.TextChannel | None:
    want = {b.lower() for b in bases}
    for ch in guild.text_channels:
        if channel_base(ch.name) in want or ch.name.lower() in want:
            return ch
    return None


def find_member_role(guild: discord.Guild, preferred: str | None = None) -> discord.Role | None:
    names = []
    if preferred:
        names.append(preferred)
    names.extend(["Viewer", "Member"])
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        role = discord.utils.get(guild.roles, name=name)
        if role:
            return role
    return None


def can_setup(member: discord.Member, owner_ids: set[int]) -> bool:
    if member.id in owner_ids:
        return True
    perms = member.guild_permissions
    return perms.administrator or (
        perms.manage_guild and perms.manage_channels and perms.manage_roles
    )
