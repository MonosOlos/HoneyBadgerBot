import discord
from discord.ext import commands
import json

token = "ODM4Njk5MTYxNjYyNTIxMzU1.YI-5dg.A-_HKb_M8jd1uo7C1d6xivIQx2g"

class Greetings(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self._last_member = None

# Intents
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot("£", intents = intents)

# Load cogs
initial_extensions = [
    "Cogs.challenge"
]

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f"Failed to load extension {extension}")

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name ="?help"))


bot.run(token)