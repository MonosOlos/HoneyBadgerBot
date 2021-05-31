import os
import json

import discord
from discord.ext import commands

from Libraries.maps import *
from Libraries.matches import *
from Libraries.bot_config import get_config

cfg = get_config()

# Intents
intents = discord.Intents.default()
intents.members = True

command_prefix = "!" 
bot = commands.Bot(command_prefix=command_prefix, intents=intents)

reporter = "<@!507367765884272641>" # MCauthon

# Loading cogs / extensions
initial_extensions = [
    "Cogs.challenge",
    "Cogs.mapdetails",
    "Cogs.maplist"
]

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f"Failed to load extension {extension}")

@bot.event
async def on_ready():
	print(f'Bot connected as {bot.user}')

bot.run(cfg["DISCORD_TOKEN"])
