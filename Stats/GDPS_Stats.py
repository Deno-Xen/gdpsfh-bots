import discord
from discord import Member
from discord.ext import commands
from discord.ext.commands import has_permissions
import mysql.connector
from mysql.connector import Error
import json
import os
import typing
import urllib.request
import base64
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
bot_token = os.environ.get("bot_token")
prefix = os.environ.get("prefix")
mysql_ip = os.environ.get("mysql_ip")
mysql_port = os.environ.get("mysql_port")
mysql_database = os.environ.get("mysql_database")
mysql_user = os.environ.get("mysql_user")
mysql_pass = os.environ.get("mysql_pass")

client = commands.Bot(command_prefix = prefix, help_command=None)
connection_dictionnary = {}

database_connection = None
try:
    database_connection = mysql.connector.connect(host=mysql_ip,
                                         database=mysql_database,
                                         user=mysql_user,
                                         port = int(mysql_port),
                                         password=mysql_pass)
    print("Connected to the DB!")
except:
    print("Couldn't connect to the database.")
    exit()

if database_connection is None:
    exit()

database_connection.autocommit = 1
database_cursor = database_connection.cursor(buffered=True)

try:
    f = open("StatsDatabase.json")
    with open("StatsDatabase.json", "r+") as file:
        data = json.load(file)
        file.seek(0)
        json.dump(data, file, sort_keys=True, indent=4)
    print("Stats Database found, using it")
except IOError:
    print("Stats Database not found, creating one...")
    f= open("StatsDatabase.json","w+")
    f.write(r"{}")
    print("File created!")
finally:
    f.close()

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="gdps!help"))
    print("Bot pret")

@client.command(name="setup", pass_context=True)
@has_permissions(administrator=True)
async def setup(ctx):
    serverid = ctx.message.guild.id

    data = await get_server_data(serverid)
    if data is not None:
        await ctx.send("This server is already setup!")
        if not has_connection(serverid):
            connection = mysql.connector.connect(host='127.0.0.1',
                                                 database=data["mysqldatabase"],
                                                 user=data["mysqluser"],
                                                 password=data["password"])
            connection_dictionnary[serverid] = { "connection": connection }
    else:
        await logs(ctx.guild.id, ctx.author.id, "setup")
        await ctx.send("Alright first of all are you in a private channel that only you or admins can see? yes/no")
        isinprivatechannel = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        if isinprivatechannel.content.lower() == "yes":
            await ctx.send("Next: is your gdps hosted by the GDPS free hosting discord? yes/no")
            isHostedByMat = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            if isHostedByMat.content.lower() == "yes":

                await ctx.send("Great! Now enter your custom URL\n\nExample: if your current URL is \"http://ps.fhgdps.com/testgdps1234\" then just enter the end of the url so here its \"testgdps1234\"")
                customurl = await client.wait_for('message', check=lambda message: message.author == ctx.author)
                customurl = customurl.content

                database_cursor.execute("select * from gdps_creator_userdata where gdps_custom_url = %s", [customurl])
                database_info = database_cursor.fetchall()
                if database_cursor.rowcount == 0:
                    await ctx.send("This custom URL is not valid")
                    return
                patchedurl = f"gdps_{database_info[0][2]}"
                userpass = database_info[0][4]
                try:
                    await ctx.send("Testing connection...")
                    connection = mysql.connector.connect(host='127.0.0.1',
                                                database=str(patchedurl),
                                                user=str(patchedurl),
                                                password=userpass)
                    if connection.is_connected():
                        db_Info = connection.get_server_info()
                        await ctx.send("Your gdps is now linked to this discord server!")
                        
                        connection_dictionnary[serverid] = {"connection": connection}

                        with open("StatsDatabase.json", "r+") as file:
                            data = json.load(file)
                            
                            data[serverid] = {
                                "mysqlhost": "127.0.0.1",
                                "mysqlport": str(connection._port), 
                                "mysqldatabase": str(patchedurl),
                                "mysqluser": str(patchedurl), 
                                "password": str(userpass)
                            }
                            file.seek(0)
                            json.dump(data, file, indent=4)

                except Error as e:
                    print(e)
                    await ctx.send("Your database informations are incorrect, please enter the command again with the right informations")

            elif isHostedByMat.content.lower() == "no":
                await ctx.send("Great! Now i need your MySQL hostname (7m.pl not supported because they blocked remote connections)")
                mysqlhost = await client.wait_for('message', check=lambda message: message.author == ctx.author)

                await ctx.send("Great! Now i need your MySQL port / Most common: 3306")
                mysqlport = await client.wait_for('message', check=lambda message: message.author == ctx.author)

                await ctx.send("Great! Now i need your MySQL database name")
                mysqldatabase = await client.wait_for('message', check=lambda message: message.author == ctx.author)

                await ctx.send("Great! Now i need your MySQL user")
                mysqluser = await client.wait_for('message', check=lambda message: message.author == ctx.author)

                await ctx.send("Good! Now i need your MySQL password")
                mysqlpass = await client.wait_for('message', check=lambda message: message.author == ctx.author)

                try:
                    await ctx.send("Testing connection...")
                    connection = mysql.connector.connect(host=str(mysqlhost.content()),
                                                        port=str(mysqlport.content()),
                                                        database=str(mysqldatabase.content()),
                                                        user=str(mysqluser.content()),
                                                        password=str(mysqlpass.content()))
                    if connection.is_connected():
                        db_Info = connection.get_server_info()
                        await ctx.send("Connected to MySQL Server version " + db_Info)
                        connection.close()

                        with open("StatsDatabase.json", "r+") as file:
                            data = json.load(file) 
                            data[serverid] = {
                                "mysqlhost": str(mysqlhost.content),
                                "mysqlport": str(connection._port),
                                "mysqldatabase": str(mysqldatabase.content),
                                "mysqluser": str(mysqluser.content), 
                                "password": str(mysqlpass.content)
                            }
                            file.seek(0)
                            json.dump(data, file, sort_keys=True, indent=4)

                except Error as e:
                    await ctx.send("Error while connecting to MySQL" + str(e))

            else:
                await ctx.send("You need to answer the question.")
        else:
            await ctx.send("Then go in a private channel before getting further, you don't want all your members to see your gdps database login info right?")

