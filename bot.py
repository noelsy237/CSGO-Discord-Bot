import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import random

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client = commands.Bot(command_prefix='-')


@client.event
async def on_ready():
    activity = discord.Game(name="Counter-Strike: Global Offensive", type=3)
    await client.change_presence(activity=activity)
    print('Success!')


@client.command()
async def hello(ctx):
    chats = ["The last time I was this happy, I was told I could stop paying alimony.",
             "You're alive! I've never been more happy to lose fifty quid.",
             "You deserve a promotion! Well, our fundings all tied up so I can't afford to give you one but on paper, "
             "wooo, you've earned it."]
    await ctx.send(random.choice(chats))

client.run(token)