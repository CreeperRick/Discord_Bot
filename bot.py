import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Optional
from datetime import datetime
import threading
import webbrowser

print("Starting bot.py...")

import discord
from discord.ext import commands, tasks
from discord import app_commands
import feedparser
import aiohttp
from flask import Flask, render_template_string, request

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

print(f"Monitoring {len(USERNAMES)} accounts, interval={CHECK_INTERVAL}min (RSS mode)")

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

# ---------- TikTok RSS + Thumbnail Fetch ----------
async def fetch_video_thumbnail(video_url: str) -> Optional[str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status != 200:
                    return None
                html = await resp.text()
                match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
                if match:
                    return match.group(1)
                match = re.search(r'<meta[^>]*name="twitter:image"[^>]*content="([^"]+)"', html)
                if match:
                    return match.group(1)
    except Exception as e:
        logger.debug(f"Thumbnail fetch failed: {e}")
    return None

def fetch_latest_video_rss(username):
    url = f"https://www.tiktok.com/@{username}/rss"
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            logger.warning(f"No entries in RSS feed for @{username}")
            return None
        latest = feed.entries[0]
        match = re.search(r'/video/(\d+)', latest.link)
        video_id = match.group(1) if match else "unknown"
        return type('Video', (), {
            'id': video_id,
            'desc': latest.title,
            'link': latest.link,
        })()
    except Exception as e:
        logger.error(f"RSS fetch failed for @{username}: {e}")
        return None

async def fetch_latest_video(username):
    video = fetch_latest_video_rss(username)
    if video and hasattr(video, 'link'):
        thumbnail = await fetch_video_thumbnail(video.link)
        if thumbnail:
            video.thumbnail = thumbnail
    return video

def build_video_embed(username, video, title=None, description_prefix="", color=0x00f2ea, footer=None):
    video_id = getattr(video, "id", "unknown")
    raw_desc = getattr(video, "desc", "")
    desc = raw_desc[:200] if raw_desc else "*No description*"
    embed = discord.Embed(
        title=title or f"📸 New TikTok from @{username}!",
        url=f"https://www.tiktok.com/@{username}/video/{video_id}",
        description=f"{description_prefix}{desc}",
        color=color,
    )
    embed.set_author(name=f"@{username}")
    if footer:
        embed.set_footer(text=footer)
    if hasattr(video, 'thumbnail') and video.thumbnail:
        embed.set_image(url=video.thumbnail)
    return embed

# ---------- Bot ----------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Web UI (Flask) ----------
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>TikTok Bot Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1e1e2f; color: #eee; }
        h1 { color: #00f2ea; }
        .card { background: #2a2a3a; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #444; }
        th { background: #00f2ea; color: #1e1e2f; }
        button, input[type=submit] { background: #00f2ea; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        input[type=text] { padding: 8px; border-radius: 5px; border: none; width: 200px; }
        .status-online { color: #4caf50; }
        a { color: #00f2ea; }
    </style>
</head>
<body>
    <h1>🤖 TikTok Monitor Dashboard</h1>
    <div class="card">
        <h2>Bot Status</h2>
        <p><strong>Status:</strong> <span class="status-online">● Online</span></p>
        <p><strong>Monitored Accounts:</strong> {{ accounts|length }}</p>
        <p><strong>Check Interval:</strong> {{ interval }} minutes</p>
        <p><strong>Notification Channel:</strong> <code>{{ channel_id }}</code></p>
        <p><strong>Ping Role:</strong> <code>{{ ping_role_id }}</code></p>
    </div>

    <div class="card">
        <h2>➕ Add Account</h2>
        <form action="/add" method="post">
            <input type="text" name="username" placeholder="TikTok username (without @)" required>
            <input type="submit" value="Add">
        </form>
    </div>

    <div class="card">
        <h2>📋 Monitored Accounts</h2>
        <table>
            <tr><th>Username</th><th>Last Video ID</th><th>Action</th></tr>
            {% for user in accounts %}
            <tr>
                <td>@{{ user }}</td>
                <td><code>{{ last_videos.get(user, 'N/A')[:20] }}</code></td>
                <td>
                    <form action="/remove" method="post" style="display:inline;">
                        <input type="hidden" name="username" value="{{ user }}">
                        <input type="submit" value="Remove" style="background:#f44336;">
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="card">
        <h2>🕹️ Actions</h2>
        <form action="/check_now" method="post" style="display:inline;">
            <input type="submit" value="▶️ Force Check Now">
        </form>
        <form action="/reset_all" method="post" style="display:inline;">
            <input type="submit" value="🔄 Reset All Tracking" style="background:#ff9800;">
        </form>
    </div>

    <div class="card">
        <h2>ℹ️ Info</h2>
        <p>This bot uses <strong>RSS feeds</strong> – no TikTokApi required.</p>
        <p>Last updated: {{ time }}</p>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE,
        accounts=USERNAMES,
        interval=CHECK_INTERVAL,
        channel_id=CHANNEL_ID,
        ping_role_id=PING_ROLE_ID,
        last_videos=load_last_videos(),
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/add', methods=['POST'])
def add_account_web():
    username = request.form.get('username', '').strip().lower().lstrip('@')
    if not username or username in USERNAMES:
        return "Invalid or duplicate", 400
    async def add():
        video = await fetch_latest_video(username)
        if video:
            USERNAMES.append(username)
            config["tiktok_usernames"] = USERNAMES
            save_config()
            last = load_last_videos()
            last[username] = video.id
            save_last_videos(last)
            return True
        return False
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(add())
    loop.close()
    if result:
        return "Added", 200
    return "Failed to fetch video", 400

@app.route('/remove', methods=['POST'])
def remove_account_web():
    username = request.form.get('username', '').strip().lower().lstrip('@')
    if username in USERNAMES:
        USERNAMES.remove(username)
        config["tiktok_usernames"] = USERNAMES
        save_config()
        last = load_last_videos()
        last.pop(username, None)
        save_last_videos(last)
        return "Removed", 200
    return "Not found", 404

@app.route('/check_now', methods=['POST'])
def check_now_web():
    asyncio.run_coroutine_threadsafe(check_tiktok(), bot.loop)
    return "Check triggered", 200

@app.route('/reset_all', methods=['POST'])
def reset_all_web():
    save_last_videos({})
    return "Reset", 200

def start_web_server():
    webbrowser.open("http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# ---------- Discord Events ----------
@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Monitoring {len(USERNAMES)} account(s) every {CHECK_INTERVAL} min via RSS")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")
    if not check_tiktok.is_running():
        check_tiktok.start()

    # Start web UI thread only once
    if not hasattr(bot, 'web_started'):
        bot.web_started = True
        thread = threading.Thread(target=start_web_server, daemon=True)
        thread.start()
        logger.info("Web UI started at http://127.0.0.1:5000")

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

# ---------- Slash Commands ----------
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
    embed.add_field(name="Method", value="RSS + optional thumbnail", inline=False)
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

@bot.tree.command(name="browser_info", description="Show current method (RSS mode)")
async def slash_browser_info(interaction: discord.Interaction):
    embed = discord.Embed(title="🌐 Current Mode", color=0x00f2ea)
    embed.add_field(name="Method", value="RSS feed (no browser required)", inline=False)
    embed.add_field(name="Thumbnails", value="Extracted from video page (if available)", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Show all available commands")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 TikTok Bot Commands", description="All available slash commands:", color=0x00f2ea)
    sections = {
        "📌 Basic": [
            ("/ping", "Check bot latency"),
            ("/status", "Show monitoring status"),
            ("/accounts", "List monitored accounts"),
            ("/browser_info", "Show current method (RSS)"),
            ("/help", "This message"),
        ],
        "🔧 Management": [
            ("/add_account <username>", "Add a TikTok account"),
            ("/remove_account <username>", "Remove an account"),
            ("/set_channel <#channel>", "Set notification channel"),
            ("/set_interval <minutes>", "Change check frequency"),
            ("/set_ping_role <@role>", "Change ping role"),
            ("/check_now", "Manually trigger a check"),
        ],
        "🧪 Testing": [
            ("/test <username>", "Send test notification"),
            ("/test_all", "Test all monitored accounts"),
            ("/test_reset [username]", "Reset stored video IDs"),
            ("/test_force <username>", "Force a notification"),
            ("/test_info <username>", "Inspect account without notifying"),
            ("/test_performance", "Benchmark response times"),
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

@bot.tree.command(name="check_now", description="Manually check for new videos right now")
async def slash_check_now(interaction: discord.Interaction):
    await interaction.response.send_message("🔍 Checking for new videos...", ephemeral=True)
    await check_tiktok()
    await interaction.followup.send("✅ Check completed!", ephemeral=True)

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
    if hasattr(video, 'thumbnail') and video.thumbnail:
        embed.set_thumbnail(url=video.thumbnail)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="test_performance", description="Benchmark response time for all monitored accounts")
async def slash_test_performance(interaction: discord.Interaction):
    if not USERNAMES:
        await interaction.response.send_message("❌ No accounts to benchmark.", ephemeral=True)
        return
    await interaction.response.send_message("⏱️ Running performance test...", ephemeral=True)
    results = []
    for username in USERNAMES:
        start = asyncio.get_event_loop().time()
        video = await fetch_latest_video(username)
        elapsed = (asyncio.get_event_loop().time() - start) * 1000
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