@client.command()
@has_permissions(administrator=True)
async def updateinfo(ctx):
    await logs(ctx.guild.id, ctx.author.id, "updateinfo")
    serverid = ctx.guild.id
    with open("StatsDatabase.json", "r+") as file:
        data = json.load(file)
        file.seek(0)
        if str(serverid) not in data:
            await ctx.send("This server is not linked!")
            return
        if data[str(serverid)]["mysqlhost"] == "127.0.0.1":
            patchedurl = str(data[str(serverid)]["mysqldatabase"]).replace("gdps_", "")
            database_cursor.execute("select * from gdps_creator_userdata where gdps_custom_url = %s", [patchedurl])
            database_info = database_cursor.fetchall()
            if database_cursor.rowcount == 0:
                await ctx.send("This custom URL is not valid")
                return
            data[str(serverid)]["password"] = database_info[0][4]
            json.dump(data, file, indent=4)
            await ctx.send("Server updated!")
            return

async def get_server_data(serverid):
    with open("StatsDatabase.json", "r+") as file:
        data = json.load(file)
        if str(serverid) in data:
            return data[str(serverid)]
    return None

async def levellisttemplate(ctx, embed, records, cursor):
    emoji_star_difficulty = {
        "0" : "<:unrated:798358095487041566>",
        "10": "<:easy:798342287087632434>",
        "20": "<:normal:798342323951632404>",
        "30": "<:hard:798342350274953219>",
        "40": "<:harder:798342370289647626>",
        "50": "<:insane:798342386560270337>"
    }
    emoji_star_difficulty_demon = {
        "3": "<:easydemon:798342474976198666>",
        "4": "<:mediumdemon:798342514502926336>",
        "0": "<:harddemon:798241354379034624>",
        "5": "<:insanedemon:798342557900734484>",
        "6": "<:extremedemon:798342589832626196>"
    }
    emoji_star_auto = "<:auto:798342232394301510>"
    emoji_star_featured_difficulty = {
        "0" : "<:unrated:798358095487041566>",
        "10": "<:featured_easy:798542116765958184>",
        "20": "<:featured_normal:798543308641140766>",
        "30": "<:featured_hard:798543343381774337>",
        "40": "<:featured_harder:798543376474964038>",
        "50": "<:featured_insane:798541756001943572>"
    }
    emoji_star_featured_difficulty_demon = {
        "3": "<:featured_easydemon:798543467335647262>",
        "4": "<:featured_mediumdemon:798543508528300032>",
        "0": "<:featured_harddemon:798543571107840001>",
        "5": "<:featured_insanedemon:798543610353811516>",
        "6": "<:featured_extremedemon:798543646399135766>"
    }
    emoji_star_featured_auto = "<:featured_auto:798540563405733898>"

    if cursor.rowcount == 0:
        await ctx.send("You reached the end!")
        return
    else:
        for row in records:

            diff = ""
            if int(row[25]) == 1:
                if int(row[31]) == 1:
                    diff = emoji_star_featured_auto
                else:
                    diff = emoji_star_auto
            elif int(row[24]) == 1:
                if int(row[31]) == 1:
                    diff = emoji_star_featured_difficulty_demon[str(row[34])]
                else:
                    diff = emoji_star_difficulty_demon[str(row[34])]
            else:
                if int(row[31]) == 1:
                    diff = emoji_star_featured_difficulty[str(row[21])]
                else:
                    diff = emoji_star_difficulty[str(row[21])]

            lenght = ""
            if int(row[7]) == 0:
                lenght = "Tiny"
            elif int(row[7]) == 1:
                lenght = "Short"
            elif int(row[7]) == 2:
                lenght = "Medium"
            elif int(row[7]) == 3:
                lenght = "Long"
            elif int(row[7]) == 4:
                lenght = "XL"
            else:
                lenght = "Error"
            embed.add_field(name=row[4] + " " + diff, value="\n<:gdstar:798238253500989460> " + ("Not rated" if int(row[26]) == 0 else str(row[26]))
            + "\n<:epic:798532362358095872> " + ("No" if int(row[33]) == 0 else "Yes")
            + "\n<:download:798322135659315210> " + str(row[22]) 
            + ("\n<:dislike:798353417378201600> " if int(row[23]) < 0 else "\n<:gd_like:767754910867259446> ") + str(row[23]) 
            + "\n<:time:798323102798053427> " + lenght, inline=True)

    await ctx.send(embed=embed)

