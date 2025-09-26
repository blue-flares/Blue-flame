import challonge
import discord
from discord.ext import commands

import config
import asyncio

cog_extension = [
    "jishaku",
    "cogs.error",
    "cogs.match",
    "cogs.mongo",
    "cogs.referee",
    "cogs.owner",
]


class BlueFlare(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("bf", "BF", "Bf", "bF", "!"),
            intents=discord.Intents.all(),
            strip_after_prefix=True,
            owner_ids={724447396066754643},
            case_insensitive=False,
            self_bot=False,
            allowed_mentions=discord.AllowedMentions(
                roles=False, everyone=False, users=True
            ),
        )

    async def on_ready(self):
        print(
            f"Logged in {self.user.name} (ID {self.user.id})\nVersion {discord.__version__}"
        )

    async def setup_hook(self):
        self.lcog = cog_extension

        challonge.set_credentials(config.CHALLONGE_USERNAME, config.CHALLONGE_API_KEY)
        for cog in cog_extension:
            # await self.load_extension(cog)
            try:
                await self.load_extension(cog)
            except Exception as e:
                print(e)
                print(f"Failed to load extension: {cog}")

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        if message.content == f"<@{self.user.id}>":
            embed = discord.Embed(
                title="BlackFlames Bot",
                description=f"Prefixes : <@{self.user.id}>, bf\n Developer : <@724447396066754643>",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow(),
            )
            await message.channel.send(embed=embed)
        await self.process_commands(message)

    async def on_message_edit(self, before, after):
        if after.author.id in self.owner_ids:
            await self.process_commands(after)
        else:
            return

    async def start(self):
        await super().start(config.TOKEN, reconnect=True)

    async def close(self):
        await super().close()
        await self.session.close()

    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner

    @property
    def mongo(self):
        return self.get_cog("Mongo")

    @property
    def challenge(self):
        return challonge


bot = BlueFlare()

asyncio.run(bot.start())
