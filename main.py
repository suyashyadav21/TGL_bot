import discord
import os
import random
import asyncio
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View

load_dotenv()

# Intents 
intents = discord.Intents.default()
intents.messages = True
intents.reactions = True  # Not needed anymore for reactions, but still here for general use
bot = commands.Bot(command_prefix="$", intents=intents)

# Bot is ready
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"We have logged in as {bot.user}")

# Check if the user is an administrator
async def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

# Slash command: /ping (Admin only)
@bot.tree.command(name="ping", description="Responds with the bot's latency.")
async def slash_ping(interaction: discord.Interaction):
    if await is_admin(interaction):  # Check if the user is an admin
        latency = round(bot.latency * 1000)
        await interaction.response.send_message(f"🏓Pong! Latency: {latency}ms")
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

# Slash command: /embed 
@bot.tree.command(name="embed", description="Create an embed with a custom color, optional image, thumbnail, and footer.")
@app_commands.describe(
    title="The title of the embed",
    description="The description of the embed",
    color="The color for the embed in hex format (e.g., #FF5733)",
    footer="Optional footer text",
    image_url="Optional image or GIF URL to add to the bottom of the embed",
    thumbnail_url="Optional URL for a small image (thumbnail) in the top-right corner"
)
async def slash_embed(
    interaction: discord.Interaction, 
    title: str, 
    description: str, 
    color: str, 
    footer: str = None,  
    image_url: str = None,  
    thumbnail_url: str = None  
):
    if await is_admin(interaction):
        if not color.startswith("#") or len(color) != 7:
            await interaction.response.send_message("Please provide a valid hex color code (e.g., #FF5733).", ephemeral=True)
            return

        try:
            hex_color = int(color.lstrip("#"), 16)
            embed = discord.Embed(title=title, description=description, color=hex_color)

            if footer:
                embed.set_footer(text=footer)
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            if image_url:
                embed.set_image(url=image_url)

            await interaction.response.send_message(embed=embed)
        except ValueError:
            await interaction.response.send_message("Invalid color format. Please use a valid hex color (e.g., #FF5733).", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

# Custom view for the giveaway button
class GiveawayView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = set()  # Store participants in a set to avoid duplicates

    # Button for entering the giveaway
    @discord.ui.button(label="🎉", style=discord.ButtonStyle.green, custom_id="giveaway_button")
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the user has already entered
        if interaction.user in self.participants:
            await interaction.response.send_message("You are already entered in the giveaway!", ephemeral=True)
        else:
            self.participants.add(interaction.user)
            button.label = f"🎉({len(self.participants)})"
            await interaction.response.edit_message(view=self)
            await interaction.response.send_message("You've successfully entered the giveaway!", ephemeral=True)

# Slash command: /giveaway
@bot.tree.command(name="giveaway", description="Start a giveaway with duration, prize, and number of winners.")
@app_commands.describe(
    duration="Giveaway duration in seconds",
    prize="The prize to win",
    winners="Number of winners"
)
async def slash_giveaway(
    interaction: discord.Interaction, 
    duration: int, 
    prize: str, 
    winners: int
):
    if await is_admin(interaction):  # Check if the user is an admin
        # Create the giveaway embed
        embed = discord.Embed(
            title="🎉 **GIVEAWAY TIME!** 🎉",
            description=f"Prize: **{prize}**\nClick 🎉 button to enter!\nDuration: **{duration} seconds**\nNumber of Winners: **{winners}**",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Giveaway hosted by {interaction.user.display_name}")

        # Create the view (button) for the giveaway
        view = GiveawayView()

        # Send the giveaway message with the embed and button
        await interaction.response.send_message(embed=embed, view=view)

        # Wait for the giveaway duration
        await asyncio.sleep(duration)

        # Pick winners from participants
        participants = list(view.participants)
        if len(participants) < winners:
            winners = len(participants)

        # Select random winners
        chosen_winners = random.sample(participants, winners)

        # Announce the winners
        if chosen_winners:
            winner_mentions = ", ".join([winner.mention for winner in chosen_winners])
            await interaction.followup.send(f"🎉 Congratulations {winner_mentions}! You won the **{prize}**!")
        else:
            await interaction.followup.send("No one participated in the giveaway.")
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)



        


bot.run(os.getenv("TOKEN"))