@client.command()
async def help(ctx):
    embed = discord.Embed(title = "Bot informations", color = discord.Colour.from_rgb(255, 0, 0))
    embed.add_field(name = "All commands:", value = "**gdps!help** : Shows you a list of all commands that you can execute"
                                                    + "\n**gdps!setup** : This is to link the bot to your gdps database (Admin only)"
                                                    + "\n**gdps!leaderboard** : Shows diffrent types of leaderboards"
                                                    + "\n**gdps!levels <page>** : Shows you all levels on the gdps"
                                                    + "\n**gdps!gdlevel <id>** : Shows you the informations of a level"
                                                    + "\n**gdps!featured <page>** : Shows you all featured levels on the gdps"
                                                    + "\n**gdps!recent <page>** : Shows you all recent levels on the gdps"
                                                    + "\n**gdps!profile <name>** : Shows you the profile of a specific user"
                                                    + "\n**gdps!leadbanned <page>** : Shows you the list of all leaderboard banned people"
                                                    + "\n**gdps!creatorbanned <page>** : Shows you the list of all creator banned people"
                                                    + "\n**gdps!refreshcp** : Refresh cp of all users"
                                                    + "\n**gdps!ping** : Shows the latency of the bot"
                                                    + "\n**gdps!info** : Shows you who created the bot and how to invite it to your server")

    await ctx.send(embed=embed)

