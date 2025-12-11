#!/usr/bin/env python3
"""
Run script for Discord Bot
"""
import os
import sys

# Check for required token
if not os.getenv('DISCORD_TOKEN'):
    print("Error: DISCORD_TOKEN environment variable not set!")
    print("Create a .env file with your token or export it:")
    print("  export DISCORD_TOKEN='your_token_here'")
    print("Or create .env file from .env.example")
    sys.exit(1)

# Run the bot
import asyncio
from main import main

if __name__ == '__main__':
    asyncio.run(main())
