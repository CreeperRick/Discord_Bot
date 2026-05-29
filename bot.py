import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple

print("Starting bot.py...")

import discord
from discord.ext import commands, tasks
from discord import app_commands
from TikTokApi import TikTokApi

print("Imports OK")

# ---------- Config ----------
CONFIG_PATH = Path("config.json")
LAST_VIDEOS_PATH = Path("last_videos.json")

if not CONFIG_PATH.exists():
    print("ERROR: config.json not found! Create it first.")
    exit(1)

with open(CONFIG_PATH, encoding="utf-8") as f:
    config = json.load(f)

print("Config loaded:", list(config.keys()))

TOKEN = config["token"]
CHANNEL_ID = int(config["channel_id"])
PING_ROLE_ID = int(config["ping_role_id"])
USERNAMES = config["tiktok_usernames"]
CHECK_INTERVAL = int(config["check_interval_minutes"])
BROWSER_PATH = config.get("browser_executable_path", None)

print(f"Monitoring {len(USERNAMES)} accounts, interval={CHECK_INTERVAL}min")

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tiktok_bot")

# ---------- Storage ----------
def load_last_videos():
    if LAST_VIDEOS_PATH.exists():
        with open(LAST_VIDEOS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_last_videos(data):
    with open(LAST_VIDEOS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def save_config():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

# ---------- TikTok Helpers ----------
async def fetch_latest_video(username):
    """Fetch the most recent video from a TikTok user. Returns None on failure."""
    try:
        async with TikTokApi() as api:
            kwargs = {
                "ms_tokens": [""],
                "num_sessions": 1,
                "headless": True,
            }
            if BROWSER_PATH:
                kwargs["executable_path"] = BROWSER_PATH
            await api.create_sessions(**kwargs)
            user = api.user(username)
            videos = [v async for v in user.videos(count=1)]
            return videos[0] if videos else None
    except Exception as e:
        logger.error(f"Error fetching video for @{username}: {e}")
        return None

def build_video_embed(username, video, title=None, description_prefix="", color=0x00f2ea, footer=None):
    """Build a Discord embed for a TikTok video."""
    desc = video.desc[:200] if video.desc else "*No description*"
    embed = discord.Embed(
        title=title or f"📸 New TikTok from @{username}!",
        url=f"https://www.tiktok.com/@{username}/video/{video.id}",
        description=f"{description_prefix}{desc}",
        color=color,
    )
    embed.set_author(name=f"@{username}")
    if footer:
        embed.set_footer(text=footer)
    cover = video.as_dict.get("video", {}).get("cover")
    if cover:
        embed.set_image(url=cover)
    return embed

# ---------- Bot ----------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(
        f"Browser: {BROWSER_PATH if BROWSER_PATH else 'auto-detect'} | "
        f"Monitoring {len(USERNAMES)} account(s) every {CHECK_INTERVAL} min"
    )
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")
    if not check_tiktok.is_running():
        check_tiktok.start()

# ---------- Background Task ----------
@tasks.loop(minutes=CHECK_INTERVAL)
async def check_tiktok():
    logger.info("Running scheduled TikTok check...")
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        logger.error(f"Channel {CHANNEL_ID} not found.")
        return

    last_videos = load_last_videos()
    updated = False

    for username in USERNAMES:
        video = await fetch_latest_video(username)
        if not video:
            continue

        if last_videos.get(username) == video.id:
            logger.info(f"No new video for @{username}")
            continue

        last_videos[username] = video.id
        updated = True

        embed = build_video_embed(username, video, footer=f"Video ID: {video.id}")
        await channel.send(content=f"<@&{PING_ROLE_ID}>", embed=embed)
        logger.info(f"Notified for new video from @{username}: {video.id}")
        await asyncio.sleep(2)

    if updated:
        save_last_videos(last_videos)

@check_tiktok.before_loop
async def before_check():
    await bot.wait_until_ready()

# ---------- Basic Commands ----------
@bot.tree.command(name="ping", description="Check if the bot is responsive")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 Latency: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="status", description="Show current monitoring status")
async def slash_status(interaction: discord.Interaction):
    embed = discord.Embed(title="📊 TikTok Bot Status", color=0x00f2ea)
    embed.add_field(name="Accounts", value=f"**{len(USERNAMES)}** monitored", inline=True)
    embed.add_field(name="Check Interval", value=f"Every **{CHECK_INTERVAL}** min", inline=True)
    embed.add_field(name="Notification Channel", value=f"<#{CHANNEL_ID}>", inline=True)
    embed.add_field(name="Ping Role", value=f"<@&{PING_ROLE_ID}>", inline=True)
    embed.add_field(
        name="Browser",
        value=f"`{BROWSER_PATH}`" if BROWSER_PATH else "Auto-detect",
        inline=False,
    )
    if USERNAMES:
        embed.add_field(
            name="Monitored Accounts",
            value="\n".join(f"`@{u}`" for u in USERNAMES),
            inline=False,
        )
    last_videos = load_last_videos()
    if last_videos:
        lines = [f"**@{u}:** `{vid[:12]}...`" for u, vid in list(last_videos.items())[:5]]
        embed.add_field(name="Last Known Video IDs", value="\n".join(lines), inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="accounts", description="List all monitored TikTok accounts")