@client.command()
async def leaderboard(ctx, arg1="Null", arg2="Null"):
    await logs(ctx.guild.id, ctx.author.id, "leaderboard")
    connection = await get_connection_with_error_message(ctx)
    if connection is None:
        return
    if arg1 == "Null":
        embed = discord.Embed(title = "Leaderboard options", description = "Command: gdps!leaderboard <option> <page> \n\n **Options:**\n stars\n creator \ncoins \nusercoins \ndemons", color = discord.Colour.from_rgb(0, 189, 255))
        await ctx.send(embed=embed)
    if arg2 == "Null":
        arg2 = 1

    if arg1 == "stars":
        cursor = connection.cursor()
        cursor.execute("select * from users where isRegistered = 1 AND isBanned = 0 order by stars desc LIMIT 12 OFFSET " + str((int(arg2)-1)*10))
        records = cursor.fetchall()
        connection.commit()
        embed = discord.Embed(title = "GDPS Star Leaderboard", description = "If there is nothing on further pages well you just reached the end", color = discord.Colour.from_rgb(0, 189, 255))

        if cursor.rowcount == 0:
            await ctx.send("You reached the end!")
        else:
            for row in records:
                embed.add_field(name = row[3], value = "<:gdstar:798238253500989460> " + str(row[4]), inline = True)

            await ctx.send(embed=embed)
    elif arg1 == "creator":
        cursor = connection.cursor()
        cursor.execute("select * from users where isRegistered = 1 AND isBanned = 0 order by creatorPoints desc LIMIT 12 OFFSET " + str((int(arg2)-1)*10))
        records = cursor.fetchall()
        connection.commit()
        embed = discord.Embed(title = "GDPS CP Leaderboard", description = "This is the creator point leaderboard", color = discord.Colour.from_rgb(0, 189, 255))

        if cursor.rowcount == 0:
            await ctx.send("You reached the end!")
        else:
            for row in records:
                embed.add_field(name = row[3], value = "\n<:creator_point:798260703982256168> " + str(row[22]), inline = True)

            await ctx.send(embed=embed)
    elif arg1 == "coins":
        cursor = connection.cursor()
        cursor.execute("select * from users where isRegistered = 1 AND isBanned = 0 order by coins desc LIMIT 12 OFFSET " + str((int(arg2)-1)*10))
        records = cursor.fetchall()
        connection.commit()
        embed = discord.Embed(title = "GDPS Coin Leaderboard", description = "This is the creator point leaderboard", color = discord.Colour.from_rgb(0, 189, 255))

        if cursor.rowcount == 0:
            await ctx.send("You reached the end!")
        else:
            for row in records:
                embed.add_field(name = row[3], value = "\n<:goldcoin:798298334812831774> " + str(row[10]), inline = True)

            await ctx.send(embed=embed)
    elif arg1 == "usercoins":
        cursor = connection.cursor()
        cursor.execute("select * from users where isRegistered = 1 AND isBanned = 0 order by userCoins desc LIMIT 12 OFFSET " + str((int(arg2)-1)*10))
        records = cursor.fetchall()
        connection.commit()
        embed = discord.Embed(title = "GDPS User Coin Leaderboard", description = "This is the creator point leaderboard", color = discord.Colour.from_rgb(0, 189, 255))

        if cursor.rowcount == 0:
            await ctx.send("You reached the end!")
        else:
            for row in records:
                embed.add_field(name = row[3], value = "\n<:usercoin:798293582364147752> " + str(row[11]), inline = True)

            await ctx.send(embed=embed)
    elif arg1 == "demons":
        cursor = connection.cursor()
        cursor.execute("select * from users where isRegistered = 1 AND isBanned = 0 order by demons desc LIMIT 12 OFFSET " + str((int(arg2)-1)*10))
        records = cursor.fetchall()
        connection.commit()
        embed = discord.Embed(title = "GDPS Demon Leaderboard", description = "This is the creator point leaderboard", color = discord.Colour.from_rgb(0, 189, 255))

        if cursor.rowcount == 0:
            await ctx.send("You reached the end!")
        else:
            for row in records:
                embed.add_field(name = row[3], value = "\n<:harddemon:798241354379034624> " + str(row[5]) , inline = True)

            await ctx.send(embed=embed)
    else:
        await ctx.send("You entered a wrong option")

