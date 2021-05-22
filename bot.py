import os
import json

import discord
from discord.ext import commands
import asyncio

from Libraries.maps import *
from Libraries.matches import *
from Libraries.bot_config import get_config
cfg = get_config()

testing = True
if testing == True:
    bot = commands.Bot(command_prefix='£')
else:
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
    if len(content.split()) == 1 and "challenge" in content: # ?challenge
        challenge_type = "open"
        my_timeout = 86400
    elif len(content.split()) == 2 and content.split()[1].isnumeric():
        challenge_type = "timed"
        my_timeout = int(content.split()[1])
    elif (len(content.split()) == 2 and "<@" in content): # ?challenge @MCauthon
        challenge_type = "direct"
    else:
        await ctx.send("Invalid Challenge. Usage:\n**?challenge, ?challenge [time in minutes], ?challenge @username**")
        return

    print(f"Challenge type: {challenge_type}")

    challenger = {}
    challenger["base"] = ctx.message.author
    challenger["id"] = challenger["base"].id
    challenger["name"] = challenger["base"].display_name
    challenger["mention"] = challenger["base"].mention


    # If timeout or open challenge, need to wait for recipient reaction
    if challenge_type in ["open", "timed"]:

        challenge_message = await ctx.send(
        f"""
        **{challenger['name']} has created an open challenge!**
        This challenge will expire in {my_timeout//60} minutes
        --- React with ---
        👍 to **accept**
        """)

    recipient = {}
    recipient["base"] = ctx.message.mentions[0]
    recipient["id"] = recipient["base"].id
    recipient["name"] = recipient["base"].display_name
    recipient["mention"] = recipient["base"].mention    

    if challenger['id'] == recipient["id"]:
        await ctx.send("You can't challenge yourself! Usage:\n**!challenge @username**")
        return

    challenger_pk = get_player_key(cfg, challenger['id'])
    recipient_pk = get_player_key(cfg, recipient["id"])

    challenge_message = await ctx.send(
        f"""
    **{challenger['name']} is challenging {recipient['name']}!**
    --- {recipient['name']} react with ---
    👍 to **accept**
    🚫 to **decline**
    """)

    invalid_player = None
    if challenger_pk == False:
        invalid_player = challenger
    elif recipient_pk == False:
        invalid_player = recipient

    if invalid_player is not None:
        await ctx.send(f"""
        Could not find {invalid_player["name"]}'s Discord ID on the system. Ask {reporter} if you need help. 
        Most likely, {invalid_player["name"]} needs to go to https://www.honeybadgersc2mod.com/user_home/, register/log-in, and update their Discord ID, as below:
        Discord ID: {invalid_player["id"]}
        Server PK (for debugging): {invalid_player["pk"]}
        """)

    # Check for response
    def check_accept_challenge(reaction, user): # User is the person who reacted
        my_check = (
            user.id == recipient["id"] and (str(reaction.emoji) in ['👍', '🚫'])
            )
        return my_check

    try:
        await challenge_message.add_reaction('👍'); await challenge_message.add_reaction('🚫')
        reaction = await bot.wait_for("reaction_add", timeout=86400, check = check_accept_challenge) # 86400 = 24 hours

    except asyncio.TimeoutError:
        await ctx.send(f"Hi {challenger['mention']}, you challenged {recipient['mention']}, but they chickened out (did not accept in time).")
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
    {challenger['mention']} [{matchup_rate_p1}%] vs {recipient['mention']} [{matchup_rate_p2}%] on {match_details['map_name']}
    --- React to this message with ---
    1️⃣ if **{challenger['name']}** won
    2️⃣ if **{recipient['name']}** won
    🚫 to cancel the match.
    """)

    def check_match_winner(reaction, user):
        my_check = (
            str(reaction.emoji) in ["1️⃣", "2️⃣", "🚫"] and 
            user.id in [recipient["id"], challenger['id']]
        )
        return my_check

    try:
        await match_message.add_reaction("1️⃣"); await match_message.add_reaction("2️⃣"); await match_message.add_reaction("🚫")
        reaction = await bot.wait_for("reaction_add", timeout=my_timeout, check = check_match_winner) # 86400 = 24 hours

    except asyncio.TimeoutError:
        await ctx.send(f"Hi {challenger['mention']}, you challenged {recipient['mention']}, but they chickened out (did not accept in time).")
        return

    emoji_reaction = reaction[0]

    if str(emoji_reaction) == "1️⃣": # Challenger
        update = update_result(cfg, match_pk, challenger_pk)
        winner_name = challenger['name']
    elif str(emoji_reaction) == "2️⃣": # Recipient
        update = update_result(cfg, match_pk, recipient_pk)
        winner_name = recipient['name']
    elif str(emoji_reaction) == "🚫": # Cancel
        update = False

    # DELETE THE MATCH
    if update == False: 
        update = delete_match(cfg, match_pk)
        if str(update) == "202":
            await ctx.send(f"Match between {challenger['name']} and {recipient['name']} on {match_details['map_name']} has been cancelled.")
            return
        else:
            await ctx.send(f"**Error updating the match.** Tell {reporter} to fix this.")
        return

    if str(update) == "202":
        await ctx.send(f"Match between {challenger['name']} and {recipient['name']} has been updated. {winner_name} has won.")
        return
    else:
        await ctx.send(f"**Error updating the match.** Tell {reporter} to fix this.")

    print("hello")


bot.run(cfg["DISCORD_TOKEN"])
