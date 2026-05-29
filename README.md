# TikTok → Discord Notification Bot

Watches multiple TikTok accounts and posts a Discord embed when a new video appears.

## Requirements
- Python 3.8 or newer
- A Discord bot token (create one at https://discord.com/developers/applications)
- The bot invited to your server with the `Send Messages` and `Embed Links` permissions

## Setup

1. **Install dependencies**
```
git clone https://github.com/CreeperRick/Discord_Bot/tree/main
cd Discord_Bot
pip install -r requirements.txt
playwright install
```
The bot uses `TikTokApi` which needs a browser engine. The `playwright install` command downloads Chromium/Firefox.

2. **Configure the bot**
Open `config.json` and fill in:
- `token` – your Discord bot token
- `channel_id` – the numeric channel ID where notifications should appear
- `tiktok_usernames` – list of TikTok usernames (without @)
- `check_interval_minutes` – how often to check (recommended: 5)

3. **Run the bot**
   ```
   python bot.py
   ```
   The bot will log in, load the last known video IDs from `last_videos.json`, and start checking every X minutes.

## How it works
- On first run it saves the most recent video ID for each account so it won’t spam notifications for existing videos.
- When a new video is detected, it sends an embed to the specified Discord channel.
- The bot runs forever; stop it with `Ctrl+C`.

## Troubleshooting
- **No notifications?** Check the console logs for errors. If TikTokApi can’t fetch videos, try increasing `check_interval` to avoid rate limits.
- **Playwright issues?** Make sure you ran `playwright install` and that your system can run a headless browser.

Enjoy!
