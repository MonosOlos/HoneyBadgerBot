import discord
from discord.ext import commands
import asyncio

from Libraries.matches import *
from Libraries.maps import *
from Libraries.challenges import * 
from Libraries.bot_config import get_config


class ChallengeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command(help="Sends a challenge. If accepted, creates a match tracked on https://www.honeybadgersc2mod.com/")
    async def challenge(self, ctx):
        cfg = get_config()

        content = str(ctx.message.content)

        challenge = await parse_challenge(ctx, content) # {type=<str type>, timeout=<int timeout>}
        if not challenge:
            return

        challenger = {}
        challenger["base"] = ctx.message.author
        challenger["id"] = challenger["base"].id
        challenger["name"] = challenger["base"].display_name
        challenger["mention"] = challenger["base"].mention

        recipient = None
        if challenge["type"] == "direct":
            recipient = {}
            recipient["base"] = ctx.message.mentions[0]
            recipient["id"] = recipient["base"].id
            recipient["name"] = recipient["base"].display_name
            recipient["mention"] = recipient["base"].mention 

        challenge_reaction = await challenge_message(ctx, self.bot, challenger, challenge["timeout"], challenge["type"], recipient)

        if challenge["type"] != "direct":
            recipient = {}
            recipient["base"] = challenge_reaction[1]
            recipient["id"] = recipient["base"].id
            recipient["name"] = recipient["base"].name
            recipient["mention"] = recipient["base"].mention

        #print(f"challenger: {challenger['name']}\nrecipient: {recipient['name']}")

        challenger_pk = get_player_key(cfg, challenger['id'])
        recipient_pk = get_player_key(cfg, recipient["id"])

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

def setup(bot):
    bot.add_cog(ChallengeCog(bot))

