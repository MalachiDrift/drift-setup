import discord

STREAMER_STRUCTURE = {
    "INFO": ["welcome", "rules", "announcements", "stream-schedule"],
    "LIVE": ["now-live", "stream-chat", "clips-and-highlights"],
    "COMMUNITY": ["general", "memes", "introductions", "off-topic"],
    "CREATORS": ["collab-wanted", "content-feedback", "resources"],
    "VOICE": [],
}
STREAMER_VOICE = ["Stage", "Chill", "Squad"]
STREAMER_ROLES = [
    ("Streamer", discord.Color.purple()),
    ("Mod", discord.Color.blue()),
    ("VIP", discord.Color.gold()),
    ("Viewer", discord.Color.light_grey()),
]
