import discord
from discord.ext import commands

from utility import check


class Referee(commands.Cog):
    """For Referee related commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        settings = self.bot.mongo.Settings.find({})
        async for setting in settings:
            if setting.registration_status:
                self.bot.add_view(self.PersistentView())

    class PersistentView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)  # Persistent

        class SecondView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)  # 3 minutes

            @discord.ui.button(
                label="Leave", style=discord.ButtonStyle.red, custom_id="leave_button"
            )
            async def second_button(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                try:
                    user = await interaction.client.mongo.Player.find_one(
                        {"player_id": interaction.user.id}
                    )

                    if not user:
                        return
                    await user.delete()
                    settings = await interaction.client.mongo.Settings.find_one(
                        {"guild_id": interaction.guild.id}
                    )
                    settings.joined -= 1
                    await settings.commit()

                except Exception as e:
                    print(e)
                    return

                try:
                    role = interaction.guild.get_role(settings.participant_role_id)
                    if role:
                        await interaction.user.remove_roles(
                            role, reason="Left the tournament"
                        )
                except Exception as e:
                    print(e)

                await interaction.response.send_message(
                    "You have left the tournament.", ephemeral=True
                )

        @discord.ui.button(
            label="Register",
            style=discord.ButtonStyle.green,
            custom_id="register_button",
        )
        async def click_me(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            user_data = await interaction.client.mongo.Player.find_one(
                {"player_id": interaction.user.id}
            )
            if user_data:
                return await interaction.response.send_message(
                    "You are already registered. Do you want to leave.",
                    view=self.SecondView(),
                    ephemeral=True,
                )

            settings = await interaction.client.mongo.Settings.find_one(
                {"guild_id": interaction.guild.id}
            )
            if settings.joined >= settings.max_players:
                return await interaction.response.send_message(
                    "Registration is full.", ephemeral=True
                )
            settings.joined += 1
            await settings.commit()

            try:
                new_user = interaction.client.mongo.Player(
                    player_id=interaction.user.id,
                    name=interaction.user.name,
                )
                await new_user.commit()
            except Exception as e:
                print(e)

            try:
                role = interaction.guild.get_role(settings.participant_role_id)
                if role:
                    await interaction.user.add_roles(
                        role, reason="Joined the tournament"
                    )

            except Exception as e:
                print(e)

            await interaction.response.send_message(
                "You have joined the tournament.", ephemeral=True
            )

    @check.is_referee()
    @commands.command(name="setup")
    async def setup(self, ctx: commands.Context):
        """Starts the tournament."""

        settings = await self.bot.mongo.Settings.find_one({"guild_id": ctx.guild.id})
        if not settings:
            return await ctx.send(
                "Settings not found. Please run the setup command first."
            )

        if settings.participant_role_id or settings.category_id:
            return await ctx.send("Setup has already been completed.")

        message = await ctx.send("Creating the Role...")
        role = await ctx.guild.create_role(
            name="Participant",
            mentionable=True,
            reason="Role for tournament participants",
            color=discord.Color.blue(),
        )
        await message.edit(content=f"Role created: {role.name}")

        referee_role = ctx.guild.get_role(settings.referee_role_id)
        if referee_role is None:
            return await ctx.send("Referee role not found. Please set it up first.")

        message = await ctx.send("Creating the Category...")

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(view_channel=True),
            referee_role: discord.PermissionOverwrite(view_channel=True),
            ctx.guild.me: discord.PermissionOverwrite(view_channel=True),
        }
        category = await ctx.guild.create_category(
            name="Tournament",
            overwrites=overwrites,
            reason="Category for tournament channels",
        )
        await message.edit(content=f"Category created: {category.name}")

        await ctx.send("Creating respective channels...")
        discussion = await category.create_text_channel(name="discussion")
        results = await category.create_text_channel(name="results")
        matchups = await category.create_text_channel(name="matchups")
        await ctx.send(
            "Channels created: "
            + f"{discussion.mention}, {results.mention}, {matchups.mention}"
        )

        settings.participant_role_id = role.id
        settings.category_id = category.id
        settings.desc_id = discussion.id
        settings.result_id = results.id
        settings.match_id = matchups.id

        await settings.commit()

        await ctx.send("Setup completed.")

    @check.is_referee()
    @commands.command(name="start")
    async def start(self, ctx: commands.Context):
        """Sends the message"""

        settings = await self.bot.mongo.Settings.find_one({"guild_id": ctx.guild.id})
        if not settings:
            return await ctx.send(
                "Settings not found. Please run the setup command first."
            )

        if settings.registration_status:
            return await ctx.send("Registration is already open.")
        settings.registration_status = True

        message: discord.Message = await ctx.send(
            "Registration is now open!", view=self.PersistentView()
        )

        settings.registration_channel_id = ctx.channel.id
        settings.registration_message_id = message.id
        await settings.commit()

    @check.is_referee()
    @commands.command(name="end")
    async def end(self, ctx: commands.Context):
        """Ends the registration."""

        settings = await self.bot.mongo.get_settings(ctx.guild.id)

        if (settings is not None) and (settings.registration_status != False):
            channel: discord.TextChannel = ctx.guild.get_channel(
                settings.registration_channel_id
            )
            if not channel:
                return print("No channel Found.")
            message: discord.Message = channel.fetch_message(
                settings.registration_message_id
            )

            if not message:
                return print("No Message Found.")

            await message.edit(
                content="Registration have now been closed.",
                embed=message.embeds,
                view=None,
            )

            await ctx.send("Registration have been closed.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Referee(bot))
