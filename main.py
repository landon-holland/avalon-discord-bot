import os
import discord
from discord.ext import commands
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
bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    print('Logged in as {0} - {1}'.format(bot.user.name, bot.user.id))
    print('avalon-discord-bot loaded!')
    print('==================================')
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity())

# install cog
#setup(bot)

# Actually run the bot
bot.run(discordToken)