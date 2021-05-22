import discord
from discord.ext import commands

from Libraries.maps import *
from Libraries.bot_config import get_config

cfg = get_config()

class MapList(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.command(help="Lists all maps in the current pool. Get map details and image with !mapdetails")
    async def maplist(self, ctx):
        maplist = get_map_names(cfg)
        
        map_names = ""

        for i in range(0, len(maplist)):               
            if i % 2 == 0:
                map_names += "\n"
            else:
                map_names += "  =H=  "
            map_names += ("**" + maplist[i] + "**")

        await ctx.send(map_names)

def setup(bot:commands.Bot):
    bot.add_cog(MapList(bot))