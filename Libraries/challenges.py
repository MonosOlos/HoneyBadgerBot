import discord
from discord.ext import commands
import asyncio

from Libraries.matches import *
from Libraries.maps import *
from Libraries.bot_config import get_config

async def parse_challenge(ctx, content):
    challenge_type = None
    my_timeout = 24 * 60 * 60 # 24 hours

    if len(content.split()) == 1 and "challenge" in content: # ?challenge
        challenge_type = "open"
    elif len(content.split()) == 2 and content.split()[1].isnumeric():
        challenge_type = "timed"
        my_timeout = int(content.split()[1]) * 60 # Convert to minutes
    elif (len(content.split()) == 2 and "<@" in content): # ?challenge @MCauthon
        challenge_type = "direct"
    else:
        await ctx.send("**Invalid Challenge.** Usage:\n?challenge / ?challenge [time in minutes] / ?challenge @username")
        return

    challenge = {
        "type" : challenge_type,
        "timeout" : my_timeout
    }
    return challenge


async def create_challenge_message(ctx, bot, challenger, timeout, challenge_type, recipient=None):

    if challenge_type in ["open", "timed"]:
        looking_for_match = "<@&802635905709768704>"

        challenge_message = await ctx.send(f"""
        **{challenger['name']} has created an open challenge!**
        This challenge will expire in {timeout//60} minutes <<looking_for_match>>
        --- React with ---
        👍 to **accept**
        🚫 to **cancel** ({challenger['name']} only)
        """)

    if challenge_type == "direct":

        assert recipient != None

        challenge_message = await ctx.send(f"""
        **{challenger['name']} is challenging {recipient['name']}!**
        --- {recipient['name']} react with ---
        👍 to **accept**
        🚫 to **decline**
        """)

    # Check for response
    def check_accept_challenge(reaction, user, challenge_type=challenge_type): # User is the person who reacted
        assert challenge_type in ["open", "timed", "direct"]

        if challenge_type in ["open", "timed"]:
            my_check = (
                (user.id != challenger["id"] and str(reaction.emoji) == '👍' and user != bot.user) or # So that user can't accept own challenge
                (user.id == challenger["id"] and str(reaction.emoji) == '🚫')
                )
        if challenge_type == "direct":
            my_check = (
                user.id == recipient["id"] and (str(reaction.emoji) in ['👍', '🚫']) # Ensures only recipient can accept
                )
        return my_check

    try:
        await challenge_message.add_reaction('👍'); await challenge_message.add_reaction('🚫')
        reaction = await bot.wait_for("reaction_add", timeout=timeout, check = check_accept_challenge) # 86400 = 24 hours

    except asyncio.TimeoutError:
        if recipient == None:
            await ctx.send(f"Challenge by {challenger['mention']} has expired.")
        else:
            await ctx.send(f"Hi {challenger['mention']}, you challenged {recipient['mention']}, but they chickened out (did not accept in time).")
    
    return {
        "message" : challenge_message,
        "reaction": reaction
    }

