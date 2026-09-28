import discord

# INFO stays visible to @everyone (welcome/rules gate). Other cats locked until Member.
BASIC_STRUCTURE = {
    "INFO": [
        "👋-welcome",
        "📜-rules",
        "📢-announcements",
    ],
    "SOCIALS": [
        "🟣-twitch",
        "📺-youtube",
        "🎵-tiktok",
    ],
    "CHAT": [
        "💬-general",
        "😂-memes",
        "💭-off-topic",
    ],
    "VOICE": [],
}
BASIC_VOICE = ["🔊 Lounge", "🎮 Gaming"]
BASIC_ROLES = [
    ("Admin", discord.Color.red()),
    ("Member", discord.Color.green()),
]
BASIC_MEMBER_ROLE = "Member"
BASIC_PUBLIC_CATEGORIES = ("INFO",)
