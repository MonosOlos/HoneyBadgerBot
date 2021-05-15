import os
import json

import discord
from discord.ext import commands
import asyncio

from Libraries.maps import *
from Libraries.matches import *
from Libraries.bot_config import get_config
cfg = get_config()

bot = commands.Bot(command_prefix='?')

@bot.event
async def on_ready():
	print(f'Bot connected as {bot.user}')

# No input, outputs list of maps
@bot.command(help="Lists all maps in the current pool. Get map details and image with !mapdetails")
async def maplist(ctx):
    maplist = get_map_names(cfg)
    
    map_names = ""

    for i in range(0, len(maplist)):               
        if i % 2 == 0:
            map_names += "\n"
        else:
            map_names += "  =H=  "
        map_names += ("**" + maplist[i] + "**")

    await ctx.send(map_names)


# Takes map name as input, outputs map name, size, and image
@bot.command(help="Gives details for a map, including size and image")
async def mapdetails(ctx):
    map_name = str(ctx.message.content.split(' ', 1)[1])

    map_names = get_map_names(cfg, lower=True)
    if map_name.lower() not in map_names:
        print("not in list")
        await ctx.send(f"Available maps:\n{map_names}")
        return

    map_details = get_map_details(cfg, map_name)

    map_name = map_details["name"]
    #map_location = map_details["image_location"]
    #map_size = map_details["size"]

    await ctx.send(map_name)

# Takes a discord tag as input
# TODO: Hook up to API
@bot.command(help="Sends a challenge. If accepted, creates a match tracked on https://www.honeybadgersc2mod.com/")
async def challenge(ctx):
    content = str(ctx.message.content)
    if not (len(content.split()) == 2 and "<@!" in content):
        await ctx.send("Invalid Challenge. Usage:\n**!challenge @username**")
        return

    challenger_id = ctx.message.author.id
    challenger_mention = ctx.message.author.mention

    recipient_id = ctx.message.mentions[0].id
    recipient_mention = ctx.message.mentions[0].mention

    '''
    if challenger_id == recipient_id:
        await ctx.send("You can't challenge yourself! Usage:\n**!challenge @username**")
        return
    '''

    challenger_pk = get_player_key(cfg, challenger_id)
    recipient_pk = get_player_key(cfg, recipient_id)

    await ctx.send(
        f"""
**Challenger:** ID = {challenger_id}, Tag = {challenger_mention}, PK = {challenger_pk}
**Recipient:** ID = {recipient_id}, Tag = {recipient_mention}, PK = {recipient_pk}"""
        )

    '''
    if recipient_pk == False:
        reporter = "<@!507367765884272641>" # MCauthon
        await ctx.send(f"Could not find recipient on the system. {reporter} please fix.")
        return
    '''

    # Check for response
    def check(reaction, user):
        my_check = user == ctx.message.author and str(reaction.emoji) == "👍" and ctx.message.author.id == recipient_id
        print(my_check)
        return my_check

    try:
        await bot.add_reaction(ctx.message, "👍")
        reaction = await bot.wait_for("reaction_add", timeout=86400, check = check) # 86400 = 24 hours

    except asyncio.TimeoutError:
        await ctx.send(f"Hi {challenger_mention}, you challenged {recipient_mention}, but they chickened out (did not accept in time).")
        return
    
    match_details = make_match(cfg, player1_pk=challenger_pk, player2_pk=recipient_pk)

    add_match(cfg, match_details)

    await ctx.send(f"**MATCH CREATED:** {challenger_mention} vs {recipient_mention} on {match_details['map_name']}")

    return






'''
    @bot.event
    async def on_reaction_add(reaction, user):
        print(reaction.message.content)
        if reaction.emoji == '👍':
            await ctx.send("Hello")
'''

'''
    @bot.event
    async def on_raw_reaction_add(payload):
        channel = bot.get_channel(payload.channel_id)
        # skip DM messages
        if isinstance(channel, discord.DMChannel):
            return

        message = await channel.fetch_message(payload.message_id)
        guild = bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        emoji = payload.emoji.name
        reaction = discord.utils.get(message.reactions, emoji=emoji)

        print(message.author.id)
        if message.author.id != cfg["BOT_ID"]:
            return
        
        print("Hello")

        #print(f"{guild}\n{user}\n{emoji}\n{reaction}")
        #print(payload.user_id)
        #print(message.author.name)
'''
bot.run(cfg["DISCORD_TOKEN"])


'''
@bot.command(help="Accepts a challenge. Needs to be a reply to a challenge message.")
async def accept(ctx):
    content = str(ctx.message)
    print(content)
    
    msg = await ctx.send("Hello")
    await msg.add_reaction("\N{THUMBS UP SIGN}") 

    #reaction = await bot.wait_for_reaction(emoji="👍", message=msg)
    #reaction = await bot.wait_for_reaction(['\N{SMILE}', custom_emoji], msg1)
    #await bot.say("You responded with {}".format(reaction.emoji))
'''