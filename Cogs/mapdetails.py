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
        
        map_details = liquipedia_get_page(map_name)
        if map_details == None:
            await ctx.send(f'Could not find a map for "{map_name}", please check spelling.')
            return
        
        map_image_url = liquipedia_get_image_url(map_details)

        del map_details["pageid"]

        output_string = ""
        for item in map_details:
            if map_details[item] != None:
                output_string += f'**{item}**: {map_details[item]}, \n'

        await ctx.send(output_string)
        await ctx.send(map_image_url)

        return

# https://liquipedia.net/starcraft2/api.php?action=query&prop=info&pageids=48483&inprop=url

def setup(bot:commands.Bot):
    bot.add_cog(MapDetails(bot))