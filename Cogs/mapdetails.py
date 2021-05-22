import discord
from discord.ext import commands

from Libraries.maps import *
from Libraries.bot_config import get_config

cfg = get_config()

class MapDetails(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.command(help="Gives details for a map, including size and image")
    async def mapdetails(self, ctx):
        map_name = str(ctx.message.content.split(' ', 1)[1])

        map_names = get_map_names(cfg, lower=True)
        if map_name.lower() not in map_names:
            print("not in list")
            await ctx.send(f"Available maps:\n{map_names}")
            return

        map_details = get_map_details(cfg, map_name)

        map_name = map_details["name"]
        #map_location = map_details["image_location"] # TODO: Add location and size to API
        #map_size = map_details["size"]

        await ctx.send(map_name)

def setup(bot:commands.Bot):
    bot.add_cog(MapDetails(bot))