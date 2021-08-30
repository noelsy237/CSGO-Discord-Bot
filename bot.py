import os, random, discord, json
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio

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
    audio, text = random.choice(list(audioText.items()))
    if ctx.message.author.voice:
        channel = ctx.message.author.voice.channel
        voice = get(client.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        voice.play(discord.FFmpegPCMAudio(executable=r"ffmpeg.exe", source=f"audio/{audio}.wav"))
        await ctx.send(text)

    else:
        await ctx.send("You are not connected to a voice channel.")
        return

client.run(token)