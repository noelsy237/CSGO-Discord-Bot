import os, random, discord, json
from dotenv import load_dotenv
from discord.ext import commands
from discord import FFmpegPCMAudio

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='-')
audioText = json.load(open('audio.json'))
bot.remove_command('help')

@bot.event
async def on_ready():
    activity = discord.Game(name="Counter-Strike: Global Offensive", type=3)
    await bot.change_presence(activity=activity)
    print('Success!')


@bot.command()
async def help(ctx):
    await ctx.send("Hello operator! You can say hi to me by typing '-hi' followed by any of the following options```felix, legacy, hostage\n\nExample: -hi felix```")

@bot.command()
async def hi(ctx, type):
    #https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py
    if ctx.author.voice and ctx.author.voice.channel:
        await ctx.message.delete()
        authorChannel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await authorChannel.connect()
        elif ctx.voice_client.channel != authorChannel:
            await ctx.voice_client.disconnect()
            await authorChannel.connect()
        if type is None or type == "felix":
            audio, text = random.choice(list(audioText['felix'][0].items()))
        elif type == "hostage":
            audio, text = random.choice(list(audioText['hostage'][0].items()))
        elif type == "legacy":
            audio, text = random.choice(list(audioText['legacy'][0].items()))
        ctx.voice_client.play(discord.FFmpegPCMAudio(source=f"audio/{audio}.wav"))
        await ctx.send(text)
    else:
        await ctx.send("You are not connected to a voice channel.")

bot.run(token)