import os, random, discord, json, requests, datetime
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio, Color
from steam.steamid import SteamID
from database import get_db
from youtube_dl import YoutubeDL

# Oath2 URL:
'''https://discord.com/api/oauth2/authorize?client_id=881401966377463860&permissions=36793344&redirect_uri=https%3A%2F%2Fdiscord.com%2Fapp
&response_type=code&scope=identify%20bot'''


load_dotenv()
discordToken = os.getenv('DISCORD_TOKEN')
steamToken = os.getenv('STEAM_TOKEN')
bot = commands.Bot(command_prefix='!')
audioText = json.load(open('audio.json'))
bot.remove_command('help')
# Only certain servers can use music functionality
authorisedMusicGuildIds = [851353987025600554, 438667788962496534] #Gaming Hub & Legend

## Events
# Init function
@bot.event
async def on_ready():
    activity = discord.Game(name="Counter-Strike: Global Offensive", type=3)
    await bot.change_presence(activity=activity)
    db = get_db()
    for guild in bot.guilds:
        if not db.execute('SELECT EXISTS(SELECT 1 FROM guilds WHERE id = ?)', (guild.id,)).fetchone()[0]: 
            db.execute('INSERT INTO guilds (id, alert_channel, add_date) VALUES (?, ?, ?)', 
                (guild.id, '0', datetime.datetime.now()))
            db.commit()
    print('Bot started successfully')

# When bot is added to a new guild
@bot.event
async def on_guild_join(guild):
    db = get_db()
    db.execute('INSERT INTO guilds (id, alert_channel, add_date) VALUES (?, ?, ?)', 
        (guild.id, '0', datetime.datetime.now()))
    db.commit()

# When a bot is removed from a guild
@bot.event
async def on_guild_remove(guild):
    db = get_db()
    db.execute('DELETE FROM guilds WHERE id = ?', (guild.id,))
    db.commit()
    db.execute('DELETE FROM players WHERE guild_id = ?', (guild.id,))
    db.commit()

# Make bot leave when channel is empty
@bot.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
        return 
    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()

# @bot.event
# async def on_message(message):
#     if bot.user.mentioned_in(message):
#         await message.channel.send("Hello there! If you are in need of a hand, try !help.")
#     await bot.process_commands(message)

## Commands
# Help command
@bot.command()
async def help(ctx):
    helpEmbed = discord.Embed(title = "Hello operator!", colour = Color.teal())
    helpEmbed.add_field(name="!hi", value="Use any option to hear an audio clip.")
    helpEmbed.add_field(name="Options", value="[felix] [legacy] [hostage]\n\nExample: !hi felix")
    helpEmbed.add_field(name='\u200b', value="\u200b", inline=False)
    helpEmbed.add_field(name="!vac", value="""Add a suspected cheater to a tracking list by using their profile url. 
        You can also retrieve a list of all players being tracked or banned""")
    helpEmbed.add_field(name="Options", value="[profile] [track] [ban]\n\nExample: !vac https://steamcommunity.com/id/Micky2000")
    helpEmbed.add_field(name='\u200b', value="\u200b", inline=False)
    helpEmbed.add_field(name="!p", value="Supply a Youtube link or keywords to play audio. (Only on authorised servers)")
    helpEmbed.add_field(name="Options", value="""[url] [keyword] \n\nExample: !p bad piggies
        \n\nYou can also pause and resume playback with [!pause] [!resume]""")
    helpEmbed.add_field(name='\u200b', value="\u200b", inline=False)
    await ctx.send(embed=helpEmbed)

# Play a random audio clip from game files
@bot.command()
async def hi(ctx, type=None):
    #https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py
    if ctx.author.voice and ctx.author.voice.channel:
        #await ctx.message.delete()
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
        await ctx.send(text)
        ctx.voice_client.play(discord.FFmpegPCMAudio(source=f"audio/{audio}.wav"))
    else:
        await ctx.send("You are not connected to a voice channel.")

