import os
import discord
from discord.ext.commands import Bot
from discord_slash import SlashCommand
import logging

# dotenv setup
from dotenv import load_dotenv
load_dotenv()
discordToken = os.getenv("TOKEN")

# Code for setting up logging
logging.basicConfig(level=logging.INFO)

# Intents setup
intents = discord.Intents.default()
intents.typing = False

# Initialize bot with intents
bot = Bot(command_prefix="!", help_command=None, self_bot=True, intents=intents)
slash = SlashCommand(bot, sync_commands=True)

@bot.event
async def on_ready():
    print('Logged in as {0} - {1}'.format(bot.user.name, bot.user.id))
    print('avalon-discord-bot loaded!')
    print('==================================')
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity())

bot.load_extension("avalon")

# Actually run the bot
bot.run(discordToken)
