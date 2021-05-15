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
reporter = "<@!507367765884272641>" # MCauthon


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
@bot.command(help="Sends a challenge. If accepted, creates a match tracked on https://www.honeybadgersc2mod.com/")
async def challenge(ctx):
    content = str(ctx.message.content)
    if not (len(content.split()) == 2 and "<@" in content):
        await ctx.send("Invalid Challenge. Usage:\n**?challenge @username**")
        return

    challenger_id = ctx.message.author.id
    challenger_nick = ctx.message.author.display_name
    challenger_mention = ctx.message.author.mention

    recipient_id = ctx.message.mentions[0].id
    recipient_nick = ctx.message.mentions[0].display_name
    recipient_mention = ctx.message.mentions[0].mention

    # if challenger_id == recipient_id:
    #     await ctx.send("You can't challenge yourself! Usage:\n**!challenge @username**")
    #     return

    challenger_pk = get_player_key(cfg, challenger_id)
    recipient_pk = get_player_key(cfg, recipient_id)

    challenge_message = await ctx.send(
        f"""
**{challenger_nick} is challenging {recipient_nick}!**
--- {recipient_nick} react with ---
👍 to **accept**
🚫 to **decline**
    """)

    if recipient_pk == False:
        await ctx.send(f"""
        Could not find recipient on the system. {reporter} please fix.
        {recipient_nick} 
        ID: {recipient_id}, PK: {recipient_pk}
        """)
        return

    # Check for response
    def check_accept_challenge(reaction, user): # User is the person who reacted
        my_check = (
            user.id == recipient_id and (str(reaction.emoji) in ['👍', '🚫'])
            )
        return my_check

    try:
        await challenge_message.add_reaction('👍'); await challenge_message.add_reaction('🚫')
        reaction = await bot.wait_for("reaction_add", timeout=86400, check = check_accept_challenge) # 86400 = 24 hours

    except asyncio.TimeoutError:
        await ctx.send(f"Hi {challenger_mention}, you challenged {recipient_mention}, but they chickened out (did not accept in time).")
        return

    emoji_reaction = reaction[0]
    if str(emoji_reaction) == "🚫":
        await ctx.send("Match declined.")
        return
    # Making the match and checking for winner

    match_details = make_match(cfg, player1_pk=challenger_pk, player2_pk=recipient_pk) # Returns dict with match details

    match_response = add_match(cfg, match_details) # Adds the match to the system
    match_pk = match_response["pk"]

    matchup_rate_p1 = round(get_matchup_rate(cfg, challenger_pk, recipient_pk).json()["expected_score_challenger"] * 100)
    matchup_rate_p2 = (100 - matchup_rate_p1)

    match_message = await ctx.send(f"""
**MATCH CREATED:** 
{challenger_mention} [{matchup_rate_p1}%] vs {recipient_mention} [{matchup_rate_p2}%] on {match_details['map_name']}
--- React to this message with ---
1️⃣ if **{challenger_nick}** won
2️⃣ if **{recipient_nick}** won
🚫 to cancel the match.
    """)

    def check_match_winner(reaction, user):
        my_check = (
            str(reaction.emoji) in ["1️⃣", "2️⃣", "🚫"] and 
            user.id in [recipient_id, challenger_id]
        )
        return my_check

    try:
        await match_message.add_reaction("1️⃣"); await match_message.add_reaction("2️⃣"); await match_message.add_reaction("🚫")
        reaction = await bot.wait_for("reaction_add", timeout=86400, check = check_match_winner) # 86400 = 24 hours

    except asyncio.TimeoutError:
        await ctx.send(f"Hi {challenger_mention}, you challenged {recipient_mention}, but they chickened out (did not accept in time).")
        return

    emoji_reaction = reaction[0]

    if str(emoji_reaction) == "1️⃣": # Challenger
        update = update_result(cfg, match_pk, challenger_pk)
        winner_name = challenger_nick
    elif str(emoji_reaction) == "2️⃣": # Recipient
        update = update_result(cfg, match_pk, recipient_pk)
        winner_name = recipient_nick
    elif str(emoji_reaction) == "🚫": # Cancel
        update = False

    # DELETE THE MATCH
    if update == False: 
        update = delete_match(cfg, match_pk)
        if str(update) == "202":
            await ctx.send(f"Match between {challenger_nick} and {recipient_nick} on {match_details['map_name']} has been cancelled.")
            return
        else:
            await ctx.send(f"**Error updating the match.** Tell {reporter} to fix this.")
        return

    if str(update) == "202":
        await ctx.send(f"Match between {challenger_nick} and {recipient_nick} has been updated. {winner_name} has won.")
        return
    else:
        await ctx.send(f"**Error updating the match.** Tell {reporter} to fix this.")

bot.run(cfg["DISCORD_TOKEN"])