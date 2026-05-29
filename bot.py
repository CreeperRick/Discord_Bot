import asyncio
import json
import logging
from pathlib import Path

import discord
from discord.ext import commands, tasks
from discord import app_commands
from TikTokApi import TikTokApi

# ---------- config ----------
CONFIG_PATH = Path("config.json")
LAST_VIDEOS_PATH = Path("last_videos.json")

with open(CONFIG_PATH, encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config["token"]
CHANNEL_ID = config["channel_id"]
PING_ROLE_ID = config["ping_role_id"]
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
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")
    check_tiktok.start()

# ---------- Helper Functions for Testing ----------
async def fetch_latest_video(username: str):
    """Fetch the latest video from a TikTok user"""
    try:
        async with TikTokApi() as api:
            user = api.user(username)
            videos = [v async for v in user.videos(count=1)]
            if videos:
                return videos[0]
            return None
    except Exception as e:
        logger.error(f"Error fetching video for @{username}: {e}")
        return None

async def send_test_notification(channel, username, video):
    """Send a test notification (same format as real one, but with TEST label)"""
    embed = discord.Embed(
        title=f"🧪 TEST: New TikTok from @{username}!",
        url=f"https://www.tiktok.com/@{username}/video/{video.id}",
        description=f"[TEST MODE] {video.desc[:200] if video.desc else '*No description*'}",
        color=0xffaa00,  # Orange color for test mode
    )
    embed.set_author(name=f"@{username}")
    embed.set_footer(text="🧪 TEST NOTIFICATION - No video was actually posted")
    
    if video.as_dict.get("video", {}).get("cover"):
        cover_url = video.as_dict["video"]["cover"]
        embed.set_image(url=cover_url)
    
    await channel.send(embed=embed)

# ---------- Slash Commands ----------

@bot.tree.command(name="ping", description="Check if the bot is responsive")
async def slash_ping(interaction: discord.Interaction):
    """Simple ping command to test the bot"""
    await interaction.response.send_message(f"Pong! 🏓 Latency: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="test", description="Test the bot with any TikTok account")
@app_commands.describe(
    username="TikTok username to test (without @)",
    ping_role="Whether to ping the role in test mode"
)
async def slash_test(interaction: discord.Interaction, username: str, ping_role: bool = False):
    """Manually test the bot by fetching and displaying a TikTok video"""
    username = username.lower().strip()
    
    await interaction.response.defer()
    
    # Fetch the latest video
    video = await fetch_latest_video(username)
    
    if not video:
        await interaction.followup.send(f"❌ Could not fetch video from `@{username}`. Make sure the account exists and has videos.", ephemeral=True)
        return
    
    # Send test notification
    channel = interaction.channel
    
    if ping_role:
        await channel.send(f"<@&{PING_ROLE_ID}>")
    
    await send_test_notification(channel, username, video)
    
    await interaction.followup.send(f"✅ Test notification sent for `@{username}`! Video ID: `{video.id}`", ephemeral=True)

@bot.tree.command(name="test_all", description="Test all monitored accounts at once")
async def slash_test_all(interaction: discord.Interaction):
    """Test all currently monitored accounts"""
    if not USERNAMES:
        await interaction.response.send_message("❌ No accounts are currently being monitored. Add some with `/add_account`", ephemeral=True)
        return
    
    await interaction.response.send_message(f"🧪 Testing {len(USERNAMES)} account(s)...", ephemeral=True)
    
    channel = interaction.channel
    success_count = 0
    
    for username in USERNAMES:
        video = await fetch_latest_video(username)
        if video:
            await send_test_notification(channel, username, video)
            success_count += 1
            await asyncio.sleep(1)  # Small delay between notifications
    
    await interaction.followup.send(f"✅ Test complete! Sent {success_count}/{len(USERNAMES)} test notifications.", ephemeral=True)

@bot.tree.command(name="test_reset", description="Reset last video ID to force notification on next check")
@app_commands.describe(username="TikTok username to reset (leave empty for all)")
async def slash_test_reset(interaction: discord.Interaction, username: str = None):
    """Reset stored video IDs to trigger notifications on next automatic check"""
    last_videos = load_last_videos()
    
    if username:
        username = username.lower().strip()
        if username in last_videos:
            old_id = last_videos[username]
            del last_videos[username]
            save_last_videos(last_videos)
            await interaction.response.send_message(f"🔄 Reset tracking for `@{username}`. Last known video `{old_id}` was removed. Next check will notify as if it's new!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ `@{username}` not found in tracked accounts.", ephemeral=True)
    else:
        # Reset all accounts
        count = len(last_videos)
        save_last_videos({})
        await interaction.response.send_message(f"🔄 Reset tracking for all {count} account(s). Next check will notify for all monitored accounts!", ephemeral=True)

@bot.tree.command(name="test_force", description="Force a notification for an account (even if no new video)")
@app_commands.describe(
    username="TikTok username to force notify",
    custom_message="Optional custom message for the notification"
)
async def slash_test_force(interaction: discord.Interaction, username: str, custom_message: str = None):
    """Force send a notification for any account (testing only)"""
    username = username.lower().strip()
    
    await interaction.response.defer()
    
    # Try to fetch video
    video = await fetch_latest_video(username)
    
    if not video:
        await interaction.followup.send(f"❌ Could not fetch video from `@{username}`.", ephemeral=True)
        return
    
    channel = interaction.channel
    
    # Create forced notification
    embed = discord.Embed(
        title=f"⚠️ FORCED TEST: @{username}",
        url=f"https://www.tiktok.com/@{username}/video/{video.id}",
        description=custom_message or f"[FORCED TEST] This is a manual test notification for @{username}",
        color=0xff4444,  # Red color for forced test
    )
    embed.set_author(name=f"@{username}")
    embed.set_footer(text="⚠️ FORCED TEST - Manual trigger")
    
    if video.as_dict.get("video", {}).get("cover"):
        cover_url = video.as_dict["video"]["cover"]
        embed.set_image(url=cover_url)
    
    await channel.send(f"<@&{PING_ROLE_ID}>", embed=embed)
    await interaction.followup.send(f"✅ Forced test notification sent for `@{username}`!", ephemeral=True)

@bot.tree.command(name="test_info", description="Get info about a TikTok account without sending notification")
@app_commands.describe(username="TikTok username to inspect")
async def slash_test_info(interaction: discord.Interaction, username: str):
    """Get detailed information about a TikTok account's latest video"""
    username = username.lower().strip()
    
    await interaction.response.defer()
    
    video = await fetch_latest_video(username)
    
    if not video:
        await interaction.followup.send(f"❌ Could not fetch info for `@{username}`", ephemeral=True)
        return
    
    # Get last stored ID
    last_videos = load_last_videos()
    stored_id = last_videos.get(username, "Not tracked")
    is_new = stored_id != video.id
    
    embed = discord.Embed(
        title=f"📊 TikTok Info: @{username}",
        color=0x00f2ea
    )
    embed.add_field(name="Latest Video ID", value=f"`{video.id}`", inline=False)
    embed.add_field(name="Stored Video ID", value=f"`{stored_id}`", inline=False)
    embed.add_field(name="Status", value="✅ NEW VIDEO" if is_new and stored_id != "Not tracked" else "Already seen" if not is_new and stored_id != "Not tracked" else "First time checking", inline=True)
    embed.add_field(name="Video URL", value=f"[Click to view](https://www.tiktok.com/@{username}/video/{video.id})", inline=True)
    embed.add_field(name="Description", value=video.desc[:200] if video.desc else "*No description*", inline=False)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="test_performance", description="Test API response time for all accounts")
async def slash_test_performance(interaction: discord.Interaction):
    """Test how long it takes to fetch videos from all monitored accounts"""
    if not USERNAMES:
        await interaction.response.send_message("❌ No accounts to test", ephemeral=True)
        return
    
    await interaction.response.send_message("⏱️ Running performance test...", ephemeral=True)
    
    results = []
    total_time = 0
    
    for username in USERNAMES:
        start = asyncio.get_event_loop().time()
        video = await fetch_latest_video(username)
        end = asyncio.get_event_loop().time()
        elapsed = (end - start) * 1000  # Convert to ms
        
        status = "✅" if video else "❌"
        results.append(f"{status} `@{username}`: {elapsed:.0f}ms")
        total_time += elapsed
    
    avg_time = total_time / len(USERNAMES)
    
    embed = discord.Embed(
        title="⏱️ Performance Test Results",
        description=f"Tested {len(USERNAMES)} account(s)",
        color=0x00f2ea
    )
    embed.add_field(name="Individual Times", value="\n".join(results), inline=False)
    embed.add_field(name="Average Response", value=f"{avg_time:.0f}ms", inline=True)
    embed.add_field(name="Total Time", value=f"{total_time:.0f}ms", inline=True)
    
    await interaction.followup.send(embed=embed)

# Keep existing commands (status, add_account, remove_account, etc.)
@bot.tree.command(name="status", description="Show current monitoring status")
async def slash_status(interaction: discord.Interaction):
    """Show which TikTok accounts are being monitored"""
    embed = discord.Embed(
        title="📊 TikTok Bot Status",
        color=0x00f2ea
    )
    embed.add_field(name="Monitored Accounts", value=f"**{len(USERNAMES)}** accounts", inline=False)
    embed.add_field(name="Accounts List", value=f"`{', '.join(USERNAMES)}`", inline=False)
    embed.add_field(name="Check Interval", value=f"Every **{CHECK_INTERVAL}** minutes", inline=True)
    embed.add_field(name="Notification Channel", value=f"<#{CHANNEL_ID}>", inline=True)
    embed.add_field(name="Ping Role", value=f"<@&{PING_ROLE_ID}>", inline=True)
    
    last_videos = load_last_videos()
    if last_videos:
        latest_text = "\n".join([f"**@{user}:** `{vid[:10]}...`" for user, vid in list(last_videos.items())[:5]])
        embed.add_field(name="Last Video IDs", value=latest_text, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="add_account", description="Add a TikTok username to monitor")
@app_commands.describe(username="TikTok username to monitor (without @)")
async def slash_add_account(interaction: discord.Interaction, username: str):
    """Add a new TikTok account to monitor"""
    username = username.lower().strip()
    
    if username in USERNAMES:
        await interaction.response.send_message(f"❌ Account `@{username}` is already being monitored!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    video = await fetch_latest_video(username)
    if not video:
        await interaction.followup.send(f"❌ Account `@{username}` not found or has no videos!", ephemeral=True)
        return
    
    USERNAMES.append(username)
    config["tiktok_usernames"] = USERNAMES
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    last_videos = load_last_videos()
    last_videos[username] = video.id
    save_last_videos(last_videos)
    
    await interaction.followup.send(f"✅ Added `@{username}` to monitored accounts!", ephemeral=True)
    
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"📝 **Account Added:** Now monitoring `@{username}`")

@bot.tree.command(name="remove_account", description="Remove a TikTok username from monitoring")
@app_commands.describe(username="TikTok username to remove (without @)")
async def slash_remove_account(interaction: discord.Interaction, username: str):
    username = username.lower().strip()
    
    if username not in USERNAMES:
        await interaction.response.send_message(f"❌ Account `@{username}` is not being monitored!", ephemeral=True)
        return
    
    USERNAMES.remove(username)
    config["tiktok_usernames"] = USERNAMES
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    last_videos = load_last_videos()
    if username in last_videos:
        del last_videos[username]
        save_last_videos(last_videos)
    
    await interaction.response.send_message(f"✅ Removed `@{username}` from monitored accounts!", ephemeral=True)
    
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"🗑️ **Account Removed:** No longer monitoring `@{username}`")

