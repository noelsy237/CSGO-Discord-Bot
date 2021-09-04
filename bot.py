import os, random, discord, json, requests, datetime, database
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
from discord import Color
from asyncio import sleep
from steam.steamid import SteamID

load_dotenv()
discordToken = os.getenv('DISCORD_TOKEN')
steamToken = os.getenv('STEAM_TOKEN')
vacChannelId = int(os.getenv('VAC_CHANNEL_ID'))
bot = commands.Bot(command_prefix='-')
audioText = json.load(open('audio.json'))
bot.remove_command('help')

# Init function
@bot.event
async def on_ready():
    activity = discord.Game(name="Counter-Strike: Global Offensive", type=3)
    await bot.change_presence(activity=activity)
    print('Bot started successfully')

# Make bot leave when channel is empty
@bot.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
        return 
    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()

# Help command
@bot.command()
async def help(ctx):
    helpEmbed = discord.Embed(title = "Hello operator!", colour = Color.teal())
    helpEmbed.add_field(name="-hi", value="Use any option to hear an audio clip.")
    helpEmbed.add_field(name="Options", value="[felix] [legacy] [hostage]\n\nExample: -hi felix")
    helpEmbed.add_field(name='\u200b', value="\u200b", inline=False)
    helpEmbed.add_field(name="-vac", value="""Add a suspected cheater to a tracking list by using their profile url. 
        You can also retrieve a list of all players being tracked or banned""")
    helpEmbed.add_field(name="Options", value="[profile] [track] [ban]\n\nExample: -vac https://steamcommunity.com/id/Micky2000")
    await ctx.channel.send(embed=helpEmbed)

# Play a random audio clip from game files
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

# Add a player to the tracking list for ban checking
@bot.command()
async def vac(ctx, input=None, playerLink=None):
    db = database.get_db()
    error = None
    if input:
        input.strip()
        if input == "track":
            await showList(ctx, "track")
            return
        elif input == "ban":
            await showList(ctx, "ban")
            return
        elif input == "remove":
            await removeFromList(ctx, playerLink)
            return
        userId = SteamID.from_url(input)
        player = SteamID(userId)
        if not player.is_valid():
            error = "User was not found. You must supply a community profile URL."
        elif db.execute('SELECT EXISTS(SELECT 1 FROM players WHERE steamID = ?)', (userId,)).fetchone()[0]:
            error = "User has already been added."
    
        if error is None:
            db.execute('INSERT INTO players (steamID, author, addedDate, banned) VALUES (?, ?, ?, ?)', 
                (userId, str(ctx.author.id), datetime.datetime.now(), 0))
            db.commit()
            #await ctx.message.delete() 
            await ctx.send(f"Player with ID {userId} added to tracking list.")
            await called_once_a_day_vac(userId)
        else:
            await ctx.send(error)
    else:
        await ctx.send("You must supply a community profile URL.")

# Show a list of players
async def showList(ctx, type):
    if type == "track":
        playersDict = getAllPlayers(0)
        embedTitle = "Currently Tracking Players:"
    elif type == "ban":
        playersDict = getAllPlayers(1)
        embedTitle = "Currently Banned Players:"
    playerEmbed = discord.Embed(title = embedTitle, colour = Color.purple())
    for playerId, values in playersDict.items():
        playerEmbed.add_field(name="Profile", value=f"[Steam](https://steamcommunity.com/profiles/{playerId})")
        playerEmbed.add_field(name="Added By", value=f"<@!{values[0]}>")
        playerEmbed.add_field(name="Added On", value=f"{values[1]}")
    await ctx.channel.send(embed=playerEmbed)

# Remove a player from tracking list
async def removeFromList(ctx, playerLink):
    db = database.get_db()
    userId = SteamID.from_url(playerLink)
    player = db.execute('SELECT author FROM players WHERE steamID = ?', (userId,)).fetchone()
    if player:
        if int(player[0]) == ctx.message.author.id:
            db.execute('DELETE FROM players WHERE steamID = ?', (userId,))
            db.commit()
            await ctx.channel.send(f"Player with ID {userId} removed from the tracking list.")
        else:
            await ctx.channel.send("You are not the original person who added this player.")
    else:
        await ctx.channel.send("This player does not exist in the tracking list.")

# Check if any tracked player is banned
@tasks.loop(hours=24)
async def called_once_a_day_vac(userId=None):
    db = database.get_db()
    channel = bot.get_channel(vacChannelId)
    playersDict = {}
    if userId is None:
        playersDict = getAllPlayers(0)
    else:
        playersDB = db.execute('SELECT author, datetime(addedDate) FROM players WHERE steamID = ?', (userId,)).fetchone()
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
            playerEmbed = discord.Embed(title = "Ban Detected", colour = Color.red())
            playerEmbed.add_field(name="Profile", value=f"[Steam]({banProfile})")
            playerEmbed.add_field(name="Type", value=f"{banField}")
            playerEmbed.add_field(name="Last Ban", value=f"{banDay} day/s ago")
            playerEmbed.add_field(name="Total Bans", value=vacAmount)
            playerEmbed.add_field(name="Added On", value=values[1])
            playerEmbed.add_field(name="Added By", value=f"<@!{values[0]}>")
            await channel.send(embed=playerEmbed)
            db.execute('UPDATE players SET banned = 1 WHERE steamID = ?', (playerId,))        
            db.commit()

# Return a list of all players
def getAllPlayers(banned):
    db = database.get_db()
    playersDict = {}
    playersDB = db.execute('SELECT steamID, author, datetime(addedDate) FROM players WHERE banned = ?', (int(banned),)).fetchall()
    for row in playersDB:
        steamdID, author, addedDate = row
        conv_date = datetime.datetime.strptime(addedDate, "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")
        playersDict[steamdID] = [author, conv_date]
    return playersDict

# Format date_time into D/MM/YYYY
def formatDateTime(dateTime):
    return datetime.datetime.strptime(dateTime, "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")

# Daily ban checker
@called_once_a_day_vac.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting for daily check")

# Main run
called_once_a_day_vac.start()
bot.run(discordToken)