import string
import random
from discord.ext import commands


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(name="ga")
    async def guild_add(self, ctx: commands.Context):
        try:
            role = await ctx.guild.create_role(name="Referee")
            await ctx.send(f"Created role {role.mention}")

        except Exception as e:
            print(e)
            await ctx.send("I don't have permission to create roles.")
            return

        try:
            chars = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
            url = "".join(random.choice(chars) for _ in range(12))
            tournament = self.bot.challenge.tournaments.create(
                name=f"{ctx.guild.name} Tournament",
                url=url,
                tournament_type="single elimination",
            )
            setting = self.bot.mongo.Settings(
                guild_id=ctx.guild.id,
                referee_role_id=role.id,
                tournament_id=tournament["id"],
                tournament_url=tournament["url"],
            )

            await setting.commit()

        except Exception as e:
            print(e)
            return

        await ctx.send("Guild added to the database.")


async def setup(bot):
    await bot.add_cog(Owner(bot))
