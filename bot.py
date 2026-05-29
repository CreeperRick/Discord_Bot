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

# ---------- Slash Commands ----------

@bot.tree.command(name="ping", description="Check if the bot is responsive")
async def slash_ping(interaction: discord.Interaction):
    """Simple ping command to test the bot"""
    await interaction.response.send_message(f"Pong! 🏓 Latency: {round(bot.latency * 1000)}ms")

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
    
    # Load last video IDs
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
    
    # Verify the account exists
    await interaction.response.defer(ephemeral=True)
    
    try:
        async with TikTokApi() as api:
            user = api.user(username)
            videos = [v async for v in user.videos(count=1)]
            if not videos:
                await interaction.followup.send(f"❌ Account `@{username}` not found or has no videos!", ephemeral=True)
                return
    except Exception as e:
        await interaction.followup.send(f"❌ Error verifying account `@{username}`: {str(e)[:100]}", ephemeral=True)
        return
    
    # Add to config
    USERNAMES.append(username)
    config["tiktok_usernames"] = USERNAMES
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    # Initialize last_videos for this account
    last_videos = load_last_videos()
    async with TikTokApi() as api:
        user = api.user(username)
        videos = [v async for v in user.videos(count=1)]
        if videos:
            last_videos[username] = videos[0].id
            save_last_videos(last_videos)
    
    await interaction.followup.send(f"✅ Added `@{username}` to monitored accounts!", ephemeral=True)
    
    # Log to channel
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"📝 **Account Added:** Now monitoring `@{username}`")

@bot.tree.command(name="remove_account", description="Remove a TikTok username from monitoring")
@app_commands.describe(username="TikTok username to remove (without @)")
async def slash_remove_account(interaction: discord.Interaction, username: str):
    """Remove a TikTok account from monitoring"""
    username = username.lower().strip()
    
    if username not in USERNAMES:
        await interaction.response.send_message(f"❌ Account `@{username}` is not being monitored!", ephemeral=True)
        return
    
    # Remove from config
    USERNAMES.remove(username)
    config["tiktok_usernames"] = USERNAMES
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    # Remove from last_videos tracking
    last_videos = load_last_videos()
    if username in last_videos:
        del last_videos[username]
        save_last_videos(last_videos)
    
    await interaction.response.send_message(f"✅ Removed `@{username}` from monitored accounts!", ephemeral=True)
    
    # Log to channel
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"🗑️ **Account Removed:** No longer monitoring `@{username}`")

@bot.tree.command(name="accounts", description="List all monitored TikTok accounts")
async def slash_list_accounts(interaction: discord.Interaction):
    """List all currently monitored TikTok accounts"""
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
    """Force an immediate check for new videos"""
    await interaction.response.send_message("🔍 Manually checking for new videos...", ephemeral=True)
    
    # Run the check function
    await check_tiktok()
    
    await interaction.followup.send("✅ Check completed! Check the channel for any notifications.", ephemeral=True)

@bot.tree.command(name="set_channel", description="Set the notification channel")
@app_commands.describe(channel="The text channel to send notifications to")
async def slash_set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Change the notification channel"""
    global CHANNEL_ID
    CHANNEL_ID = channel.id
    config["channel_id"] = channel.id
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    await interaction.response.send_message(f"✅ Notification channel set to {channel.mention}!")

@bot.tree.command(name="set_interval", description="Set the check interval in minutes")
@app_commands.describe(minutes="How often to check for new videos (in minutes)")
async def slash_set_interval(interaction: discord.Interaction, minutes: int):
    """Change how often the bot checks for new videos"""
    if minutes < 1:
        await interaction.response.send_message("❌ Interval must be at least 1 minute!", ephemeral=True)
        return
    if minutes > 60:
        await interaction.response.send_message("⚠️ Interval over 60 minutes may cause delays. Recommended: 5-15 minutes", ephemeral=True)
    
    global CHECK_INTERVAL
    CHECK_INTERVAL = minutes
    config["check_interval_minutes"] = minutes
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    # Restart the loop with new interval
    check_tiktok.change_interval(minutes=minutes)
    
    await interaction.response.send_message(f"✅ Check interval updated to **{minutes} minutes**!")

@bot.tree.command(name="set_ping_role", description="Set the role to ping for new videos")
@app_commands.describe(role="The role to ping when new videos are posted")
async def slash_set_ping_role(interaction: discord.Interaction, role: discord.Role):
    """Change which role gets pinged"""
    global PING_ROLE_ID
    PING_ROLE_ID = role.id
    config["ping_role_id"] = role.id
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    await interaction.response.send_message(f"✅ Ping role set to {role.mention}!")

@bot.tree.command(name="help", description="Show all available commands")
async def slash_help(interaction: discord.Interaction):
    """Display help information for all commands"""
    embed = discord.Embed(
        title="🤖 TikTok Bot Commands",
        description="Here are all the available slash commands:",
        color=0x00f2ea
    )
    
    commands_info = {
        "/ping": "Check if the bot is responsive",
        "/status": "Show current monitoring status",
        "/accounts": "List all monitored TikTok accounts",
        "/add_account <username>": "Add a TikTok account to monitor",
        "/remove_account <username>": "Remove a TikTok account from monitoring",
        "/check_now": "Manually check for new videos",
        "/set_channel <channel>": "Set the notification channel",
        "/set_interval <minutes>": "Change check interval (1-60 minutes)",
        "/set_ping_role <role>": "Change which role gets pinged",
        "/help": "Show this help message"
    }
    
    for cmd, desc in commands_info.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.set_footer(text="Use / followed by the command name in Discord")
    await interaction.response.send_message(embed=embed)

# ---------- Background Task ----------
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

                # Ping the role and send embed
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