@bot.tree.command(name="accounts", description="List all monitored TikTok accounts")
async def slash_list_accounts(interaction: discord.Interaction):
    if not USERNAMES:
        await interaction.response.send_message("📭 No accounts are currently being monitored.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📱 Monitored TikTok Accounts",
        description=f"Monitoring **{len(USERNAMES)}** accounts",
        color=0x00f2ea
    )
    
    account_list = ""
    for i, username in enumerate(USERNAMES, 1):
        account_list += f"{i}. `@{username}`\n"
    
    embed.add_field(name="Accounts", value=account_list, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="check_now", description="Manually check for new videos immediately")
async def slash_check_now(interaction: discord.Interaction):
    await interaction.response.send_message("🔍 Manually checking for new videos...", ephemeral=True)
    await check_tiktok()
    await interaction.followup.send("✅ Check completed! Check the channel for any notifications.", ephemeral=True)

@bot.tree.command(name="set_channel", description="Set the notification channel")
@app_commands.describe(channel="The text channel to send notifications to")
async def slash_set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    global CHANNEL_ID
    CHANNEL_ID = channel.id
    config["channel_id"] = channel.id
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    await interaction.response.send_message(f"✅ Notification channel set to {channel.mention}!")

@bot.tree.command(name="set_interval", description="Set the check interval in minutes")
@app_commands.describe(minutes="How often to check for new videos (in minutes)")
async def slash_set_interval(interaction: discord.Interaction, minutes: int):
    if minutes < 1:
        await interaction.response.send_message("❌ Interval must be at least 1 minute!", ephemeral=True)
        return
    
    global CHECK_INTERVAL
    CHECK_INTERVAL = minutes
    config["check_interval_minutes"] = minutes
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    check_tiktok.change_interval(minutes=minutes)
    await interaction.response.send_message(f"✅ Check interval updated to **{minutes} minutes**!")