@client.command()
async def leadbanned(ctx, args: typing.Optional[int]=1):
    await logs(ctx.guild.id, ctx.author.id, "leadbanned")
    connection = await get_connection_with_error_message(ctx)
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute("select * from users where isBanned = 1 order by stars desc LIMIT 12 OFFSET " + str((int(args)-1)*10))
    records = cursor.fetchall()
    connection.commit()
    embed = discord.Embed(title = "Banned users", description = "List of all leaderboard banned users sorted by star amount, you can go further in the list by putting a page number at the end of the command.", color = discord.Colour.from_rgb(0, 189, 255))

    if cursor.rowcount == 0:
        await ctx.send("You reached the end or no one is leaderboard banned!")
    else:
        for row in records:
            embed.add_field(name = row[3], value = "<:gdstar:798238253500989460> " + str(row[4]) 
            + "\n<:harddemon:798241354379034624> " + str(row[5]) 
            + "\n<:creator_point:798260703982256168> " + str(row[22]), inline = True)

        await ctx.send(embed=embed)

@client.command()
async def creatorbanned(ctx, args: typing.Optional[int]=1):
    await logs(ctx.guild.id, ctx.author.id, "creatorbanned")
    connection = await get_connection_with_error_message(ctx)
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute("select * from users where isCreatorBanned = 1 order by stars desc LIMIT 12 OFFSET " + str((int(args)-1)*10))
    records = cursor.fetchall()
    connection.commit()
    embed = discord.Embed(title = "Creator banned users", description = "List of all creator banned users sorted by star amount, you can go further in the list by putting a page number at the end of the command.", color = discord.Colour.from_rgb(0, 189, 255))

    if cursor.rowcount == 0:
        await ctx.send("You reached the end or no one is creator banned!")
    else:
        for row in records:
            embed.add_field(name = row[3], value = "<:gdstar:798238253500989460> " + str(row[4]) 
            + "\n<:harddemon:798241354379034624> " + str(row[5]) 
            + "\n<:creator_point:798260703982256168> " + str(row[22]), inline = True)

        await ctx.send(embed=embed)

@client.command()
async def info(ctx):
    Members = 0
    for i in client.guilds:
        Members += i.member_count

    embed = discord.Embed(title = "Bot informations", color = discord.Colour.from_rgb(255, 0, 0))
    embed.set_thumbnail(url = "https://mathieuar.fr/statsbot.jpg")
    embed.add_field(name = "Team members", value = "**Owner:** MathieuAR"
                                                 + "\n**Contributors:** Ghost, Rya"
                                                 + "\n**Bot profile picture** : Robby"
                                                 + "\n\n**GDPS Free Hosting discord:** [Link](https://discord.gg/CkMV5DV)"
                                                 + "\n**Invite the bot to your server:** [Link](https://discord.com/api/oauth2/authorize?client_id=788451531342872576&permissions=8&scope=bot)"
                                                 + "\n\n**Server count** : " + str(len(client.guilds))  + " servers and " + str(Members) + " members total"
                                                 + "\n**Bot version** : 1.5")

    await ctx.send(embed=embed)

@client.command()
async def levels(ctx, args: typing.Optional[int]=1):
    await logs(ctx.guild.id, ctx.author.id, "levels")
    connection = await get_connection_with_error_message(ctx)
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute("select * from levels where unlisted = 0 AND isDeleted = 0 order by downloads desc LIMIT 9 OFFSET " + str((int(args)-1)*10))
    records = cursor.fetchall()
    connection.commit()
    embed = discord.Embed(title = "Most downloaded levels", description="Here levels are sorted by most downloads, you can go further in the list by putting a page number at the end of the command.", color = discord.Colour.from_rgb(0, 189, 255))

    try:
        await levellisttemplate(ctx, embed, records, cursor)
    except:
        await ctx.send("An error occured.")
        return

@client.command()
async def recent(ctx, args: typing.Optional[int]=1):
    await logs(ctx.guild.id, ctx.author.id, "recent")
    connection = await get_connection_with_error_message(ctx)
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute("select * from levels where unlisted = 0 AND isDeleted = 0 order by uploadDate desc LIMIT 9 OFFSET " + str((int(args)-1)*10))
    records = cursor.fetchall()
    connection.commit()
    embed = discord.Embed(title = "Recent levels", description="Here levels are sorted by the upload date, you can go further in the list by putting a page number at the end of the command.", color = discord.Colour.from_rgb(0, 189, 255))

    await levellisttemplate(ctx, embed, records, cursor)

