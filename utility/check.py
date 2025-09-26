from discord.ext import commands


class NotReferee(commands.CheckFailure):
    pass


def is_referee():
    async def predicate(ctx):
        # Fetch guild settings from Mongo
        data = await ctx.bot.mongo.Settings.find_one({"guild_id": ctx.guild.id})
        if data is None:
            raise NotReferee("Guild settings not found.")

        referee_role_id = data.referee_role_id
        if referee_role_id == 0:
            raise NotReferee("No referee role has been set for this server.")

        # Check if the author has the referee role
        if not any(role.id == referee_role_id for role in ctx.author.roles):
            raise NotReferee("You are not a referee.")

        return True

    return commands.check(predicate)
