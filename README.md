# TikTok → Discord Notification Bot

Watches multiple TikTok accounts and posts a Discord embed when a new video appears.

## Requirements
- Python 3.8 or newer
- A Discord bot token (create one at https://discord.com/developers/applications)
- The bot invited to your server with the `Send Messages` and `Embed Links` permissions

## Setup

1. **Install dependencies**
```
git clone https://github.com/CreeperRick/Discord_Bot
cd Discord_Bot
pip install discord.py feedparser aiohttp
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

# TikTok → Discord Notification Bot with Slash Commands

Watches multiple TikTok accounts, **pings a role**, and posts a Discord embed when a new video appears.

## Slash Commands Available

Once the bot is running, type `/` in Discord to see all commands:

| Command | Description |
|---------|-------------|
| `/ping` | Check if bot is responsive |
| `/status` | Show current monitoring status |
| `/accounts` | List all monitored TikTok accounts |
| `/add_account <username>` | Add a TikTok account to monitor |
| `/remove_account <username>` | Remove a TikTok account from monitoring |
| `/check_now` | Manually check for new videos |
| `/set_channel <#channel>` | Set the notification channel |
| `/set_interval <minutes>` | Change check interval (1-60 min) |
| `/set_ping_role <@role>` | Change which role gets pinged |
| `/help` | Show all commands |

## How it works
- On first run it saves the most recent video ID for each account so it won’t spam notifications for existing videos.
- When a new video is detected, it sends an embed to the specified Discord channel.
- The bot runs forever; stop it with `Ctrl+C`.

## Troubleshooting
- **No notifications?** Check the console logs for errors. If TikTokApi can’t fetch videos, try increasing `check_interval` to avoid rate limits.
- **Playwright issues?** Make sure you ran `playwright install` and that your system can run a headless browser.

Enjoy!