@bot.tree.command(name="set_ping_role", description="Set the role to ping for new videos")
@app_commands.describe(role="The role to ping when new videos are posted")
async def slash_set_ping_role(interaction: discord.Interaction, role: discord.Role):
    global PING_ROLE_ID
    PING_ROLE_ID = role.id
    config["ping_role_id"] = role.id
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    await interaction.response.send_message(f"✅ Ping role set to {role.mention}!")

@bot.tree.command(name="help", description="Show all available commands")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 TikTok Bot Commands",
        description="Here are all the available slash commands:",
        color=0x00f2ea
    )
    
    commands_info = {
        "📌 Basic Commands": {
            "/ping": "Check if bot is responsive",
            "/status": "Show current monitoring status",
            "/accounts": "List all monitored TikTok accounts",
            "/help": "Show this help message"
        },
        "🔧 Management Commands": {
            "/add_account <username>": "Add a TikTok account to monitor",
            "/remove_account <username>": "Remove a TikTok account",
            "/set_channel <#channel>": "Set notification channel",
            "/set_interval <minutes>": "Change check frequency",
            "/set_ping_role <@role>": "Change which role gets pinged",
            "/check_now": "Manually check for new videos"
        },
        "🧪 Testing Commands": {
            "/test <username> [ping_role]": "Test any TikTok account",
            "/test_all": "Test all monitored accounts",
            "/test_reset [username]": "Reset stored video IDs",
            "/test_force <username> [message]": "Force a notification",
            "/test_info <username>": "Get account info without notifying",
            "/test_performance": "Test API response times"
        }
    }
    
    for category, cmds in commands_info.items():
        cmd_text = "\n".join([f"**{cmd}** - {desc}" for cmd, desc in cmds.items()])
        embed.add_field(name=category, value=cmd_text, inline=False)
    
    embed.set_footer(text="Use / followed by the command name in Discord")
    await interaction.response.send_message(embed=embed)

# ---------- Background Task ----------
@tasks.loop(minutes=CHECK_INTERVAL)
async def check_tiktok():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        logger.error(f"Channel ID {CHANNEL_ID} not found.")
        return

    last_videos = load_last_videos()

    async with TikTokApi() as api:
        for username in USERNAMES:
            try:
                user = api.user(username)
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

                last_videos[username] = video_id
                save_last_videos(last_videos)

                embed = discord.Embed(
                    title=f"New TikTok from @{username}!",
                    url=f"https://www.tiktok.com/@{username}/video/{video_id}",
                    description=latest.desc[:200] if latest.desc else "*No description*",
                    color=0x00f2ea,
                )
                embed.set_author(name=f"@{username}")
                if latest.as_dict.get("video", {}).get("cover"):
                    cover_url = latest.as_dict["video"]["cover"]
                    embed.set_image(url=cover_url)
                embed.set_footer(text=f"Video ID: {video_id}")

                await channel.send(f"<@&{PING_ROLE_ID}>", embed=embed)
                logger.info(f"Notified Discord about new video from @{username}: {video_id}")

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
