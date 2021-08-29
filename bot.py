import os, random, discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client = commands.Bot(command_prefix='-')
client.remove_command('help')

@client.event
async def on_ready():
    activity = discord.Game(name="Counter-Strike: Global Offensive", type=3)
    await client.change_presence(activity=activity)
    print('Success!')

@client.command()
async def help(ctx):
    embed = discord.Embed(
        title='Command List',
        description='Try out any of the commands listed below.',
        colour=discord.Colour.blue()
    )
    embed.add_field(name='Help', value='Lorem ipsum dolor sit amet, consectetur adipiscing elit, 
                    sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim 
                    ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip 
                    ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate 
                    velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat 
                    cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id 
                    est laborum.', inline=False)

    await ctx.send(embed=embed)    
    
@client.command()
async def hello(ctx):
    chats = ["The last time I was this happy, I was told I could stop paying alimony.",
             "You're alive! I've never been more happy to lose fifty quid.",
             "You deserve a promotion! Well, our fundings all tied up so I can't afford to give you one but on paper, "
             "wooo, you've earned it."]
    await ctx.send(random.choice(chats))

client.run(token)