# Add a player to the tracking list for ban checking
@bot.command()
async def vac(ctx, input=None, playerLink=None):
    db = get_db()
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
            error = "User was not found. You must supply a valid community profile URL."
        elif db.execute('SELECT EXISTS(SELECT 1 FROM players WHERE steam_id = ? and guild_id = ?)', (userId, ctx.guild.id)).fetchone()[0]:
            error = "User has already been added."
    
        if error is None:
            db.execute('INSERT INTO players (steam_id, author, add_date, banned, guild_id) VALUES (?, ?, ?, ?, ?)', 
                (userId, str(ctx.author.id), datetime.datetime.now(), 0, ctx.guild.id))
            db.commit()
            await ctx.send(f"Player with ID {userId} added to tracking list.")
            await called_once_a_day_vac(userId, ctx.guild.id)
        else:
            await ctx.send(error)
    else:
        await ctx.send("You must supply a community profile URL.")

# Set the alert channel id for bans
@bot.command()
@commands.has_guild_permissions(manage_guild=True)
async def channel(ctx, channelId):
    db = get_db()
    if channelId is None:
        await ctx.send("You need to supply a channel ID. Enable developer mode -> Right click on desired channel -> Copy ID")
        return
    db.execute('UPDATE guilds SET alert_channel = ? WHERE id = ?', (channelId, ctx.guild.id)) 
    db.commit()
    await ctx.send("Alert channel updated successfully.")

# Initiate new music play session
@bot.command(aliases=['play'])
async def p(ctx, *, input):  
    if ctx.guild.id in authorisedMusicGuildIds and input:
        if ctx.author.voice and ctx.author.voice.channel:
            YDL_OPTIONS = {'format': '250/251/140/249', 'noplaylist': True, 'default_search': 'auto'}
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
            musicEmbed = discord.Embed(title = "Playing", colour = Color.blue())
            authorChannel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await authorChannel.connect()
            elif ctx.voice_client.channel != authorChannel:
                await ctx.voice_client.disconnect()
                await authorChannel.connect()
            if ctx.voice_client.is_playing():
                await ctx.send("Audio is already playing. Queue functonality not yet implemented.")
                return

            with YoutubeDL(YDL_OPTIONS) as ydl:
                video = ydl.extract_info(input, download=False)

                if 'entries' in video: info = video['entries'][0]    
                elif 'formats' in video: info = video
                else: 
                    await ctx.send("Error, please try again later.")
                    return

                title = info['title']
                thumbnail = info['thumbnail']
                url = info["url"]
                duration = info['duration']
                filesize = info['filesize']
                
                if duration > 5400:
                    await ctx.send("Audio duration is too long. Maximum 1.5 hours")
                    return
                
                ctx.voice_client.play(FFmpegPCMAudio(url, **FFMPEG_OPTIONS))

                musicEmbed.add_field(name="Title", value=f"{title}")
                musicEmbed.add_field(name="Requested By", value=f"{ctx.author.name}")
                musicEmbed.add_field(name='\u200b', value="\u200b", inline=False)
                musicEmbed.add_field(name="Duration (Mins)", value=f"{str(round(float(duration/60),2))}")
                musicEmbed.add_field(name="Filesize (MB)", value=f"{str(round(float(filesize/1024/1024),2))}")
                musicEmbed.set_thumbnail(url=thumbnail)
                await ctx.send(embed=musicEmbed)
        else:
            await ctx.send("You are not connected to a voice channel.")
    else:
        await ctx.send("Either the input was invalid, or this server is not authorised to use this feature.")
    
# Resume music 
@bot.command()
async def resume(ctx):
    if ctx.guild.id in authorisedMusicGuildIds:
        if ctx.author.voice and ctx.author.voice.channel:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                if not ctx.voice_client.is_playing():
                    ctx.voice_client.resume()
                    await ctx.send('Audio is resuming.')
            else:
                await ctx.send("You are not connected to the same voice channel.")
        else:
            await ctx.send("You are not connected to a voice channel.")
    else:
        await ctx.send("This server is not authorised to use this feature.")

# Pause music
@bot.command()
async def pause(ctx):
    if ctx.guild.id in authorisedMusicGuildIds:
        if ctx.author.voice and ctx.author.voice.channel:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                if ctx.voice_client.is_playing():
                    ctx.voice_client.pause()
                    await ctx.send('Audio has been paused.')
            else:
                await ctx.send("You are not connected to the same voice channel.")
        else:
            await ctx.send("You are not connected to a voice channel.")
    else:
        await ctx.send("This server is not authorised to use this feature.")

