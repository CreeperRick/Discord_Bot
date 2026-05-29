import asyncio
import json
import logging
from pathlib import Path

import discord
from discord.ext import commands, tasks
from TikTokApi import TikTokApi

# ---------- config ----------
CONFIG_PATH = Path("config.json")
LAST_VIDEOS_PATH = Path("last_videos.json")

with open(CONFIG_PATH, encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config["token"]
CHANNEL_ID = config["channel_id"]
USERNAMES = config["tiktok_usernames"]
CHECK_INTERVAL = config["check_interval_minutes"]

# ---------- logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tiktok_bot")

# ---------- storage ----------
def load_last_videos() -> dict[str, str]:
    if LAST_VIDEOS_PATH.exists():
        with open(LAST_VIDEOS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_last_videos(data: dict[str, str]) -> None:
    with open(LAST_VIDEOS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------- bot ----------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    check_tiktok.start()

@tasks.loop(minutes=CHECK_INTERVAL)
async def check_tiktok():
    """Check each TikTok account for a new video."""
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        logger.error(f"Channel ID {CHANNEL_ID} not found.")
        return

    last_videos = load_last_videos()

    async with TikTokApi() as api:
        for username in USERNAMES:
            try:
                user = api.user(username)
                # get the single most recent video
                videos = [v async for v in user.videos(count=1)]
                if not videos:
                    logger.warning(f"No videos found for @{username}")
                    continue

                latest = videos[0]
                video_id = latest.id
                previous_id = last_videos.get(username)

                if video_id == previous_id:
                    logger.info(f"No new video for @{username}")
                    continue

                # New video detected
                last_videos[username] = video_id
                save_last_videos(last_videos)

                # Build a clean Discord embed
                embed = discord.Embed(
                    title=f"New TikTok from @{username}!",
                    url=f"https://www.tiktok.com/@{username}/video/{video_id}",
                    description=latest.desc[:200] if latest.desc else "*No description*",
                    color=0x00f2ea,  # TikTok blue-ish
                )
                embed.set_author(name=f"@{username}")
                # Use the cover / dynamic cover as thumbnail if available
                if latest.as_dict.get("video", {}).get("cover"):
                    cover_url = latest.as_dict["video"]["cover"]
                    embed.set_image(url=cover_url)

                await channel.send(embed=embed)
                logger.info(f"Notified Discord about new video from @{username}: {video_id}")

                # Small delay between accounts to be polite to TikTok
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error checking @{username}: {e}")
                continue

# ---------- Run ----------
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
