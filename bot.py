import os, random, discord, json
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from asyncio import sleep

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
client = commands.Bot(command_prefix='-')
audioText = json.load(open('audio.json'))

@client.event
async def on_ready():
    activity = discord.Game(name="Counter-Strike: Global Offensive", type=3)
    await client.change_presence(activity=activity)
    print('Success!')

@client.command()
async def hello(ctx):
    #https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py
    audio, text = random.choice(list(audioText.items()))
    if ctx.author.voice and ctx.author.voice.channel:
        authorChannel = ctx.author.voice.channel
        print(ctx.voice_client.channel)
        if ctx.voice_client is None:
            await authorChannel.connect()
        elif ctx.voice_client.channel != authorChannel:
            await ctx.voice_client.disconnect()
            await authorChannel.connect()
        ctx.voice_client.play(discord.FFmpegPCMAudio(executable=r"ffmpeg.exe", source=f"audio/{audio}.wav"))
        await ctx.send(text)
    else:
        await ctx.send("You are not connected to a voice channel.")

client.run(token)