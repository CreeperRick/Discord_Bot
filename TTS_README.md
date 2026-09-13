# Discord TTS + Personal Voice Cloning

This adds a second bot entry point, `tts_bot.py`, alongside the existing TikTok bot.

## Features

- `/tts` speaks text in the user's current voice channel.
- `/voices` lists built-in voices and the user's own saved voices.
- `/clone_voice` accepts an audio attachment and creates a personal voice profile.
- `/delete_voice` removes a personal voice.
- `/leave` disconnects from voice.
- Built-in voices use Microsoft Edge TTS.
- Personal clones use Coqui XTTS v2 locally.

## Consent

Only clone your own voice or a voice for which you have explicit permission. The bot stores personal samples under the Discord user ID that created them and does not expose them to other users.

## Install

```bash
sudo apt-get install ffmpeg
python -m pip install -r tts_requirements.txt
```

XTTS v2 is much heavier than normal TTS and works best with a machine that has a capable GPU. CPU inference can be slow.

## Configure

Set the Discord bot token as an environment variable rather than committing it:

```bash
export DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN"
python tts_bot.py
```

The bot needs the Discord permissions required to connect to and speak in voice channels. Enable the Voice-related permissions when inviting the bot.

## Commands

- `/tts text:Hello voice:aria`
- `/voices`
- `/clone_voice name:my-voice sample:<your audio> confirm:true`
- `/delete_voice name:my-voice`
- `/leave`

The first XTTS request downloads/loads the model and can take a while.