async def slash_list_accounts(interaction: discord.Interaction):
    if not USERNAMES:
        await interaction.response.send_message("📭 No accounts are currently monitored.", ephemeral=True)
        return
    embed = discord.Embed(
        title="📱 Monitored TikTok Accounts",
        description="\n".join(f"{i}. `@{u}`" for i, u in enumerate(USERNAMES, 1)),
        color=0x00f2ea,
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="browser_info", description="Show browser configuration")
async def slash_browser_info(interaction: discord.Interaction):
    embed = discord.Embed(title="🌐 Browser Configuration", color=0x00f2ea)
    if BROWSER_PATH:
        exists = Path(BROWSER_PATH).exists()
        embed.add_field(name="Path", value=f"`{BROWSER_PATH}`", inline=False)
        embed.add_field(name="Status", value="✅ Custom browser configured", inline=True)
        embed.add_field(name="File Check", value="✅ Found" if exists else "❌ Not found!", inline=True)
    else:
        embed.add_field(name="Path", value="Auto-detect (Playwright default)", inline=False)
        embed.add_field(name="Status", value="ℹ️ Using default browser", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Show all available commands")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 TikTok Bot Commands", description="All available slash commands:", color=0x00f2ea)
    sections = {
        "📌 Basic": [
            ("/ping", "Check bot latency"),
            ("/status", "Show monitoring status"),
            ("/accounts", "List monitored accounts"),
            ("/browser_info", "Show browser config"),
            ("/help", "This message"),
        ],
        "🔧 Management": [
            ("/add_account <username>", "Add a TikTok account"),
            ("/remove_account <username>", "Remove an account"),
            ("/set_channel <#channel>", "Set notification channel"),
            ("/set_interval <minutes>", "Change check frequency"),
            ("/set_ping_role <@role>", "Change ping role"),
            ("/set_browser <path>", "Set browser path (or 'none')"),
            ("/check_now", "Manually trigger a check"),
        ],
        "🧪 Testing": [
            ("/test <username>", "Send test notification"),
            ("/test_all", "Test all monitored accounts"),
            ("/test_reset [username]", "Reset stored video IDs"),
            ("/test_force <username>", "Force a notification"),
            ("/test_info <username>", "Inspect account without notifying"),
            ("/test_performance", "Benchmark API response times"),
        ],
    }
    for section, cmds in sections.items():
        embed.add_field(
            name=section,
            value="\n".join(f"**{cmd}** — {desc}" for cmd, desc in cmds),
            inline=False,
        )
    embed.set_footer(text="Type / in Discord to see all commands")
    await interaction.response.send_message(embed=embed)

# ---------- Management Commands ----------
@bot.tree.command(name="add_account", description="Add a TikTok username to monitor")
@app_commands.describe(username="TikTok username (without @)")
async def slash_add_account(interaction: discord.Interaction, username: str):
    username = username.lower().strip().lstrip("@")
    if username in USERNAMES:
        await interaction.response.send_message(f"❌ `@{username}` is already monitored.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    video = await fetch_latest_video(username)
    if not video:
        await interaction.followup.send(f"❌ `@{username}` not found or has no videos.", ephemeral=True)
        return
    USERNAMES.append(username)
    config["tiktok_usernames"] = USERNAMES
    save_config()
    last_videos = load_last_videos()
    last_videos[username] = video.id
    save_last_videos(last_videos)
    await interaction.followup.send(f"✅ Now monitoring `@{username}`!", ephemeral=True)
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"📝 **Account Added:** Now monitoring `@{username}`")

@bot.tree.command(name="remove_account", description="Remove a TikTok username from monitoring")
@app_commands.describe(username="TikTok username (without @)")
async def slash_remove_account(interaction: discord.Interaction, username: str):
    username = username.lower().strip().lstrip("@")
    if username not in USERNAMES:
        await interaction.response.send_message(f"❌ `@{username}` is not being monitored.", ephemeral=True)
        return
    USERNAMES.remove(username)
    config["tiktok_usernames"] = USERNAMES
    save_config()
    last_videos = load_last_videos()
    last_videos.pop(username, None)
    save_last_videos(last_videos)
    await interaction.response.send_message(f"✅ Removed `@{username}` from monitoring.", ephemeral=True)
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"🗑️ **Account Removed:** No longer monitoring `@{username}`")