@client.command()
async def featured(ctx, args: typing.Optional[int]=1):
    await logs(ctx.guild.id, ctx.author.id, "featured")
    connection = await get_connection_with_error_message(ctx)
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute("select * from levels where unlisted = 0 AND isDeleted = 0 AND starFeatured = 1 order by downloads desc LIMIT 9 OFFSET " + str((int(args)-1)*10))
    records = cursor.fetchall()
    connection.commit()
    embed = discord.Embed(title = "Featured levels", description="Here levels are sorted by most downloads, you can go further in the list by putting a page number at the end of the command.", color = discord.Colour.from_rgb(0, 189, 255))

    await levellisttemplate(ctx, embed, records, cursor)

@client.command()
async def profile(ctx, args = "null"):
    await logs(ctx.guild.id, ctx.author.id, "profile")
    connection = await get_connection_with_error_message(ctx)
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute("select * from accounts where userName = %s", [args])
    accountsRecord = cursor.fetchall()
    connection.commit()

    modBadgeLevel = None
    if cursor.rowcount > 0:
    
        accountId = accountsRecord[0][4]

        cursor1 = connection.cursor()
        cursor1.execute("select * from roleassign where accountID = %s", [accountId])
        roleAssign = cursor1.fetchall()
        connection.commit()

        if cursor1.rowcount > 0:

            roleId = roleAssign[0][1]

            cursor2 = connection.cursor()
            cursor2.execute("select * from roles where roleID = %s", [roleId])
            roles = cursor2.fetchall()
            connection.commit()

            if cursor2.rowcount > 0:

                role = roles[0]
                modBadgeLevel = role[40]
    

    cursor = connection.cursor()
    cursor.execute("select * from users where userName = %s", [args])
    accountsRecord = cursor.fetchall()
    connection.commit()

    embed = discord.Embed(title = "GDPS user profile", color = discord.Colour.from_rgb(0, 189, 255))

    ismod = ""
    if modBadgeLevel == 0:
        ismod = ""
    elif modBadgeLevel == 1:
        ismod = "<:gd_mod:767754902976856064>"
    elif modBadgeLevel == 2:
        ismod = "<:gd_eldermod:767754892613255168>"
    else:
        ismod = ""
        
    if args == "null":
        await ctx.send("You need to type an account name!")
    else:
        if cursor.rowcount == 0:
            await ctx.send("The account that you entered does not exist!")
        else:
            for row in accountsRecord:
                embed.add_field(name = row[3] + " " + ismod, value = "<:gdstar:798238253500989460> " + str(row[4]) 
                + " \n " + "<:harddemon:798241354379034624> " + str(row[5]) 
                + " \n " + "<:goldcoin:798298334812831774> " + str(row[10]) 
                + " \n " + "<:usercoin:798293582364147752> " + str(row[11]) 
                + " \n " + "<:diamond:798298365863395339> " + str(row[25]) 
                + " \n " + "<:orbs:798301145080397837> " + str(row[26]) 
                + " \n " + "<:creator_point:798260703982256168> " + str(row[22]) 
                + " \n " + "**Others informations:**"
                + " \n " + "Account ID: " + str(accountId)
                + " \n " + "Completed levels: " + str(row[27])
                + " \n " + "Leaderboard banned: " + ("No" if int(row[34]) == 0 else "Yes")
                + " \n " + "Creator banned: " + ("No" if int(row[35]) == 0 else "Yes"), inline = False)

                await ctx.send(embed=embed)

