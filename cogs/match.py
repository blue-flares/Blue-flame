import asyncio
import discord
from discord.ext import commands

from utility.check import is_referee


class Match(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @is_referee()
    @commands.command("init")
    async def init(self, ctx: commands.Context):
        """Initializes the match."""

        tournament_id = await self.bot.mongo.get_chal_id(ctx.guild.id)
        if not tournament_id:
            return await ctx.send("Tournament ID not set.")

        player_data = self.bot.mongo.Player.find({})

        async for player in player_data:
            try:
                chal_player = self.bot.challenge.participants.create(
                    tournament_id, player.name
                )
                player.challonge_id = chal_player["id"]
                await player.commit()
            except Exception as e:
                print(f"Error adding player {player.name}: {e}")

        self.bot.challenge.participants.randomize(tournament_id)
        self.bot.challenge.tournaments.start(tournament_id)

        # await ctx.send("Starting to create threads for the tournament now.")

        matches = self.bot.challenge.matches.index(tournament_id)

        for match in matches:
            player1 = await self.bot.mongo.Player.find_one(
                {"challonge_id": match["player1_id"]}
            )
            player2 = await self.bot.mongo.Player.find_one(
                {"challonge_id": match["player2_id"]}
            )

            match_doc = self.bot.mongo.Match(
                players=list(filter(lambda x: x is not None, [player1, player2])),
                challonge_match_id=match["id"],
            )

            await match_doc.commit()

        await ctx.send("Tournament started and players added.")

    @is_referee()
    @commands.command("list")
    async def list(self, ctx: commands.Context):
        """List all the members for the match."""
        settings = await self.bot.mongo.get_settings(ctx.guild.id)
        if not settings:
            return await ctx.send("Settings not found. Please set up the bot first.")

        players = self.bot.mongo.Player.find({})
        player_list = []
        async for player in players:
            player_list.append(player.name)

        await ctx.send(f"Registered players:\n ```\n{'\n'.join(player_list)}\n```")

    @is_referee()
    @commands.command("create")
    async def create(self, ctx: commands.Context):
        """Create a match thread."""

        settings = await self.bot.mongo.get_settings(ctx.guild.id)
        if not settings:
            return await ctx.send("Settings not found. Please set up the bot first.")

        matches = (
            await self.bot.Match.find(
                {
                    "players": {"$size": 2},  # exactly 2 players
                    "archieved": False,  # not archived
                    "thread_create": False,  # thread not created
                }
            ).to_list(None)  # fetch all results
        )

        await ctx.send(f"Creating threads and sending match links.")

        for matche in matches:
            player1, player2 = matche.players
            player1 = await player1.fetch()
            player2 = await player2.fetch()

            try:
                user1 = ctx.guild.get_member(player1.player_id)
                user2 = ctx.guild.get_member(player2.player_id)
            except Exception as e:
                return await ctx.send(f"Error fetching members: {e}")

            channel: discord.TextChannel = ctx.guild.get_channel(settings.match_id)

            if not channel:
                return await ctx.send("Match channel not found. Please check settings.")

            await channel.send(f"{user1.mention} vs {user2.mention}")

            thread: discord.Thread = await channel.create_thread(
                name=f"{player1.name}-vs-{player2.name}",
            )

            await thread.add_user(user1)
            await thread.add_user(user2)

            matche.thread_id = thread.id
            matche.thread_create = True
            await matche.commit()

            await thread.send(
                f"Match thread created for {user1.mention} and {user2.mention}.\n"
                f"Please report the match result here once completed."
            )

    async def log_result(self, guild: discord.Guild, user: discord.Member):
        setting = await self.bot.mongo.get_settings(guild.id)
        channel: discord.TextChannel = guild.get_channel(setting.result_id)

        await channel.send(f"{user.mention} has won their match!")

    @is_referee()
    @commands.command("score")
    async def score(self, ctx: commands.Context, winner: discord.Member | None = None):
        """Report match score."""

        if not winner:
            return await ctx.send("Please mention a user to log the win for.")

        match_data = await self.bot.mongo.Match.find_one({"thread_id": ctx.channel.id})

        if not match_data:
            return await ctx.send("This command can only be used in match threads.")

        players = []
        for p in match_data.players:
            p = await p.fetch()
            players.append(p)

        if winner.id not in [p.player_id for p in players]:
            return await ctx.send("The mentioned user is not part of this match.")

        winner_player = next(p for p in players if p.player_id == winner.id)

        self.bot.challenge.matches.update(
            await self.bot.mongo.get_chal_id(ctx.guild.id),
            match_data.challonge_match_id,
            winner_id=winner_player.challonge_id,
        )

        match_data.winner = winner_player
        match_data.archieved = True
        match_data.referee_id = ctx.author.id
        await match_data.commit()

        await self.log_result(ctx.guild, winner)

        await ctx.send(f"Match result logged. {winner.mention} is the winner!")
        await ctx.send("Archiving this thread in 10 seconds...")

        await asyncio.sleep(10)
        await ctx.channel.edit(archived=True)


async def setup(bot):
    await bot.add_cog(Match(bot))