# Disconnect bot
@bot.command(aliases=['dc'])
async def disconnect(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

# Skip music
@bot.command(aliases=['s'])
async def skip(ctx):
    if ctx.guild.id in authorisedMusicGuildIds:
            if ctx.author.voice and ctx.author.voice.channel:
                if ctx.voice_client.channel == ctx.author.voice.channel:
                    if ctx.voice_client.is_playing():
                        ctx.voice_client.stop()
                        await ctx.send('Skipped.')

## Functions
# Show a list of players
async def showList(ctx, type):
    if type == "track":
        playersDict = getAllPlayers(0, ctx.guild.id)
        embedTitle = "Currently Tracking Players:"
    elif type == "ban":
        playersDict = getAllPlayers(1, ctx.guild.id)
        embedTitle = "Currently Banned Players:"
    playerEmbed = discord.Embed(title = embedTitle, colour = Color.purple())
    for playerId, values in playersDict.items():
        playerEmbed.add_field(name="Profile", value=f"[Steam](https://steamcommunity.com/profiles/{playerId})")
        playerEmbed.add_field(name="Added By", value=f"<@!{values[0]}>")
        playerEmbed.add_field(name="Added On", value=f"{values[1]}")
    await ctx.channel.send(embed=playerEmbed)

# Remove a player from tracking list
async def removeFromList(ctx, playerLink):
    db = get_db()
    userId = SteamID.from_url(playerLink)
    player = db.execute('SELECT author FROM players WHERE steam_id = ? AND guild_id = ?', (userId, ctx.guild.id)).fetchone()
    if player:
        if int(player[0]) == ctx.message.author.id:
            db.execute('DELETE FROM players WHERE steam_id = ? AND guild_id = ?', (userId, ctx.guild.id))
            db.commit()
            await ctx.channel.send(f"Player with ID {userId} removed from the tracking list.")
        else:
            await ctx.channel.send("You are not the original person who added this player.")
    else:
        await ctx.channel.send("This player does not exist in the tracking list.")

# Return a list of all players
def getAllPlayers(banned, guildId=None):
    db = get_db()
    playersDict = {}
    if guildId:
        playersDB = db.execute('SELECT steam_id, author, datetime(add_date), guild_id FROM players WHERE guild_id = ? AND banned = ?', (guildId, int(banned))).fetchall()    
    else:
        playersDB = db.execute('SELECT steam_id, author, datetime(add_date), guild_id FROM players WHERE banned = ?', (int(banned),)).fetchall()
    for row in playersDB:
            steamdID, author, addedDate, guild_id = row
            conv_date = datetime.datetime.strptime(addedDate, "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")
            playersDict[steamdID] = [author, conv_date, int(guild_id)]
    return playersDict

# Format date_time into D/MM/YYYY
def formatDateTime(dateTime):
    return datetime.datetime.strptime(dateTime, "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")


## Scheduled Functions
# Check if any tracked player is banned
@tasks.loop(hours=24)
async def called_once_a_day_vac(userId=None, guildId=None):
    db = get_db()
    playersDict = {}
    if userId is None and guildId is None:
        playersDict = getAllPlayers(0)
    else:
        playersDB = db.execute('SELECT author, datetime(add_date) FROM players WHERE steam_id = ?', (userId,)).fetchone()
        playersDict[userId] = (playersDB[0], datetime.datetime.strptime(playersDB[1], "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y"), guildId)

    for playerId, values in playersDict.items():
        player = json.loads(requests.get(f'http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={steamToken}&steamids={playerId}').text)['players'][0]
        banField = None
        vacBan = player['VACBanned']
        vacAmount = player['NumberOfVACBans']
        gameAmount = player['NumberOfGameBans']
        banDay = player['DaysSinceLastBan']
        alertChannel = db.execute('SELECT alert_channel FROM guilds WHERE id = ?', (values[2],)).fetchone()[0]
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
            channel = bot.get_channel(int(alertChannel))
            await channel.send(embed=playerEmbed)
            db.execute('UPDATE players SET banned = 1 WHERE steam_id = ? AND guild_id = ?', (playerId, values[2]))        
            db.commit()


# Daily ban checker
@called_once_a_day_vac.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting for daily check")

# Main run
called_once_a_day_vac.start()
bot.run(discordToken)