@client.command()
async def gdlevel(ctx, args = "null"):
    await logs(ctx.guild.id, ctx.author.id, "gdlevel")
    connection = await get_connection_with_error_message(ctx)
    if connection is None:
        return

    emoji_star_difficulty = {
        "0" : "<:unrated:798358095487041566>",
        "10": "<:easy:798342287087632434>",
        "20": "<:normal:798342323951632404>",
        "30": "<:hard:798342350274953219>",
        "40": "<:harder:798342370289647626>",
        "50": "<:insane:798342386560270337>"
    }
    emoji_star_difficulty_demon = {
        "3": "<:easydemon:798342474976198666>",
        "4": "<:mediumdemon:798342514502926336>",
        "0": "<:harddemon:798241354379034624>",
        "5": "<:insanedemon:798342557900734484>",
        "6": "<:extremedemon:798342589832626196>"
    }
    emoji_star_auto = "<:auto:798342232394301510>"
    emoji_star_featured_difficulty = {
        "0" : "<:unrated:798358095487041566>",
        "10": "<:featured_easy:798542116765958184>",
        "20": "<:featured_normal:798543308641140766>",
        "30": "<:featured_hard:798543343381774337>",
        "40": "<:featured_harder:798543376474964038>",
        "50": "<:featured_insane:798541756001943572>"
    }
    emoji_star_featured_difficulty_demon = {
        "3": "<:featured_easydemon:798543467335647262>",
        "4": "<:featured_mediumdemon:798543508528300032>",
        "0": "<:featured_harddemon:798543571107840001>",
        "5": "<:featured_insanedemon:798543610353811516>",
        "6": "<:featured_extremedemon:798543646399135766>"
    }
    emoji_star_featured_auto = "<:featured_auto:798540563405733898>"
    orignal_song_list = {
        "0": "Stereo Madness",
        "1": "Back On Track",
        "2": "Polargeist",
        "3": "Dry Out",
        "4": "Base After Base",
        "5": "Cant Let Go",
        "6": "Jumper",
        "7": "Time Machine",
        "8": "Cycles",
        "9": "xStep",
        "10": "Clutterfunk",
        "11": "Theory of Everything",
        "12": "Electroman Adventures",
        "13": "Clubstep",
        "14": "Electrodynamix",
        "15": "Hexagon Force",
        "16": "Blast Processing",
        "17": "Thery of Everything 2",
        "18": "Geometrycal Dominator",
        "19": "Deadlocked",
        "20": "Fingerdash",
    }

    cursor = connection.cursor()
    cursor.execute("select * from levels where levelID = %s", [args])
    records = cursor.fetchall()
    connection.commit()

    embed = discord.Embed(title = "Level informations", color = discord.Colour.from_rgb(0, 189, 255))

    if args == "null":
        await ctx.send("You need to type a level id!")
    else:
        if cursor.rowcount == 0:
            await ctx.send("The id that you entered does not exist!")
        else:
            for row in records:

                cursor.execute("select * from songs where ID = %s", [row[13]])
                ehrbgvbcv = cursor.fetchall()
                songName = "Unknown"
                songAuthor = "Unknown"
                if cursor.rowcount > 0:
                    song = ehrbgvbcv[0]
                    songName = str(song[1])
                    songAuthor = str(song[3])
                connection.commit()

                diff = ""
                if int(row[25]) == 1:
                    if int(row[31]) == 1:
                        diff = emoji_star_featured_auto
                    else:
                        diff = emoji_star_auto
                elif int(row[24]) == 1:
                    if int(row[31]) == 1:
                        diff = emoji_star_featured_difficulty_demon[str(row[34])]
                    else:
                        diff = emoji_star_difficulty_demon[str(row[34])]
                else:
                    if int(row[31]) == 1:
                        diff = emoji_star_featured_difficulty[str(row[21])]
                    else:
                        diff = emoji_star_difficulty[str(row[21])]

                lenght = ""
                if int(row[7]) == 0:
                    lenght = "Tiny"
                elif int(row[7]) == 1:
                    lenght = "Short"
                elif int(row[7]) == 2:
                    lenght = "Medium"
                elif int(row[7]) == 3:
                    lenght = "Long"
                elif int(row[7]) == 4:
                    lenght = "XL"
                else:
                    lenght = "Error"

                copy = ""
                if int(row[10]) == 0:
                    copy = "No"
                elif int(row[10]) == 1:
                    copy = "Yes"
                elif int(row[10]) > 1:
                    copy = "Yes with password"
                else:
                    copy = "Error"

                if int(row[13]) == 0:
                    songName = orignal_song_list[str(row[8])]
                    songAuthor = "Original game song"

                embed.add_field(name = row[4] + " " + diff, value = "**Created by:** " + str(row[2]) 
                + " \n " + "**Description:** " + str(base64.b64decode( str(row[5]).replace("_", "=").replace("-", "+") ) )[2:][:-1]
                + " \n " + "**Song:** " + songName
                + " \n " + "**Song author:** " + songAuthor
                + " \n " + "**Objects:** " + str(row[14])
                + " \n " + "**Version:** " + str(row[6])
                + " \n " + "**Original:** " + ("Not copied" if int(row[11]) == 0 else str(row[11]))
                + " \n " + "**Two players:** " + ("No" if int(row[11]) == 0 else "Yes")
                + " \n " + "**LDM:** " + ("No" if int(row[11]) == 0 else "Yes")
                + " \n " + "**Copyable:** " + copy
                + " \n " + "**Stars requested:** " + str(row[16])
                + " \n " + "**Upload date:** " + datetime.utcfromtimestamp(int(row[27])).strftime("(UTC) *%Y/%m/%d **|** %H:%M:%S*")
                + " \n " + "**Last update:** " + datetime.utcfromtimestamp(int(row[28])).strftime("(UTC) *%Y/%m/%d **|** %H:%M:%S*")
                + " \n " + "<:gdstar:798238253500989460> " + ("Not rated" if int(row[26]) == 0 else str(row[26]))
                + " \n " + "<:usercoin:798293582364147752> " + ("No user coins" if int(row[15]) == 0 else str(row[15]))
                + " \n " + "<:time:798323102798053427> " + lenght
                + " \n " + "<:download:798322135659315210> " + str(row[22])
                + " \n " + ("<:dislike:798353417378201600> " if int(row[23]) < 0 else "<:gd_like:767754910867259446> ") + str(row[23]))

                await ctx.send(embed=embed)

