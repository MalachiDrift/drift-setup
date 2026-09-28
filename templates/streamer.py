import discord

# INFO stays visible to @everyone (welcome/rules gate). Other cats locked until Viewer.
STREAMER_STRUCTURE = {
    "INFO": [
        "👋-welcome",
        "📜-rules",
        "📢-announcements",
        "📅-stream-schedule",
    ],
    "SOCIALS": [
        "🟣-twitch",
        "📺-youtube",
        "🎵-tiktok",
        "📸-instagram",
    ],
    "LIVE": [
        "🔴-now-live",
        "🎮-now-playing",
        "💬-stream-chat",
        "📹-clips",
    ],
    "COMMUNITY": [
        "💬-general",
        "🎮-looking-for-group",
        "😂-memes",
        "🙋-introductions",
        "💭-off-topic",
    ],
    "CREATORS": [
        "🎨-media",
        "🤝-collab-wanted",
        "📝-content-feedback",
        "📚-resources",
    ],
    "VOICE": [],
}
STREAMER_VOICE = ["🔊 Lobby", "🔊 Chill", "🔊 Squad"]
STREAMER_ROLES = [
    ("Streamer", discord.Color.purple()),
    ("Mod", discord.Color.blue()),
    ("VIP", discord.Color.gold()),
    ("Viewer", discord.Color.light_grey()),
]
STREAMER_MEMBER_ROLE = "Viewer"
STREAMER_PUBLIC_CATEGORIES = ("INFO",)