@bot.tree.command(name="set_channel", description="Set the notification channel")
@app_commands.describe(channel="Text channel for notifications")
async def slash_set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    global CHANNEL_ID
    CHANNEL_ID = channel.id
    config["channel_id"] = channel.id
    save_config()
    await interaction.response.send_message(f"✅ Notification channel set to {channel.mention}!")

@bot.tree.command(name="set_interval", description="Set the check interval in minutes")
@app_commands.describe(minutes="How often to check (minimum 1)")
async def slash_set_interval(interaction: discord.Interaction, minutes: int):
    if minutes < 1:
        await interaction.response.send_message("❌ Interval must be at least 1 minute.", ephemeral=True)
        return
    global CHECK_INTERVAL
    CHECK_INTERVAL = minutes
    config["check_interval_minutes"] = minutes
    save_config()
    check_tiktok.change_interval(minutes=minutes)
    await interaction.response.send_message(f"✅ Check interval updated to **{minutes} minutes**.")

@bot.tree.command(name="set_ping_role", description="Set the role to ping for new videos")
@app_commands.describe(role="Role to mention when new videos are posted")
async def slash_set_ping_role(interaction: discord.Interaction, role: discord.Role):
    global PING_ROLE_ID
    PING_ROLE_ID = role.id
    config["ping_role_id"] = role.id
    save_config()
    await interaction.response.send_message(f"✅ Ping role set to {role.mention}!")

@bot.tree.command(name="set_browser", description="Set the browser executable path")
@app_commands.describe(path="Full path to browser (e.g. /usr/bin/chromium-browser), or 'none' for auto-detect")
async def slash_set_browser(interaction: discord.Interaction, path: str):
    global BROWSER_PATH
    if path.lower() in ("none", "null", "auto"):
        BROWSER_PATH = None
        config["browser_executable_path"] = None
        await interaction.response.send_message("✅ Browser set to auto-detect.", ephemeral=True)
    elif Path(path).exists():
        BROWSER_PATH = path
        config["browser_executable_path"] = path
        await interaction.response.send_message(f"✅ Browser path set to `{path}`.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Path `{path}` does not exist.", ephemeral=True)
        return
    save_config()
    await interaction.followup.send("⚠️ **Restart the bot** for this change to take effect.", ephemeral=True)

@bot.tree.command(name="check_now", description="Manually check for new videos right now")
async def slash_check_now(interaction: discord.Interaction):
    await interaction.response.send_message("🔍 Checking for new videos...", ephemeral=True)
    await check_tiktok()
    await interaction.followup.send("✅ Check completed!", ephemeral=True)

# ---------- Testing Commands ----------
@bot.tree.command(name="test", description="Send a test notification for any TikTok account")
@app_commands.describe(
    username="TikTok username (without @)",
    ping_role="Whether to also ping the notification role",
)
async def slash_test(interaction: discord.Interaction, username: str, ping_role: bool = False):
    username = username.lower().strip().lstrip("@")
    await interaction.response.defer()
    video = await fetch_latest_video(username)
    if not video:
        await interaction.followup.send(f"❌ Could not fetch a video for `@{username}`.", ephemeral=True)
        return
    channel = interaction.channel
    if ping_role:
        await channel.send(f"<@&{PING_ROLE_ID}>")
    embed = build_video_embed(
        username, video,
        title=f"🧪 TEST: New TikTok from @{username}!",
        description_prefix="[TEST MODE] ",
        color=0xffaa00,
        footer="🧪 TEST NOTIFICATION — no video was actually posted",
    )
    await channel.send(embed=embed)
    await interaction.followup.send(f"✅ Test sent for `@{username}` (video `{video.id}`).", ephemeral=True)

@bot.tree.command(name="test_all", description="Send test notifications for all monitored accounts")
async def slash_test_all(interaction: discord.Interaction):
    if not USERNAMES:
        await interaction.response.send_message("❌ No accounts are being monitored.", ephemeral=True)
        return
    await interaction.response.send_message(f"🧪 Testing {len(USERNAMES)} account(s)...", ephemeral=True)
    channel = interaction.channel
    success = 0
    for username in USERNAMES:
        video = await fetch_latest_video(username)
        if video:
            embed = build_video_embed(
                username, video,
                title=f"🧪 TEST: New TikTok from @{username}!",
                description_prefix="[TEST MODE] ",
                color=0xffaa00,
                footer="🧪 TEST NOTIFICATION",
            )
            await channel.send(embed=embed)
            success += 1
            await asyncio.sleep(1)
    await interaction.followup.send(f"✅ Done! Sent {success}/{len(USERNAMES)} test notifications.", ephemeral=True)

