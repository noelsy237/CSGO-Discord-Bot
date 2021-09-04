import os, random, discord, json, requests, sqlite3, datetime
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
from asyncio import sleep
from steam.steamid import SteamID

load_dotenv()
discordToken = os.getenv('DISCORD_TOKEN')
steamToken = os.getenv('STEAM_TOKEN')
vacChannelId = int(os.getenv('VAC_CHANNEL_ID'))
bot = commands.Bot(command_prefix='-')
db = sqlite3.connect('csgobot.sqlite')
audioText = json.load(open('audio.json'))
bot.remove_command('help')

@bot.event
async def on_ready():
    activity = discord.Game(name="Counter-Strike: Global Offensive", type=3)
    await bot.change_presence(activity=activity)
    print('Bot started successfully')


@bot.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
        return 
    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()


@bot.command()
async def help(ctx):
    await ctx.send("Hello operator! You can say hi to me by typing '-hi' followed by any of the following options`felix, legacy, hostage\n\nExample: -hi felix`")
    await ctx.send("You can also add suspected cheaters to a tracking list by `-vac community_url`. The bot will send a message if they get banned")


@bot.command()
async def hi(ctx, type=None):
    #https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py
    if ctx.author.voice and ctx.author.voice.channel:
        await ctx.message.delete()
        authorChannel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await authorChannel.connect()
        elif ctx.voice_client.channel != authorChannel:
            await ctx.voice_client.disconnect()
            await authorChannel.connect()
        if type == "felix" or type == None:
            audio, text = random.choice(list(audioText['felix'][0].items()))
        elif type == "hostage":
            audio, text = random.choice(list(audioText['hostage'][0].items()))
        elif type == "legacy":
            audio, text = random.choice(list(audioText['legacy'][0].items()))
        ctx.voice_client.play(discord.FFmpegPCMAudio(source=f"audio/{audio}.wav"))
        await ctx.send(text)
    else:
        await ctx.send("You are not connected to a voice channel.")


@bot.command()
async def vac(ctx, input=None):
    error = None
    if input:
        input.strip()
        userId = int(SteamID.from_url(input))
        player = SteamID(userId)
        if not player.is_valid():
            error = "User was not found. You must supply a community profile URL."
        elif db.execute('SELECT EXISTS(SELECT 1 FROM players WHERE steamID = ?)', (userId,)).fetchone()[0]:
            error = "User has already been added."
    
        if error is None:
            cur = db.cursor()
            print(ctx.author.id)
            cur.execute('INSERT INTO players (steamID, author, addedDate, notified) VALUES (?, ?, ?, ?)', (userId, str(ctx.author.id), datetime.datetime.now(), 0))
            db.commit()
            await ctx.message.delete() 
            await ctx.send(f"Player with ID {userId} added to tracking list.")
            await called_once_a_day_vac(userId)
        else:
            await ctx.send(error)
    else:
        await ctx.send("You must supply a community profile URL.")


@tasks.loop(hours=24)
async def called_once_a_day_vac(userId=None):
    channel = bot.get_channel(vacChannelId)
    msg = None
    playersDict = {}
    cur = db.cursor()
    if userId is None:
        playersDB = cur.execute('SELECT steamID, author, datetime(addedDate) FROM players WHERE notified = 0').fetchall()
        for row in playersDB:
            steamdID, author, addedDate = row
            conv_date = datetime.datetime.strptime(addedDate, "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")
            playersDict[steamdID] = [author, conv_date]
    else:
        playersDB = cur.execute('SELECT author, datetime(addedDate) FROM players WHERE steamID = ?', (userId,)).fetchone()
        playersDict[userId] = (playersDB[0], datetime.datetime.strptime(playersDB[1], "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y"))

    for playerId, values in playersDict.items():
        player = json.loads(requests.get(f'http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={steamToken}&steamids={playerId}').text)['players'][0]
        banField = None
        vacBan = player['VACBanned']
        vacAmount = player['NumberOfVACBans']
        gameAmount = player['NumberOfGameBans']
        banDay = player['DaysSinceLastBan']
        banProfile = f"https://steamcommunity.com/profiles/{playerId}"
        if vacBan:
            banField = "VAC"
        elif gameAmount > 0:
            banField = "Game"
        if banField:
            playerEmbed = discord.Embed(title = "Ban Detected", colour = 15158332)
            playerEmbed.add_field(name="Profile", value=f"[Steam]({banProfile})")
            playerEmbed.add_field(name="Type", value=f"{banField}")
            playerEmbed.add_field(name="Last Ban", value=f"{banDay} day/s ago")
            playerEmbed.add_field(name="Total Bans", value=vacAmount)
            playerEmbed.add_field(name="Add Date", value=values[1])
            playerEmbed.add_field(name="Added By", value=f"<@!{values[0]}>")
            await channel.send(embed=playerEmbed)
            cur.execute('UPDATE players SET notified = 1 WHERE steamID = ?', (playerId,))        
            db.commit()


@called_once_a_day_vac.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting for daily check")


called_once_a_day_vac.start()
bot.run(discordToken)