@client.command()
async def ping(ctx):
    await ctx.send(f"Current ping is: {round(client.latency * 1000)}ms")

@client.command()
async def refreshcp(ctx):
    await logs(ctx.guild.id, ctx.author.id, "refreshcp")
    serverid = str(ctx.message.guild.id)
    f = open("StatsDatabase.json")
    with open("StatsDatabase.json", "r+") as file2:
        data = json.load(file2)
        ip = data[serverid]["mysqlhost"]
        if ip == "127.0.0.1":
            await ctx.send("Trying to refresh creator points...")
            fulluser = data[serverid]["mysqluser"]
            user = fulluser.replace("gdps_", "")
            f.close() 
            url = "http://ps.fhgdps.com/" + user + "/tools/cron/cron.php"
            urllib.request.urlopen(url)
            await ctx.send("Done!")
        else:
            await ctx.send("Sorry this is only avaliable if you are hosted on the GDPS Free Hosting discord.")

async def get_connection(serverid):
    if serverid in connection_dictionnary:
        connection = connection_dictionnary[serverid]["connection"]
        connection.ping(reconnect=True)
        return connection
    elif await init_connection_from_db(serverid):
        return connection_dictionnary[serverid]["connection"]
    return None

async def get_connection_with_error_message(ctx):
    connection = await get_connection(ctx.message.guild.id)
    if connection is None:
        await ctx.send("You must first link your gdps before using this command!")
        return None
    return connection

def has_connection(serverid):
    return serverid in connection_dictionnary

async def init_connection_from_db(serverid):
    if not has_connection(serverid):
        data = await get_server_data(serverid)
        if data is not None:
            connection = mysql.connector.connect(host='127.0.0.1',
                                                database=data["mysqldatabase"],
                                                user=data["mysqluser"],
                                                password=data["password"])
            connection_dictionnary[serverid] = {"connection": connection}
            return True
    return False

async def logs(server, user, command):
    guild = client.get_guild(server)
    user = await client.fetch_user(user)
    log_channel = client.get_channel(836226760685125662)
    embed = discord.Embed(description = f"Command **{command}** executed by <@{user.id}> ({user.name}) in **{guild.name}**", color = discord.Colour.green())
    await log_channel.send(embed=embed)

client.run(bot_token)
