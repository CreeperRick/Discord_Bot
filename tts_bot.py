"""Discord TTS + consent-based personal voice cloning bot.

Built-in voices use Microsoft Edge TTS. Personal voices use Coqui XTTS v2.
The clone command is intentionally scoped to the requesting Discord user and
requires an explicit ownership/permission confirmation.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
import edge_tts

DATA_DIR = Path(os.getenv("TTS_DATA_DIR", "data/voices"))
VOICE_DB = DATA_DIR / "voices.json"
MODEL_DIR = Path(os.getenv("XTTS_MODEL_DIR", "models/xtts"))
DEFAULT_VOICE = os.getenv("DEFAULT_TTS_VOICE", "en-US-AriaNeural")
MAX_TEXT = 1200

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("discord_tts")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

BUILTIN_VOICES = {
    "aria": "en-US-AriaNeural",
    "jenny": "en-US-JennyNeural",
    "guy": "en-US-GuyNeural",
    "ryan": "en-GB-RyanNeural",
    "sonia": "en-GB-SoniaNeural",
    "elsa": "de-DE-KatjaNeural",
    "france": "fr-FR-DeniseNeural",
    "spanish": "es-ES-ElviraNeural",
    "dutch": "nl-NL-FennaNeural",
}


def load_db() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not VOICE_DB.exists():
        return {}
    try:
        return json.loads(VOICE_DB.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log.warning("Invalid voice database; starting with an empty database")
        return {}


def save_db(db: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VOICE_DB.write_text(json.dumps(db, indent=2), encoding="utf-8")


def safe_name(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip())[:32].strip("-")
    return name or "my-voice"


def get_user_voices(user_id: int) -> dict:
    return load_db().get(str(user_id), {})


def resolve_builtin(name: str) -> str | None:
    key = name.lower().strip()
    if key in BUILTIN_VOICES:
        return BUILTIN_VOICES[key]
    if key in BUILTIN_VOICES.values():
        return key
    return None


async def synthesize_builtin(text: str, voice: str, output: Path) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output))


_xtts = None
_xtts_lock = asyncio.Lock()


async def get_xtts():
    global _xtts
    async with _xtts_lock:
        if _xtts is None:
            def load():
                from TTS.api import TTS
                MODEL_DIR.mkdir(parents=True, exist_ok=True)
                return TTS("tts_models/multilingual/multi-dataset/xtts_v2", model_dir=str(MODEL_DIR))
            _xtts = await asyncio.to_thread(load)
    return _xtts


async def synthesize_clone(sample: Path, text: str, output: Path) -> None:
    tts = await get_xtts()
    await asyncio.to_thread(
        tts.tts_to_file,
        text=text,
        speaker_wav=str(sample),
        language="en",
        file_path=str(output),
    )


async def play_audio(interaction: discord.Interaction, audio_file: Path) -> None:
    if not interaction.user.voice or not interaction.user.voice.channel:
        raise RuntimeError("Join a voice channel first.")
    channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client if interaction.guild else None
    if voice_client and voice_client.channel != channel:
        await voice_client.move_to(channel)
    elif not voice_client:
        voice_client = await channel.connect()

    if voice_client.is_playing():
        voice_client.stop()

    source = discord.FFmpegPCMAudio(str(audio_file))
    done = asyncio.Event()

    def after(error):
        if error:
            log.error("Playback error: %s", error)
        bot.loop.call_soon_threadsafe(done.set)

    voice_client.play(source, after=after)
    await done.wait()


@bot.event
async def on_ready():
    log.info("Logged in as %s", bot.user)
    try:
        synced = await bot.tree.sync()
        log.info("Synced %d slash commands", len(synced))
    except Exception:
        log.exception("Slash-command sync failed")


@bot.tree.command(name="tts", description="Speak text in your current Discord voice channel")
@app_commands.describe(text="Text to speak", voice="Built-in voice name or one of your saved voice names")
async def tts(interaction: discord.Interaction, text: str, voice: str = DEFAULT_VOICE):
    text = text.strip()
    if not text or len(text) > MAX_TEXT:
        await interaction.response.send_message(f"Text must be 1-{MAX_TEXT} characters.", ephemeral=True)
        return
    if not interaction.guild:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    output = Path(tempfile.mktemp(suffix=".mp3"))
    try:
        builtin = resolve_builtin(voice)
        if builtin:
            await synthesize_builtin(text, builtin, output)
        else:
            saved = get_user_voices(interaction.user.id)
            if voice not in saved:
                raise RuntimeError("That voice is not available. Use /voices to see your voices.")
            await synthesize_clone(Path(saved[voice]["sample"]), text, output)
        await play_audio(interaction, output)
        await interaction.followup.send(f"🔊 Spoke using **{voice}**.", ephemeral=True)
    except Exception as exc:
        log.exception("TTS failed")
        await interaction.followup.send(f"❌ TTS failed: {exc}", ephemeral=True)
    finally:
        output.unlink(missing_ok=True)


@bot.tree.command(name="voices", description="List built-in voices and your personal voice clones")
async def voices(interaction: discord.Interaction):
    mine = get_user_voices(interaction.user.id)
    builtins = ", ".join(f"`{k}`" for k in BUILTIN_VOICES)
    custom = ", ".join(f"`{k}`" for k in mine) if mine else "None yet"
    embed = discord.Embed(title="🎙️ Available voices", color=0x5865F2)
    embed.add_field(name="Built-in", value=builtins, inline=False)
    embed.add_field(name="Your personal clones", value=custom, inline=False)
    embed.set_footer(text="Personal clones are only stored under your Discord user ID.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="clone_voice", description="Create a personal clone from your own voice recording")
@app_commands.describe(
    name="Name for your personal voice",
    sample="A clear WAV/MP3/M4A recording of your own voice",
    confirm="Confirm you own the voice or have explicit permission to clone it",
)
async def clone_voice(interaction: discord.Interaction, name: str, sample: discord.Attachment, confirm: bool):
    if not confirm:
        await interaction.response.send_message(
            "For safety, you must set **confirm** to true and only upload your own voice (or a voice you have explicit permission to clone).",
            ephemeral=True,
        )
        return
    if sample.size > 15 * 1024 * 1024:
        await interaction.response.send_message("The sample is too large (15 MB maximum).", ephemeral=True)
        return
    if not sample.content_type or not sample.content_type.startswith("audio/"):
        await interaction.response.send_message("Please upload an audio recording.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    name = safe_name(name)
    user_dir = DATA_DIR / str(interaction.user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    sample_path = user_dir / f"{name}{Path(sample.filename).suffix.lower() or '.wav'}"
    try:
        await sample.save(sample_path)
        # FFmpeg is required to decode most Discord audio formats.
        if not shutil.which("ffmpeg"):
            raise RuntimeError("FFmpeg is not installed on the bot host.")
        db = load_db()
        db.setdefault(str(interaction.user.id), {})[name] = {
            "sample": str(sample_path),
            "created_by": interaction.user.id,
            "consent_confirmed": True,
        }
        save_db(db)
        await interaction.followup.send(
            f"✅ Personal voice **{name}** saved. Use `/tts` with voice `{name}` to use it.",
            ephemeral=True,
        )
    except Exception as exc:
        sample_path.unlink(missing_ok=True)
        log.exception("Voice clone setup failed")
        await interaction.followup.send(f"❌ Could not save the voice: {exc}", ephemeral=True)


@bot.tree.command(name="delete_voice", description="Delete one of your personal voice clones")
@app_commands.describe(name="The personal voice to delete")
async def delete_voice(interaction: discord.Interaction, name: str):
    db = load_db()
    mine = db.get(str(interaction.user.id), {})
    item = mine.pop(name, None)
    if not item:
        await interaction.response.send_message("That personal voice does not exist.", ephemeral=True)
        return
    Path(item["sample"]).unlink(missing_ok=True)
    if mine:
        db[str(interaction.user.id)] = mine
    else:
        db.pop(str(interaction.user.id), None)
    save_db(db)
    await interaction.response.send_message(f"🗑️ Deleted **{name}**.", ephemeral=True)


@bot.tree.command(name="leave", description="Make the bot leave your voice channel")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client if interaction.guild else None
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("👋 Left the voice channel.", ephemeral=True)
    else:
        await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)


async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("Set DISCORD_TOKEN in your environment before starting the bot.")
    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
