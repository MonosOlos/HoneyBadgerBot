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
        map_name = str(ctx.message.content.split(' ', 1)[1]).title()
        await ctx.send(map_name)
        map_image_link = fetch_image_link(map_name) # TODO: Add location and size to API
        await ctx.send(map_image_link)
'''
        map_names = get_map_names(cfg, lower=True)
        if map_name.lower() not in map_names:
            await ctx.send(f"Available maps:\n{map_names}")
            pass

        map_details = get_map_details(cfg, map_name)

        map_name = map_details["name"]
        
        #map_size = map_details["size"]
'''
        

def setup(bot:commands.Bot):
    bot.add_cog(MapDetails(bot))