from __future__ import unicode_literals
import discord
import os
import random
import json
import urllib.parse
import youtube_dl
from discord.ext import commands
from youtube_dl import YoutubeDL
from dotenv import load_dotenv, find_dotenv

intents= discord.Intents.default()
intents.members = True
load_dotenv(find_dotenv())
bot_token = os.environ.get("bot_token")
prefix = os.environ.get("prefix")
client = commands.Bot(command_prefix=prefix, help_command=None, intents=intents)

donator_roles = [743031850435477594, #Perms
                 743031374251950131, #Admin
                 746663126338109581, #Developer
                 789529083372634183, #Super Moderator
                 767099706861027429, #VIP
                 764639361999962143, #Patreon Level 6
                 764639282857246800, #Patreon Level 5
                 764639157661597756, #Patreon Level 4
                 764639093207597066, #Patreon Level 3
                 764638878320689183, #Patreon Level 2
                 743031628212994130, #Patreon Level 1
                 803894379982880778, #Donator
                 763337908211154955, #Server Booster
                 838915073363017738] #Premium: Reuploader

@client.command()
async def yt(ctx, args = "null"):
    owner_has_gdps = await check_owner_has_gdps(ctx)
    if owner_has_gdps is False:
        return
    with open("servers.json", "r+") as file:
        data = json.load(file)
        file.seek(0)
        if str(ctx.channel.id) not in str(data):
            data[str(ctx.guild.id)] = {"whitelisted_channels": []}
            json.dump(data, file, indent=4)
        if ctx.channel.id not in data[str(ctx.guild.id)]["whitelisted_channels"]:
            embed = discord.Embed(description = "This channel is not whitelisted.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
    log_channel = client.get_channel(810073425103028294)
    uploaderid = ctx.message.author.id

    with open("banned_songs.json", "r+") as file:
        data = json.load(file)
        file.close()

    if args == "null":
        await ctx.send("You need to enter an url")
    else:
        checktitle(args)
        banned = False
        for songname_part in data:
            if str(songname_part).lower() in str(video_title_check).lower():
                banned = True

        if banned:
            await ctx.send("This song is banned from this tool.")
        else:
            await ctx.send("Reuploading song please wait...")
            dlvid = await downloadvid(args)
            if dlvid == "toolong":
                await ctx.send("This video is too long, the maximum is 10 minutes")
                return
            send_link = urllib.parse.quote(video_title, safe='')
            await ctx.send("Reupload success! link: http://ps.fhgdps.com/songs/" + send_link + ".mp3")
            await log_channel.send("<@" + str(uploaderid) + "> Reuploaded: " + video_title)

@client.command()
async def whitelist(ctx, arg1=None, mention="null"):
    if not ctx.author.guild_permissions.administrator:
        embed = discord.Embed(description = "You need the administrator permission to use this command.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    gid = str(ctx.guild.id)
    with open("servers.json", "r+") as file:
        data = json.load(file)
        file.seek(0)
        if str(ctx.channel.id) not in str(data):
            data[str(ctx.guild.id)] = {"whitelisted_channels": []}
            json.dump(data, file, indent=4)
        if arg1 is None or arg1 == "help":
            embed = discord.Embed(title="Whitelist command help", description = f"**{prefix}whitelist add <channel mention>**: Add a channel to the whitelist so that it can be used to reupload songs\n"
                                                                              + f"**{prefix}whitelist remove <channel mention>**: Removes a channel from the whitelist", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        elif arg1 == "add":
            try:
                channel = await commands.TextChannelConverter().convert(ctx, mention)
                channelid = channel.id
            except:
                embed = discord.Embed(description = "Channel not found.", color = discord.Colour.red())
                await ctx.send(embed=embed)
                return
            if channelid in data[gid]["whitelisted_channels"]:
                embed = discord.Embed(description = "This channel is already whitelisted.", color = discord.Colour.red())
                await ctx.send(embed=embed)
                return
            else:
                file.seek(0)
                data[gid]["whitelisted_channels"].insert(len(data), channelid)
                json.dump(data, file, indent=4)
                embed = discord.Embed(description = "This channel can now be used to reupload songs!", color = discord.Colour.green())
                await ctx.send(embed=embed)
        elif arg1 == "remove":
            try:
                channel = await commands.TextChannelConverter().convert(ctx, mention)
                channelid = channel.id
            except:
                embed = discord.Embed(description = "Channel not found.", color = discord.Colour.red())
                await ctx.send(embed=embed)
                return
            if channelid in data[gid]["whitelisted_channels"]:
                data[gid]["whitelisted_channels"].remove(channelid)
                json.dump(data, file, indent=4)
                file.truncate()
                embed = discord.Embed(description = "This channel can no longer be used to reupload songs!", color = discord.Colour.green())
                await ctx.send(embed=embed)
                return
            else:
                embed = discord.Embed(description = "This channel was never whitelisted.", color = discord.Colour.red())
                await ctx.send(embed=embed)
                return
        else:
            embed = discord.Embed(description = "Invalid option.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return

@client.command()
@commands.has_any_role(743031490870509639, 789529083372634183, 743031374251950131, 743031850435477594)
async def delete(ctx, *, arg = "null"):
    log_channel = client.get_channel(810073425103028294)
    uploaderid = ctx.message.author.id
    if arg == "null":
        await ctx.send("You need to enter a song name")
    else:
        os.remove("/var/www/gdps/songs/" + arg + ".mp3")
        await ctx.send("Song removed!")
        await log_channel.send("<@" + str(uploaderid) + "> Deleted the song: " + video_title)

@client.command()
@commands.has_any_role(743031490870509639, 789529083372634183, 743031374251950131, 743031850435477594)
async def ban(ctx, *, arg = "null"):
    if arg == "null":
        await ctx.send("You need to enter a song name")
    else:
        with open("banned_songs.json", "r+") as file:
            data = json.load(file)

            if arg in data:
                await ctx.send("This is already banned!")
            else:
                data.insert(len(data), str(arg.lower()))

                file.seek(0)
                json.dump(data, file, indent=4)
                await ctx.send("Songs that contains \"" + arg + "\" in the title are now banned.")

@client.command()
@commands.has_any_role(743031490870509639, 789529083372634183, 743031374251950131, 743031850435477594)
async def unban(ctx, *, arg = "null"):
    lowerargs = str(arg.lower())
    if arg == "null":
        await ctx.send("You need to enter a song name")
    else:
        with open("banned_songs.json", "r+") as file:
            data = json.load(file)
            file.seek(0)

            if arg in data:
                data.remove(lowerargs)
                json.dump(data, file, indent=4)
                file.truncate()
                await ctx.send("Unbanned \"" + arg + "\"")
            else:
                await ctx.send("This song is not banned")

async def downloadvid(url):
    ydl_opts = {
        "outtmpl": "/var/www/gdps/songs/%(title)s.",
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    global video_title

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_title = info_dict.get('title', None)
        video_duration = info_dict.get('duration', None)
        if video_duration > 600:
            return "toolong"

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
def checktitle(url):
    ydl_opts = {
        "outtmpl": "/var/www/gdps/songs/%(title)s.",
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    global video_title_check

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_title_check = info_dict.get('title', None)

async def check_owner_has_gdps(ctx):
    ownerid = ctx.guild.owner.id
    gdpsfh = client.get_guild(743013350446989442)
    owner_premium = gdpsfh.get_member(ownerid)
    with open("../../GDPS_Creator/user-data.json", "r+") as file:
        data = json.load(file)
        if str(ownerid) in data:
            for rid in donator_roles:
                if str(rid) in str(owner_premium.roles):
                    return True
            embed = discord.Embed(description=f"The owner of this discord needs to be a server booster or a donator on the GDPS Free Hosting discord to be able to use the bot.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return False
        else:
            embed = discord.Embed(description=f"The owner of this discord must have a GDPS in the GDPS Free Hosting discord to be able to use the bot.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return False
    return False

@client.command()
async def help(ctx):
    embed = discord.Embed(title="Help command", description = f"**{prefix}whitelist** : Whitelist a channel so that it can be used to reupload songs\n" +
                                                              f"**{prefix}yt** : Reupload a song from youtube", color = discord.Colour.red())
    await ctx.send(embed=embed)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name=f"{prefix}help"))
    print("Bot pret")

client.run(bot_token)