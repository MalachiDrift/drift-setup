# drift-setup

Public Discord bot that scaffolds a server after you invite it.

## Streamer flow

1. Streamer creates a Discord (or empties one).
2. They make **you** an admin.
3. You invite this bot with **Administrator** (or Manage Channels + Manage Roles).
4. Run `/setup` → **Streamer** and enter the game.
5. Optional: `/build cozy horror streamer community` if `GROQ_API_KEY` is set.

`/setup` asks for the game, creates emoji-named channels (including socials), and gates the server behind a rules **I agree** button (Member/Viewer role). Keep the bot role **above** Member/Viewer.

## Commands

| Command | What it does |
|---------|----------------|
| `/setup` | Apply `streamer` or `basic` template (asks for **game**; emoji channels + rules gate) |
| `/build <description>` | Invent + create a custom layout (needs Groq) |
| `/delete` | Delete a specific channel or category (admins only) |
| `/invite` | Shows the OAuth invite link + flow |

Only server admins (or user IDs in `OWNER_IDS`) can run `/setup` and `/build`.

## Deploy (Railway)

1. Create a Discord Application → Bot → copy token.
2. Enable **Server Members Intent** only if you need it later (not required for setup).
3. Set Railway variables:
   - `DISCORD_BOT_TOKEN`
   - `OWNER_IDS` = your Discord user ID (so you can always run setup)
   - `GROQ_API_KEY` (optional)
4. Deploy this repo as a worker.

## Local

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
export DISCORD_BOT_TOKEN=...
export OWNER_IDS=your_discord_user_id
python bot.py
```

## Note

Discord will not create servers for random users via bot. The streamer creates the server; this bot **sets it up** once invited.
