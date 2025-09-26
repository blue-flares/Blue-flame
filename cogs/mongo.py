from discord.ext import commands
from umongo import Document, fields
from umongo.frameworks import MotorAsyncIOInstance
from motor.motor_asyncio import AsyncIOMotorClient

import config


class Settings(Document):
    guild_id = fields.IntegerField(required=True, unique=True)

    # IDs Related Stuff
    category_id = fields.IntegerField(default=0)
    referee_role_id = fields.IntegerField(default=0)
    participant_role_id = fields.IntegerField(default=0)
    desc_id = fields.IntegerField(default=0)
    result_id = fields.IntegerField(default=0)
    match_id = fields.IntegerField(default=0)

    # Tournament Related Stuff
    tournament_name = fields.StringField(default="Black Flames")
    registration_status = fields.BooleanField(default=False)
    registration_channel_id = fields.IntegerField(default=0)
    registration_message_id = fields.IntegerField(default=0)
    max_players = fields.IntegerField(default=64)
    current_round = fields.IntegerField(default=-1)
    joined = fields.IntegerField(default=0)

    tournament_id = fields.IntegerField(required=True, unique=True)
    tournament_url = fields.StringField(required=True, unique=True)


class Player(Document):
    player_id = fields.IntegerField(
        required=True,
        unique=True,
    )
    name = fields.StringField(required=True)
    challonge_id = fields.IntegerField(required=False, unique=True)


class Match(Document):
    players = fields.ListField(fields.GenericReferenceField(), required=False)
    winner = fields.GenericReferenceField(required=False)
    thread_id = fields.IntegerField(required=False, unique=True)
    referee_id = fields.IntegerField(required=False)
    challonge_match_id = fields.IntegerField(required=True, unique=True)
    thread_create = fields.BooleanField(default=False)
    archieved = fields.BooleanField(default=False)


class Mongo(commands.Cog):
    """For database operations."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = AsyncIOMotorClient(config.MONGO_URI)
        self.db = self.client[config.DATABASE_NAME]
        instance = MotorAsyncIOInstance(self.db)

        g = globals()

        for x in (
            "Settings",
            "Player",
            "Match",
        ):
            setattr(self, x, instance.register(g[x]))
            getattr(self, x).bot = bot

    async def get_settings(self, guild_id: int):
        settings = await self.Settings.find_one({"guild_id": guild_id})
        if not settings:
            return None
        return settings

    async def get_chal_id(self, guild_id: int):
        settings = await self.Settings.find_one({"guild_id": guild_id})
        if not settings:
            return None
        return settings.tournament_id


async def setup(bot: commands.Bot):
    await bot.add_cog(Mongo(bot))
