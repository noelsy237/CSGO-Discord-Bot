import os, random, discord, json
from dotenv import load_dotenv
from discord.ext import commands
from discord import FFmpegPCMAudio

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='-')
audioText = json.load(open('audio.json'))
discord.opus.load_opus()

@bot.event
async def on_ready():
    activity = discord.Game(name="Counter-Strike: Global Offensive", type=3)
    await bot.change_presence(activity=activity)
    print('Success!')

@bot.command()
async def hello(ctx):
    #https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py
    await ctx.message.delete()
    audio, text = random.choice(list(audioText.items()))
    if ctx.author.voice and ctx.author.voice.channel:
        authorChannel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await authorChannel.connect()
        elif ctx.voice_client.channel != authorChannel:
            await ctx.voice_client.disconnect()
            await authorChannel.connect()
        ctx.voice_client.play(discord.FFmpegPCMAudio(source=f"audio/{audio}.wav"))
        await ctx.send(text)
    else:
        await ctx.send("You are not connected to a voice channel.")

bot.run(token)