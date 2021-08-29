import os, random, discord, asyncio
from dotenv import load_dotenv
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord.utils import get


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

@client.command()
async def audio(ctx):
    channel = ctx.message.author.voice.channel
    if not channel:
        await ctx.send("You are not connected to a voice channel")
        return
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
    voice.play(discord.FFmpegPCMAudio(executable=r"ffmpeg.exe", source="audio/aw_hell.mp3"))

client.run(token)