@bot.tree.command(name="test_reset", description="Reset stored video IDs to re-trigger notifications")
@app_commands.describe(username="Username to reset, or leave empty to reset all")
async def slash_test_reset(interaction: discord.Interaction, username: Optional[str] = None):
    last_videos = load_last_videos()
    if username:
        username = username.lower().strip().lstrip("@")
        if username not in last_videos:
            await interaction.response.send_message(f"❌ `@{username}` has no stored video ID.", ephemeral=True)
            return
        del last_videos[username]
        save_last_videos(last_videos)
        await interaction.response.send_message(
            f"🔄 Reset `@{username}`. Next check will treat their latest video as new.", ephemeral=True
        )
    else:
        count = len(last_videos)
        save_last_videos({})
        await interaction.response.send_message(f"🔄 Reset tracking for all {count} account(s).", ephemeral=True)

@bot.tree.command(name="test_force", description="Force a notification for any account")
@app_commands.describe(username="TikTok username", custom_message="Optional message override")
async def slash_test_force(interaction: discord.Interaction, username: str, custom_message: Optional[str] = None):
    username = username.lower().strip().lstrip("@")
    await interaction.response.defer()
    video = await fetch_latest_video(username)
    if not video:
        await interaction.followup.send(f"❌ Could not fetch video for `@{username}`.", ephemeral=True)
        return
    embed = build_video_embed(
        username, video,
        title=f"⚠️ FORCED TEST: @{username}",
        description_prefix=custom_message + " " if custom_message else "[FORCED TEST] ",
        color=0xff4444,
        footer="⚠️ FORCED TEST — manual trigger",
    )
    await interaction.channel.send(content=f"<@&{PING_ROLE_ID}>", embed=embed)
    await interaction.followup.send(f"✅ Forced notification sent for `@{username}`.", ephemeral=True)

@bot.tree.command(name="test_info", description="Get info on an account's latest video without notifying")
@app_commands.describe(username="TikTok username")
async def slash_test_info(interaction: discord.Interaction, username: str):
    username = username.lower().strip().lstrip("@")
    await interaction.response.defer()
    video = await fetch_latest_video(username)
    if not video:
        await interaction.followup.send(f"❌ Could not fetch info for `@{username}`.", ephemeral=True)
        return
    last_videos = load_last_videos()
    stored_id = last_videos.get(username, "Not tracked")
    is_new = stored_id not in (video.id, "Not tracked")
    embed = discord.Embed(title=f"📊 TikTok Info: @{username}", color=0x00f2ea)
    embed.add_field(name="Latest Video ID", value=f"`{video.id}`", inline=False)
    embed.add_field(name="Stored Video ID", value=f"`{stored_id}`", inline=False)
    embed.add_field(
        name="Status",
        value="✅ NEW VIDEO" if is_new else ("Already seen" if stored_id != "Not tracked" else "First time checking"),
        inline=True,
    )
    embed.add_field(name="Video URL", value=f"[Open TikTok](https://www.tiktok.com/@{username}/video/{video.id})", inline=True)
    embed.add_field(name="Description", value=video.desc[:300] if video.desc else "*No description*", inline=False)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="test_performance", description="Benchmark API response time for all monitored accounts")
async def slash_test_performance(interaction: discord.Interaction):
    if not USERNAMES:
        await interaction.response.send_message("❌ No accounts to benchmark.", ephemeral=True)
        return
    await interaction.response.send_message("⏱️ Running performance test...", ephemeral=True)
    results = []
    loop = asyncio.get_event_loop()
    for username in USERNAMES:
        t0 = loop.time()
        video = await fetch_latest_video(username)
        elapsed = (loop.time() - t0) * 1000
        results.append((username, elapsed, video is not None))
    avg = sum(r[1] for r in results) / len(results)
    embed = discord.Embed(
        title="⏱️ Performance Test Results",
        description=f"Tested **{len(USERNAMES)}** account(s)",
        color=0x00f2ea,
    )
    embed.add_field(
        name="Results",
        value="\n".join(f"{'✅' if ok else '❌'} `@{u}`: {ms:.0f}ms" for u, ms, ok in results),
        inline=False,
    )
    embed.add_field(name="Average", value=f"{avg:.0f}ms", inline=True)
    embed.add_field(name="Total", value=f"{sum(r[1] for r in results):.0f}ms", inline=True)
    await interaction.followup.send(embed=embed)

# ---------- Run ----------
if __name__ == "__main__":
    logger.info("Calling bot.run()...")
    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
