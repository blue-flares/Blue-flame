import discord
from discord.ext import commands

import traceback
import sys


class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Couldn't find the member specified.")

        elif isinstance(error, commands.BadArgument):
            await ctx.send("Couldn't convert the specified argument.")

        elif isinstance(error, commands.CheckFailure):
            e = discord.Embed(
                title="Error Occured", description=f"{error}", color=discord.Color.red()
            )
            await ctx.send(embed=e)

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("Missing Permission!")
        else:
            print(
                "Ignoring exception in command {}:".format(ctx.command), file=sys.stderr
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )
            e = discord.Embed(
                title="Error Occured",
                # description = f'Command: \n```\n{ctx.command}```',
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            )
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            n_err = "".join(lines)
            e.description = n_err

            await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Error(bot))
