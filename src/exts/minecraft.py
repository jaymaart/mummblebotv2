import datetime as dt
from typing import Optional

import disnake
from disnake.ext import commands
from mcrcon import MCRcon, MCRconException

from src import constants, log

logger = log.get_logger(__name__)


class MinecraftCog(commands.Cog):
    """Minecraft server management commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def create_server_embed(self) -> disnake.Embed:
        """Create a Discord embed with Minecraft server information."""
        description = (
            "Welcome to our Minecraft SMP server! Here's everything you need to get started.\n\n"
            "🌐 **Server Address:** `smp.mummbleberry.com`\n"
            "🖥️ **Version:** `1.21.8`\n\n"
            "🎤 **Voice Chat Mod(Optional)**\n"
            "- A couple players use voice chat mod, if you need help installing just @jaymart \n\n"
            "📋 Getting Access\n"
            "To gain access to the server, click the Whitelist Me button below!\n\n"
            "This will open a form where you can enter your Minecraft username to be added to the whitelist.\n\n"
            "Note: Make sure to enter your exact Minecraft username (case-sensitive)."
        )

        embed = disnake.Embed(
            title="Minecraft Server Information",
            description=description,
            color=constants.Color.GREEN,
            timestamp=dt.datetime.now(dt.timezone.utc)
        )

        return embed

    async def whitelist_user(self, username: str) -> tuple[bool, str]:
        """Whitelist a user on the Minecraft server via RCON.

        Parameters
        ----------
        username : str
            The Minecraft username to whitelist

        Returns
        -------
        tuple[bool, str]
            (success, message) - success indicates if the operation worked,
            message contains either success confirmation or error details
        """
        if not constants.Minecraft.rcon_password:
            return False, "RCON password not configured"

        try:
            with MCRcon(constants.Minecraft.rcon_host, constants.Minecraft.rcon_password, constants.Minecraft.rcon_port) as mcr:
                # Execute the whitelist add command
                response = mcr.command(f"whitelist add {username}")

                # Check if the command was successful
                if "Added" in response or "already whitelisted" in response:
                    return True, f"Successfully whitelisted {username}!"
                else:
                    return False, f"Failed to whitelist {username}. Response: {response}"

        except MCRconException as e:
            logger.error(f"RCON error whitelisting user {username}: {e}")
            return False, f"Failed to connect to server: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error whitelisting user {username}: {e}")
            return False, f"An unexpected error occurred: {str(e)}"

    @commands.has_guild_permissions(administrator=True)
    @commands.slash_command(
        name="minecraft",
        description="Get Minecraft server information and request whitelist access"
    )
    async def minecraft_info(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: Optional[disnake.TextChannel] = None
    ) -> None:
        """Send Minecraft server information to a specified channel or current channel.

        Parameters
        ----------
        inter : disnake.ApplicationCommandInteraction
            The interaction object
        channel : Optional[disnake.TextChannel]
            The channel to send the info to. If None, sends to current channel.
        """
        # Check permissions - only allow in appropriate channels or with manage_messages permission
        if channel and not inter.author.guild_permissions.manage_messages:
            await inter.response.send_message(
                "❌ You need `Manage Messages` permission to send to other channels.",
                ephemeral=True
            )
            return

        target_channel = channel or inter.channel

        # Create the embed and button
        embed = self.create_server_embed()
        button = disnake.ui.Button(
            label="Whitelist Me",
            style=disnake.ButtonStyle.primary,
            custom_id="minecraft_whitelist",
            emoji="📋"
        )

        view = disnake.ui.View()
        view.add_item(button)

        try:
            await target_channel.send(embed=embed, view=view)
            await inter.response.send_message(
                f"✅ Minecraft server information sent to {target_channel.mention}",
                ephemeral=True
            )
        except disnake.Forbidden:
            await inter.response.send_message(
                f"❌ I don't have permission to send messages in {target_channel.mention}",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error sending Minecraft info: {e}")
            await inter.response.send_message(
                "❌ An error occurred while sending the message.",
                ephemeral=True
            )

    @commands.Cog.listener("on_button_click")
    async def handle_whitelist_button(self, inter: disnake.MessageInteraction) -> None:
        """Handle the whitelist button click by opening a modal."""
        if inter.component.custom_id != "minecraft_whitelist":
            return

        # Create and send the modal for Minecraft username input
        modal = MinecraftUsernameModal()
        await inter.response.send_modal(modal)


class MinecraftUsernameModal(disnake.ui.Modal):
    """Modal for collecting Minecraft username."""

    def __init__(self) -> None:
        super().__init__(
            title="Enter Minecraft Username",
            custom_id="minecraft_username_modal",
            components=[
                disnake.ui.TextInput(
                    label="Minecraft Username",
                    placeholder="Enter your exact Minecraft username",
                    custom_id="minecraft_username",
                    style=disnake.TextInputStyle.short,
                    min_length=3,
                    max_length=16,
                    required=True,
                ),
            ],
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        """Handle the modal submission."""
        # Defer the response to give us time to process
        await inter.response.defer(ephemeral=True)

        # Get the entered Minecraft username
        minecraft_username = inter.text_values["minecraft_username"].strip()

        # Get the cog instance
        cog = inter.bot.get_cog("MinecraftCog")
        if not cog:
            await inter.edit_original_response(
                embed=disnake.Embed(
                    title="❌ Error",
                    description="Could not find Minecraft cog. Please try again later.",
                    color=constants.Color.RED,
                )
            )
            return

        # Attempt to whitelist the user
        success, message = await cog.whitelist_user(minecraft_username)

        if success:
            embed = disnake.Embed(
                title="✅ Successfully Whitelisted!",
                description=f"**{minecraft_username}** has been added to the Minecraft server whitelist!",
                color=constants.Color.GREEN,
                timestamp=dt.datetime.now(dt.timezone.utc)
            )
            embed.add_field(
                name="📝 Next Steps",
                value=(
                    f"1. Make sure you're using the username: **{minecraft_username}**\n"
                    "2. Launch Minecraft (voice chat modpack optional but recommended)\n"
                    "3. Connect to the server and enjoy!"
                ),
                inline=False
            )
        else:
            embed = disnake.Embed(
                title="❌ Whitelist Failed",
                description="There was an issue adding you to the whitelist.",
                color=constants.Color.RED,
                timestamp=dt.datetime.now(dt.timezone.utc)
            )
            embed.add_field(
                name="Error Details",
                value=message,
                inline=False
            )
            embed.add_field(
                name="📞 Need Help?",
                value="Contact a server administrator if this problem persists.",
                inline=False
            )

        try:
            await inter.edit_original_response(embed=embed)
        except Exception as e:
            logger.error(f"Error sending whitelist response: {e}")


def setup(bot: commands.Bot) -> None:
    """Load the MinecraftCog cog."""
    bot.add_cog(MinecraftCog(bot))
