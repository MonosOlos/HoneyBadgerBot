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

        challenge_details = await create_challenge_message(ctx, self.bot, challenger, challenge["timeout"], challenge["type"], recipient)
        # challenge_details[reaction].emoji
        # challenge_details[message]

        if challenge["type"] in ["open", "timed"]:
            recipient = {}
            recipient["base"] = challenge_details["reaction"][1]
            recipient["id"] = recipient["base"].id
            recipient["name"] = recipient["base"].display_name
            recipient["mention"] = recipient["base"].mention

        if str(challenge_details["reaction"][0].emoji) == '🚫' and challenge_details["reaction"][1].id == challenger["id"]: # Allow challenge to be cancelled by the same person.
            await ctx.send(f"Challenge cancelled by {challenger['name']}")
            return

        # TODO: How do I stick this in a function???
        if challenger["id"] == recipient["id"]: # Deny challenging yourself.
            await ctx.send("You can't challenge yourself!")
            return

        challenger["pk"] = get_player_key(cfg, challenger['id'])
        recipient["pk"] = get_player_key(cfg, recipient["id"])

        invalid_player = None
        if challenger["pk"] == False:
            invalid_player = challenger
        elif recipient["pk"] == False:
            invalid_player = recipient

        if invalid_player is not None:
            await ctx.send(f"""
            Could not find {invalid_player["name"]}'s Discord ID on the system. Ask MCauthon if you need help. 
            Most likely, {invalid_player["name"]} needs to go to https://www.honeybadgersc2mod.com/user_home/, register/log-in, and update their Discord ID, as below:
            Discord ID: {invalid_player["id"]}
            Server PK (for debugging): {invalid_player["pk"]}
            """)

        if str(challenge_details["reaction"]) == "🚫":
            await ctx.send("Match declined.")
            return
        # Making the match and checking for winner

        match_details = make_match(cfg, player1_pk=challenger["pk"], player2_pk=recipient["pk"]) # Returns dict with match details

        match_response = add_match(cfg, match_details) # Adds the match to the system
        match_pk = match_response["pk"]

        matchup_rate_p1 = round(get_matchup_rate(cfg, challenger["pk"], recipient["pk"]).json()["expected_score_challenger"] * 100)
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
            reaction = await self.bot.wait_for("reaction_add", timeout=86400, check = check_match_winner) # 86400 = 24 hours

        except asyncio.TimeoutError:
            await ctx.send(f"Hi {challenger['mention']}, you challenged {recipient['mention']}, but they chickened out (did not accept in time).")
            return

        emoji_reaction = reaction[0]

        if str(emoji_reaction) == "1️⃣": # Challenger
            update = update_result(cfg, match_pk, challenger["pk"])
            winner_name = challenger['name']
        elif str(emoji_reaction) == "2️⃣": # Recipient
            update = update_result(cfg, match_pk, recipient["pk"])
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

