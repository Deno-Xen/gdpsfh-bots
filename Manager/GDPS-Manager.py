import os
import discord
import mysql.connector
import base64
import requests
import re
import youtube_dl
import urllib.parse
import itertools
import random
import asyncio
from mysql.connector import Error
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
from youtube_dl import YoutubeDL

intents = discord.Intents().default()
intents.members = True
load_dotenv(find_dotenv())
bot_token = os.environ.get("bot_token")
prefix = os.environ.get("prefix")
gdps_host = os.environ.get("gdps_host")
prefix = os.environ.get("prefix")
mysql_ip = os.environ.get("mysql_ip")
mysql_port = os.environ.get("mysql_port")
mysql_database = os.environ.get("mysql_database")
mysql_user = os.environ.get("mysql_user")
mysql_pass = os.environ.get("mysql_pass")
client = commands.Bot(command_prefix = prefix, help_command=None, intents=intents)

database_connection = None
try:
    database_connection = mysql.connector.connect(host=mysql_ip,
                                                  database=mysql_database,
                                                  user=mysql_user,
                                                  port=int(mysql_port),
                                                  password=mysql_pass)
    print("Connected to the DB!")
except:
    print("Couldn't connect to the database.")
    exit()

if database_connection is None:
    exit()

database_connection.autocommit = 1
database_cursor = database_connection.cursor(buffered=True)

connection_dictionary = {}
authorised_list = [195598321501470720]
role_link = {}
command_cooldown = {}

@client.command()
async def link(ctx, option=None, value=None, value2=None, *, value3=None):
    print(f"Command link used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    ownerid = None
    try:
        ownerid = ctx.guild.owner.id
    except:
        await ctx.send("There was an error while trying to get the discord server owner, please try again later. (This is not a bot problem discord is just too slow..)")
        return
    if ctx.author.id != ownerid and ctx.author.id not in authorised_list:
        if ctx.guild.id != 794302606792589395 and ctx.author.id != 701203087532228608:
            embed = discord.Embed(description = "Only the discord server owner can do that.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
    if option is None:
        embed = discord.Embed(title = "Link command usage", description = f"**{prefix}link gdps**: Link your gdps to this discord server \n" +
                                                                          f"**{prefix}link botaccount**: Link a bot account on the gdps to enable account linking \n" +
                                                                          f"**{prefix}link role**: Sync a discord role with a GDPS role (Role list can be found with {prefix}role) \n" +
                                                                          f"**{prefix}link logchannel <channel mention/id>**: Set a log channel for GDPS Manager", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    if not ctx.author.guild_permissions.administrator and ctx.author.id != 195598321501470720:
        embed = discord.Embed(description = "You need the administrator permission to use this command.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    if option == "gdps":
        database_cursor.execute("select * from gdps_manager_serverdata where serverID = %s", [serverid])
        if database_cursor.rowcount == 1:
            await ctx.send("This server is already setup!")
            return
        elif database_cursor.rowcount > 1:
            await ctx.send("There is an error with the configuration, please contact a staff member the GDPS Free Hosting discord.")
            return
        await ctx.send("Is your GDPS hosted by the GDPS Free Hosting server? (yes/no)")
        ishostedbymat = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        ishostedbymat = ishostedbymat.content.lower()
        global gdps_host
        gdps_port = 3306
        patcheduser = None
        patchedurl = None
        userpass = None
        if ishostedbymat == "yes":
            await ctx.send("Do you own the GDPS or is it owned by someone else? (yes/no) > yes=You own it / no=Someone else owns it")
            own_gdps = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            own_gdps = own_gdps.content
            if own_gdps.lower() == "yes":
                database_cursor.execute("select * from gdps_creator_userdata where userID = %s", [ctx.author.id])
                if database_cursor.rowcount == 0:
                    await ctx.send("You don't have a GDPS on GDPS Free Hosting.")
                    return
                gdps_data = database_cursor.fetchall()
                gdps_curl = gdps_data[0][2]
                userpass = gdps_data[0][4]
                patcheduser = f"gdps_{gdps_curl}"
                patchedurl = patcheduser
            elif own_gdps == "no":
                await ctx.send("If you don't own the GDPS then please enter the link command again and respond with no to the first question.")
                return
            else:
                await ctx.send("Not a valid answer.")
                return
        elif ishostedbymat == "no":
            await ctx.send("Ok so first are you in a channel that only you or trusted admins can see? (yes/no)")
            private_channel = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            private_channel = private_channel.content
            if private_channel.lower() != "yes":
                await ctx.send("The setup stopped, please go in a private channel because you will need to enter your database login infos.")
                return
            await ctx.send("What is your GDPS database host? (Example: ps.fhgdps.com) / 7m.pl not supported because they blocked remote connection.")
            gdps_host = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            gdps_host = gdps_host.content
            if gdps_host == "ps.fhgdps.com":
                gdps_host = "127.0.0.1"
            while True:
                if "http://" in gdps_host.lower():
                    await ctx.send("A normal url is not valid, please only put the domain name like in the example.")
                    gdps_host = await client.wait_for('message', check=lambda message: message.author == ctx.author)
                    gdps_host = gdps_host.content
                    continue
                else:
                    break

            await ctx.send("What is your GDPS database port? (Default: 3306)")
            gdps_port = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            gdps_port = gdps_port.content
            while True:
                if gdps_port.isdecimal():
                    break
                await ctx.send("A port needs to be only numbers, enter a valid one.")
                gdps_port = await client.wait_for('message', check=lambda message: message.author == ctx.author)
                gdps_port = gdps_port.content
            await ctx.send("What is your GDPS database name?")
            patchedurl = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            patchedurl = patchedurl.content
            if patchedurl.lower() == "information_schema":
                await ctx.send("information_schema is an axample database you can't link to it.. Enter the setup command again with the right informations.")
                return
            await ctx.send("What is your GDPS database user?")
            patcheduser = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            patcheduser = patcheduser.content
            await ctx.send("What is your GDPS database password?")
            userpass = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            userpass = userpass.content
        elif ishostedbymat == "adminlogin":
            if ctx.author.id != 195598321501470720:
                await ctx.send("You can't use admin login.")
                return
            patcheduser = "sysadmin"
            userpass = "X5J8RGVixv28G22L6esd8k"
            gdps_port = 3306
            await ctx.send("gdps curl")
            gdps_curl = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            patchedurl = "gdps_" + gdps_curl.content
        else:
            await ctx.send("Invalid option.")
            return
        try:
            await ctx.send("Testing connection... If the bot doesn't respond within 10 seconds then it somehow crashed, contact the GDPS Free Hosting support if it crashed.")
            connection = mysql.connector.connect(host=gdps_host,
                                                    database=str(patchedurl),
                                                    user=str(patcheduser),
                                                    port = int(gdps_port),
                                                    password=str(userpass),
                                                    connection_timeout=5)
            if connection.is_connected():
                connection_dictionary[serverid] = {"connection": connection}
                database_cursor.execute("insert into gdps_manager_serverdata (serverID, mysql_host, mysql_port, mysql_database, mysql_user, mysql_password) values (%s, %s, %s, %s, %s, %s)", [ctx.guild.id, gdps_host, connection._port, patchedurl, patcheduser, userpass])

                await ctx.send("Your gdps is now linked to this discord server!")
            else:
                if ishostedbymat == "yes":
                    await ctx.send("Couldn't get the informations of the GDPS linked to your account, try to enter the ps!changepass command on the GDPSFH discord and if that doesn't work then enter the informations manually by responding no to the first link question.")
                    return
                await ctx.send("Your database informations are incorrect, please enter the command again with the right informations")
                return

        except Error as e:
            print(e)
            if ishostedbymat == "yes":
                await ctx.send("Couldn't get the informations of the GDPS linked to your account, try to enter the ps!changepass command on the GDPSFH discord and if that doesn't work then enter the informations manually by responding no to the first link question.")
                return
            await ctx.send("Your database informations are incorrect, please enter the command again with the right informations")
    elif option == "botaccount":
        check = await check_permission(ctx)
        if not check:
            return
        await ctx.send("Are you in a channel that only you or trusted admins can see? (yes/no)")
        private_channel = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        private_channel = private_channel.content
        if private_channel.lower() != "yes":
            await ctx.send("The setup stopped, please go in a private channel because you will need to enter your database login infos.")
            return

        await ctx.send("Enter the bot account name.")
        bot_name = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        bot_name = bot_name.content
        await ctx.send("Enter the bot account password.")
        bot_password = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        bot_password = bot_password.content

        database_cursor.execute("select mysql_database from gdps_manager_serverdata where serverID = %s", [serverid])
        gdps_curl = database_cursor.fetchall()
        gdps_curl = gdps_curl[0][0].replace("gdps_", "")

        url = f"http://ps.fhgdps.com/{gdps_curl}/accounts/loginGJAccount.php"
        data = {"userName": bot_name,
                "password": bot_password,
                "udid": bot_name}
        req = requests.post(url, data=data)
        req = req.text
        errors_list = ["-1", "</html>", "-12"]
        for error in errors_list:
            if error in req:
                await ctx.send("There was a problem linking to the account")
                return
        req_list = req.split(",")
        account_id = req_list[0]

        password = xor_cipher(bot_password, "37526")
        password = password.encode("ascii")
        password = base64.b64encode(password).decode()
        gjp = str(password).replace("/", "_").replace("+", "-")

        database_cursor.execute("update gdps_manager_serverdata set gdps_botaccount_id = %s, gdps_botaccount_gjp = %s where serverID = %s", [account_id, gjp, serverid])
        await ctx.send("Bot account linked!")
    elif option == "role":
        check = await check_permission(ctx)
        if not check:
            return
        roleid = None
        if value == "link":
            try:
                value2 = await commands.RoleConverter().convert(ctx, value2)
                roleid = str(value2.id)
            except:
                embed = discord.Embed(description = "Role not found.", color = discord.Colour.red())
                await ctx.send(embed=embed)
                return
            database_cursor.execute("select id from gdps_manager_rolelink where roleID = %s", [roleid])
            if database_cursor.rowcount >= 1:
                await ctx.send("This role is already linked!")
                return

            connection = await get_connection(serverid)
            if connection is None:
                await ctx.send("There was an error while trying to contact the database.")
                return
            cursor = connection.cursor(buffered=True)

            cursor.execute("select roleName from roles where roleName = %s", [value3])
            if cursor.rowcount == 0:
                await ctx.send("This role doesn't exist on the GDPS.")
                return

            database_cursor.execute("insert into gdps_manager_rolelink (serverID, roleID, gdps_role_name) values (%s, %s, %s)", [serverid, roleid, value3])
            await ctx.send("Role linked!")
            await send_log(serverid, f"{ctx.author.mention} linked the {value2.mention} role to the \"{value3}\" role on the GDPS.")
        elif value == "unlink":
            try:
                value2 = await commands.RoleConverter().convert(ctx, value2)
                roleid = str(value2.id)
            except:
                embed = discord.Embed(description = "Role not found.", color = discord.Colour.red())
                await ctx.send(embed=embed)
                return
            database_cursor.execute("select null from gdps_manager_rolelink where serverID = %s and roleID = %s", [serverid, roleid])
            if database_cursor.rowcount == 0:
                await ctx.send("This role is not linked.")
                return
            database_cursor.execute("delete from gdps_manager_rolelink where serverID = %s and roleID = %s", [serverid, roleid])
            await ctx.send("Role unlinked!")
            await send_log(serverid, f"{ctx.author.mention} unlinked the {value2.mention} role from the GDPS.")
        else:
            embed = discord.Embed(title = "Role link command usage", description = f"**{prefix}link role link <discord role mention/id> <GDPS role name>**: Link a discord role to a GDPS role \n" +
                                                                                   f"**{prefix}link role unlink <discord role mention/id>**: Unlink a discord role", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
    elif option == "logchannel":
        channelid = None
        try:
            value = await commands.TextChannelConverter().convert(ctx, value)
            channelid = value.id
        except:
            embed = discord.Embed(description = "Channel not found.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        database_cursor.execute("update gdps_manager_serverdata set log_channel_id = %s where serverID = %s", [channelid, serverid])
        await ctx.send("Log channel linked!")
    else:
        await ctx.send("Inavlid option.")
        return

@client.command()
async def unlink(ctx):
    print("Command unlink used")
    serverid = ctx.guild.id
    """
    ownerid = ctx.guild.owner.id
    if ctx.author.id != ownerid and ctx.author.id not in authorised_list:
        embed = discord.Embed(description = "Only the discord server owner can do that.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    """
    if not ctx.author.guild_permissions.administrator and ctx.author.id != 195598321501470720:
        embed = discord.Embed(description = "You need the administrator permission to use this command.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    database_cursor.execute("select * from gdps_manager_serverdata where serverID = %s", [serverid])
    if database_cursor.rowcount == 0:
        await ctx.send("This server is not linked yet.")
        return
    database_cursor.execute("delete from gdps_manager_serverdata where serverID = %s", [serverid])
    await ctx.send("Server unlinked!")

@client.command()
async def stats(ctx):
    print(f"Command stats used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    c_serverid = str(ctx.guild.id)
    if str(ctx.guild.id) not in str(command_cooldown):
        command_cooldown[c_serverid] = {"stats": False}
    cooldown = command_cooldown[c_serverid]["stats"]
    if cooldown:
        await ctx.send("This command is on cooldown.")
        return
    command_cooldown[c_serverid]["stats"] = True
    serverid = ctx.guild.id
    connection = await get_connection(serverid)
    if connection is None:
        await ctx.send("There was an error while trying to contact the database.")
        return
    cursor = connection.cursor(buffered=True)
    cursor.execute("select null from accounts")
    registered_users = cursor.rowcount
    cursor.execute("select null from levels")
    levels_count = cursor.rowcount
    cursor.execute("select null from levels where starStars > 0")
    levelsrated_count = cursor.rowcount
    cursor.execute("select null from levels where starFeatured = 1")
    levelsfeatured_count = cursor.rowcount
    cursor.execute("select null from levels where starEpic > 0")
    levelsepic_count = cursor.rowcount
    cursor.execute("select null from songs")
    songs_count = cursor.rowcount
    cursor.execute("select null from acccomments")
    profilemsg_count = cursor.rowcount
    cursor.execute("select null from friendships")
    friendships_count = cursor.rowcount
    cursor.execute("select null from gauntlets")
    gauntlet_count = cursor.rowcount
    cursor.execute("select null from mappacks")
    mappacks_count = cursor.rowcount
    cursor.execute("select null from quests")
    quests_count = cursor.rowcount
    cursor.execute("select null from messages")
    pm_count = cursor.rowcount
    cursor.execute("select null from comments")
    comments_count = cursor.rowcount
    embed = discord.Embed(title = "GDPS Stats", description = f"Registered accounts: {registered_users} \n" +
                                                              f"Total amount of levels: {levels_count} \n" +
                                                              f"Total amount of rated levels: {levelsrated_count} \n" +
                                                              f"Total amount of featured levels: {levelsfeatured_count} \n" +
                                                              f"Total amount of epic levels: {levelsepic_count} \n" +
                                                              f"Total amount of songs: {songs_count} \n" +
                                                              f"Total profile messages sent: {profilemsg_count}\n" +
                                                              f"Total friendships: {friendships_count} \n" +
                                                              f"Gauntlet amount: {gauntlet_count} \n" +
                                                              f"Map packs amount: {mappacks_count} \n" +
                                                              f"Quests amount: {quests_count} \n" +
                                                              f"Total private messages sent: {pm_count} \n" +
                                                              f"Total amount of level comments: {comments_count}", color = discord.Colour.green())
    await ctx.send(embed=embed)
    count = 20
    while count > 0:
        await asyncio.sleep(1)
        count -= 1
    command_cooldown[c_serverid]["stats"] = False
    
@client.command()
async def selfacc(ctx, option=None, value=None, value2=None):
    serverid = ctx.guild.id
    database_cursor.execute("select mysql_database,gdps_botaccount_id,gdps_botaccount_gjp from gdps_manager_serverdata where serverID = %s", [serverid])
    if database_cursor.rowcount == 0:
        await ctx.send("This server is not linked yet.")
        return
    print(f"Command selfacc used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    bot_data = database_cursor.fetchall()[0]
    if bot_data[1] is None:
        await ctx.send("Not botaccount linked yet, this command only works if the discord server owners linked a bot account to GDPS Manager.")
        return
    if option is None or option == "help":
        embed = discord.Embed(title="Self account command help", description = f"**{prefix}selfacc link <in game name>**: Link your discord account to your GDPS account\n"
                                                                             + f"**{prefix}selfacc unlink**: Unlink your discord account to your GDPS account\n"
                                                                             + f"**{prefix}selfacc changepass**: Change the password of your GDPS account\n"
                                                                             + f"**{prefix}selfacc changename**: Change the name of your GDPS account\n"
                                                                             + f"**{prefix}selfacc forcelink**: Force link a user to a GDPS account without validation (Admin only)", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    connection = await get_connection(serverid)
    if connection is None:
        await ctx.send("There was an error while trying to contact the database.")
        return
    cursor = connection.cursor(buffered=True)
    if option == "link":
        database_cursor.execute("select ingame_name from gdps_manager_acclink where serverID = %s and userID = %s", [serverid, ctx.author.id])
        if database_cursor.rowcount > 0:
            ingame_name = database_cursor.fetchall()[0][0]
            await ctx.send(f"You are already linked to an account on the GDPS. (In game name: {ingame_name})")
            return
        cursor.execute("select accountID from accounts where userName = %s", [value])
        if cursor.rowcount == 0:
            await ctx.send("This account doesn't exist on the GDPS.")
            return
        target_accid = cursor.fetchall()[0][0]

        gdps_curl = bot_data[0].replace("gdps_", "")
        bot_password = bot_data[2]
        bot_id = bot_data[1]

        link_code = random.randint(100000, 999999)

        message = xor_cipher(f"If you never did a link request please ignore this message. link code: {link_code}", "14251")
        message = message.encode("ascii")
        url = f"http://ps.fhgdps.com/{gdps_curl}/uploadGJMessage20.php"
        data = {"gjp": bot_password,
                "subject": base64.b64encode(b"Account linking").decode(),
                "toAccountID": int(target_accid),
                "accountID": int(bot_id),
                "body": base64.b64encode(message).decode(),
                "secret": "Wmfd2893gb7"}
        req = requests.post(url, data=data)
        if req.text != "1":
            await ctx.send("There was an error while trying to send the in game message.")
            return

        await ctx.send("Enter the code you recieved in private messages on the GDPS.")
        link_code_confirmation = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        link_code_confirmation = link_code_confirmation.content
        if link_code_confirmation != str(link_code):
            await ctx.send("Invalid code, please try again.")
            return

        database_cursor.execute("insert into gdps_manager_acclink (serverID, userID, ingame_name) values (%s, %s, %s)", [serverid, ctx.author.id, value])
        if str(serverid) in str(role_link):
            if str(ctx.author.id) in str(role_link[str(serverid)]):
                if role_link[str(serverid)][str(ctx.author.id)] == 0:
                    role_link[str(serverid)][str(ctx.author.id)] = {"ingame_name": value}
        await ctx.send("Account linked!")
        await send_log(serverid, f"{ctx.author.mention} linked to the account \"{value}\" on the GDPS.")
    elif option == "forcelink":
        if not ctx.author.guild_permissions.administrator:
            embed = discord.Embed(description = "You need the administrator permission to use this command.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        userid = None
        try:
            value = await commands.MemberConverter().convert(ctx, value)
            userid = str(value.id)
        except:
            embed = discord.Embed(description = "Can't find this user.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("select userName from accounts where userName = %s", [value2])
        if cursor.rowcount == 0:
            await ctx.send("This account doesn't exist in the gdps.")
            return
        database_cursor.execute("insert into gdps_manager_acclink (serverID, userID, ingame_name) values (%s, %s, %s)", [serverid, userid, value2])
        await send_log(serverid, f"{ctx.author.mention} force linked {value.mention} to the account \"{value2}\" on the GDPS.")
        await ctx.send("Account forced linked!")
    elif option == "unlink":
        database_cursor.execute("select ingame_name from gdps_manager_acclink where serverID = %s and userID = %s", [serverid, ctx.author.id])
        if database_cursor.rowcount == 0:
            await ctx.send("You are not linked to any account on the GDPS.")
            return
        database_cursor.execute("delete from gdps_manager_acclink where serverID = %s and userID = %s", [serverid, ctx.author.id])
        await send_log(serverid, f"{ctx.author.mention} unlinked their GDPS account.")
        await ctx.send("Account unlinked!")
    elif option == "changepass":
        database_cursor.execute("select ingame_name from gdps_manager_acclink where serverID = %s and userID = %s", [serverid, ctx.author.id])
        if database_cursor.rowcount == 0:
            await ctx.send("You are not linked to any account on the GDPS.")
            return
        acc_name = database_cursor.fetchall()[0][0]
        try:
            await ctx.author.send("Enter your new password")
        except:
            await ctx.send("You have private messages disabled, please enable them and try again.")
            return
        await ctx.send("Check your private messages to change your password.")
        def check(m):
            return m.author == ctx.message.author and m.guild is None

        new_password = await client.wait_for('message', check=check)
        new_password = new_password.content
        if len(new_password) < 6:
            await ctx.author.send("The password is too short, the minimum is 6 characters.")
            return
        elif len(new_password) > 20:
            await ctx.author.send("The password length is too long, the maximum is 20 characters.")
            return

        url = "http://ps.fhgdps.com/tools/hashpass.php"
        data = {"password": new_password}
        req = requests.post(url, data=data)
        req = req.text
        if req is None:
            await ctx.author.send("An error occured.")
            return
        cursor.execute("update accounts set password = %s where userName = %s", [req, acc_name])
        connection.commit()
        await send_log(serverid, f"{ctx.author.mention} changed their GDPS account password.")
        await ctx.author.send("Password updated!")
    elif option == "changename":
        await ctx.send("Not completly stable yet so disabled for now.")
        return
        database_cursor.execute("select ingame_name from gdps_manager_acclink where serverID = %s and userID = %s", [serverid, ctx.author.id])
        if database_cursor.rowcount == 0:
            await ctx.send("You are not linked to any account on the GDPS.")
            return
        acc_name = database_cursor.fetchall()[0][0]

        await ctx.send("Before you change your name please save and unlink your account because if you don't do that it will create problems for your account. After that just type \"next\" to continue with the name change.")
        confirmation = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        confirmation = confirmation.content
        if confirmation != "next":
            await ctx.send("Invalid answer, cancelling name change.")
            return

        await ctx.send("Type the new name you want to have.")
        new_name = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        new_name = new_name.content

        cursor.execute("select userName from accounts where userName = %s", [new_name])
        if cursor.rowcount > 0:
            await ctx.send("This name is already taken, please choose another one.")
            return

        cursor.execute("update acccomments set userName = %s where userName = %s", [new_name, acc_name])
        cursor.execute("update accounts set userName = %s where userName = %s", [new_name, acc_name])
        cursor.execute("update actions set value = %s where value = %s", [new_name, acc_name])
        cursor.execute("update comments set userName = %s where userName = %s", [new_name, acc_name])
        cursor.execute("update levels set userName = %s where userName = %s", [new_name, acc_name])
        cursor.execute("update messages set userName = %s where userName = %s", [new_name, acc_name])
        cursor.execute("update suggest set suggestBy = %s where suggestBy = %s", [new_name, acc_name])
        cursor.execute("update users set userName = %s where userName = %s and ", [new_name, acc_name])
        connection.commit()
        database_cursor.execute("update gdps_manager_acclink set ingame_name = %s where ingame_name = %s", [new_name, acc_name])
        await send_log(serverid, f"{ctx.author.mention} changed their GDPS account name from {acc_name} to {new_name}.")
        await ctx.send("Name updated!")
    else:
        await ctx.send("Invalid option.")
        return

@client.command()
async def whitelist(ctx, arg1=None, mention="null"):
    print(f"Command whitelist used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    """
    ownerid = ctx.guild.owner.id
    if ctx.author.id != ownerid and ctx.author.id not in authorised_list:
        embed = discord.Embed(description = "Only the discord server owner can do that.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    """
    if not ctx.author.guild_permissions.administrator:
        embed = discord.Embed(description = "You need the administrator permission to use this command.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    database_cursor.execute("select * from gdps_manager_serverdata where serverID = %s", [serverid])
    if database_cursor.rowcount == 0:
        await ctx.send("This server is not linked yet.")
        return
    if arg1 is None or arg1 == "help":
        embed = discord.Embed(title="Whitelist command help", description = f"**{prefix}whitelist adduser <user mention>**: Give the permission to use commands\n"
                                                                          + f"**{prefix}whitelist rmuser <user mention>**: Removes the permission to use commands\n"
                                                                          + f"**{prefix}whitelist addrole <role mention>**: Give the permission to use commands to all user that have this role\n"
                                                                          + f"**{prefix}whitelist rmrole <role mention>**: Removes the permission to use commands to all user that have this role", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    elif arg1 == "adduser":
        try:
            user = await commands.MemberConverter().convert(ctx, mention)
            userid = str(user.id)
        except:
            embed = discord.Embed(description = "Can't find this user.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        database_cursor.execute("select typeID from gdps_manager_whitelist where serverID = %s and type = 'user'", [serverid])
        whitelisted_users = database_cursor.fetchall()
        if userid in str(whitelisted_users):
            embed = discord.Embed(description = "This user already has permissions!", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        else:
            database_cursor.execute("insert into gdps_manager_whitelist (type, serverID, typeID) values ('user', %s, %s)", [serverid, user.id])
            embed = discord.Embed(description = "This user can now use commands!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
    elif arg1 == "rmuser":
        try:
            user = await commands.MemberConverter().convert(ctx, mention)
            userid = str(user.id)
        except:
            embed = discord.Embed(description = "Can't find this user.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        database_cursor.execute("select typeID from gdps_manager_whitelist where serverID = %s and type = 'user'", [serverid])
        whitelisted_users = database_cursor.fetchall()
        if userid in str(whitelisted_users):
            database_cursor.execute("delete from gdps_manager_whitelist where serverID = %s and type = 'user' and typeID = %s", [serverid, userid])
            embed = discord.Embed(description = "This user no longer has permissions!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(description = "This user never had permissions!", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
    elif arg1 == "addrole":
        try:
            role = await commands.RoleConverter().convert(ctx, mention)
            roleid = str(role.id)
        except:
            embed = discord.Embed(description = "Channel not found.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        database_cursor.execute("select typeID from gdps_manager_whitelist where serverID = %s and type = 'role'", [serverid])
        whitelisted_roles = database_cursor.fetchall()
        if roleid in str(whitelisted_roles):
            embed = discord.Embed(description = "This role already has permissions!", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        else:
            database_cursor.execute("insert into gdps_manager_whitelist (type, serverID, typeID) values ('role', %s, %s)", [serverid, roleid])
            embed = discord.Embed(description = "All the users that have this role can now use commands!", color = discord.Colour.green())
            await ctx.send(embed=embed)
    elif arg1 == "rmrole":
        try:
            role = await commands.RoleConverter().convert(ctx, mention)
            roleid = str(role.id)
        except:
            embed = discord.Embed(description = "Channel not found.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        database_cursor.execute("select typeID from gdps_manager_whitelist where serverID = %s and type = 'role'", [serverid])
        whitelisted_roles = database_cursor.fetchall()
        if roleid in str(whitelisted_roles):
            database_cursor.execute("delete from gdps_manager_whitelist where serverID = %s and type = 'role' and typeID = %s", [serverid, roleid])
            embed = discord.Embed(description = "All the users that have this role can no longer use commands!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(description = "This role never had permissions!", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
    else:
        embed = discord.Embed(description = "Invalid option.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return

@client.command()
async def role(ctx, username = None, *, role_name = None):
    print(f"Command role used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    check = await check_permission(ctx)
    if not check:
        return
    if username is None:
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("select roleName from roles")
        roles = cursor.fetchall()
        roles_list = []
        for keys in roles:
            roles_list.append(keys[0] + "\n")
        real_list = "".join(map(str, roles_list))
        if cursor.rowcount == 0:
            roles_list = "You don't have any roles on your GDPS."
        embed = discord.Embed(title = "Role command usage", description = f"Use this command like this: {prefix}role <ingame name> <role> \n\n**Roles on your GDPS:** \n{real_list}", color = discord.Colour.green())
        await ctx.send(embed=embed)
        return
    if role_name is None:
        await ctx.send(f"You need to specify a role, enter the {prefix}role to have a list of avaliable roles")
        return
    connection = await get_connection(serverid)
    if connection is None:
        await ctx.send("There was an error while trying to contact the database.")
        return
    cursor = connection.cursor(buffered=True)
    cursor.execute("select accountID from accounts where userName = %s", [username])
    accid = cursor.fetchall()
    if cursor.rowcount == 0:
        await ctx.send("The account that you entered does not exist!")
        return
    cursor.execute("select roleID from roles where roleName = %s", [role_name])
    roleid = cursor.fetchall()
    if cursor.rowcount == 0:
        await ctx.send("The role that you entered does not exist!")
        return
    connection.commit()
    cursor.execute("select * from roleassign where accountID = %s", [accid[0][0]])
    if cursor.rowcount == 1:
        cursor.execute("update roleassign set roleID = %s where accountID = %s", [roleid[0][0], accid[0][0]])
        connection.commit()
        await ctx.send("User role set!")
        return
    elif cursor.rowcount > 1:
        await ctx.send("You messed up your database, your fault that its not working")
        return
    else:
        cursor.execute("insert into roleassign (roleID, accountID) values (%s, %s)", [roleid[0][0], accid[0][0]])
        connection.commit()
        await ctx.send("User role set!")
        return

@client.command()
async def modifylevel(ctx, levelid = None, stat = None, *, value = None):
    print(f"Command modifylevel used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    check = await check_permission(ctx)
    if not check:
        return
    if levelid is None:
        if ctx.guild.id == 794302606792589395:
            embed = discord.Embed(title = "Modifylevel command usage", description = f"Use this command like this: {prefix}modifylevel <levelid> <option> <value> \n\n**Options:** \ndownloads <amount> \nlikes <amount> \nstars <amount> \nlength <tiny/short/medium/long/xl> \nname <text> \ndescription <text> \ndifficulty <difficulty name> \nchangeowner <ingame name> \nfeature \nunfeature \nepic \nunepic \nlegendary \nunlegendary \nlist \nunlist", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(title = "Modifylevel command usage", description = f"Use this command like this: {prefix}modifylevel <levelid> <option> <value> \n\n**Options:** \ndownloads <amount> \nlikes <amount> \nstars <amount> \nlength <tiny/short/medium/long/xl> \nname <text> \ndescription <text> \ndifficulty <difficulty name> \nchangeowner <ingame name> \nfeature \nunfeature \nepic \nunepic \nlist \nunlist", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
    connection = await get_connection(serverid)
    if connection is None:
        await ctx.send("There was an error while trying to contact the database.")
        return
    cursor = connection.cursor(buffered=True)
    cursor.execute("select gameVersion from levels where levelID = %s", [levelid])
    if cursor.rowcount == 0:
        await ctx.send("The level that you entered does not exist!")
        return
    try:
        if stat == "downloads":
            cursor.execute("update levels set downloads = %s where levelID = %s", (int(value), int(levelid)))
        elif stat == "likes":
            cursor.execute("update levels set likes = %s where levelID = %s", (int(value), int(levelid)))
        elif stat == "stars":
            cursor.execute("update levels set starStars = %s where levelID = %s", (int(value), int(levelid)))
        elif stat == "length":
            if value.lower() == "tiny":
                length_value = 0
            elif value.lower() == "short":
                length_value = 1
            elif value.lower() == "medium":
                length_value = 2
            elif value.lower() == "long":
                length_value = 3
            elif value.lower() == "xl":
                length_value = 4
            else:
                await ctx.send("Invalid length value.")
                return
            cursor.execute("update levels set levelLength = %s where levelID = %s", (length_value, int(levelid)))
        elif stat == "name":
            cursor.execute("update levels set levelName = %s where levelID = %s", (value, int(levelid)))
        elif stat == "description":
            string_bytes = value.encode("ascii")
            base64_bytes = base64.b64encode(string_bytes)
            base64_string = base64_bytes.decode("ascii")
            cursor.execute("update levels set levelDesc = %s where levelID = %s", (base64_string, int(levelid)))
        elif stat == "difficulty":
            if value is None:
                embed = discord.Embed(title="Avaliable difficulties", description="NA \nEasy \nNormal \nHard \nHarder \nInsane \nEasy demon \nMedium demon \nHard demon \nInsane demon \nExtreme demon", color=discord.Colour.green())
                await ctx.send(embed=embed)
                return
            value = value.lower()
            demon = False
            auto = False
            if value == "na":
                value = 0
            elif value == "auto":
                auto = True
            elif value == "easy":
                value = 10
            elif value == "normal":
                value = 20
            elif value == "hard":
                value = 30
            elif value == "harder":
                value = 40
            elif value == "insane":
                value = 50
            elif value == "easy demon":
                value = 3
                demon = True
            elif value == "medium demon":
                value = 4
                demon = True
            elif value == "hard demon":
                value = 0
                demon = True
            elif value == "insane demon":
                value = 5
                demon = True
            elif value == "extreme demon":
                value = 6
                demon = True
            else:
                embed = discord.Embed(description="Invalid difficulty. Enter \"m!modifylevel <level id> difficulty\" to get a list of avaliable difficulties.", color=discord.Colour.red())
                await ctx.send(embed=embed)
                return
            if demon:
                cursor.execute("update levels set starDemon = 1 where levelID = %s", [int(levelid)])
                cursor.execute("update levels set starDemonDiff = %s where levelID = %s", (int(value), int(levelid)))
            elif auto:
                cursor.execute("update levels set starAuto = 1 where levelID = %s", [int(levelid)])
            else:
                cursor.execute("update levels set starDemon = 0 where levelID = %s", [int(levelid)])
                cursor.execute("update levels set starAuto = 0 where levelID = %s", [int(levelid)])
                cursor.execute("update levels set starDifficulty = %s where levelID = %s", (int(value), int(levelid)))
        elif stat == "feature":
            cursor.execute("update levels set starFeatured = 1 where levelID = %s", [int(levelid)])
        elif stat == "unfeature":
            cursor.execute("update levels set starFeatured = 0 where levelID = %s", [int(levelid)])
        elif stat == "epic":
            cursor.execute("update levels set starEpic = 1 where levelID = %s", [int(levelid)])
        elif stat == "unepic":
            cursor.execute("update levels set starEpic = 0 where levelID = %s", [int(levelid)])
        elif stat == "changeowner":
            cursor.execute("select accountID from accounts where userName = %s", [value])
            user_accountid = cursor.fetchall()
            if cursor.rowcount == 0:
                await ctx.send("This user doesn't exist.")
                return
            cursor.execute("select userID from users where extID = %s", [user_accountid[0][0]])
            user_userid = cursor.fetchall()
            cursor.execute("update levels set extID = %s where levelID = %s", [user_accountid[0][0], int(levelid)])
            cursor.execute("update levels set userID = %s where levelID = %s", [user_userid[0][0], int(levelid)])
            cursor.execute("update levels set userName = %s where levelID = %s", [value, int(levelid)])
        elif stat == "legendary":
            if ctx.guild.id == 794302606792589395:
                cursor.execute("update levels set starEpic = 2 where levelID = %s", [int(levelid)])
            else:
                await ctx.send("invalid stat")
                return
        elif stat == "unlegendary":
            if ctx.guild.id == 794302606792589395:
                cursor.execute("update levels set starEpic = 0 where levelID = %s", [int(levelid)])
            else:
                await ctx.send("invalid stat")
                return
        elif stat == "list":
            cursor.execute("update levels set unlisted = 0 where levelID = %s", [int(levelid)])
        elif stat == "unlist":
            cursor.execute("update levels set unlisted = 1 where levelID = %s", [int(levelid)])
        else:
            await ctx.send("invalid stat")
            return
        connection.commit()
        await ctx.send("Level modified!")
    except Exception as e:
        print(e)
        await ctx.send("An error occured.")

@client.command()
async def song(ctx, option = None, songid = None):
    print(f"Command song used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    check = await check_permission(ctx)
    if not check:
        return
    if option is None or option == "help":
        embed = discord.Embed(title="Song command help", description = f"**{prefix}song disable <song id>**: Disable a specific song\n"
                                                                     + f"**{prefix}song enable <song id>**: Enable a specific song\n", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    if songid is None:
        await ctx.send("You need to type a song id.")
        return
    connection = await get_connection(serverid)
    if connection is None:
        await ctx.send("There was an error while trying to contact the database.")
        return
    cursor = connection.cursor(buffered=True)
    cursor.execute("select isDisabled from songs where ID = %s", [songid])
    if cursor.rowcount == 0:
        await ctx.send("The song id that you entered does not exist!")
        return
    banned = cursor.fetchall()
    if option == "disable":
        if banned[0][0] == 1:
            await ctx.send("Song is already disabled.")
            return
        cursor.execute("update songs set isDisabled = 1 where ID = %s", [songid])
        await ctx.send("Song is now disabled!")
    elif option == "enable":
        if banned[0][0] == 0:
            await ctx.send("Song is already enabled.")
            return
        cursor.execute("update songs set isDisabled = 0 where ID = %s", [songid])
        await ctx.send("Song is now enabled!")
    else:
        await ctx.send("Invalid option.")
        return
    connection.commit()

@client.command()
async def reupload(ctx, option = None, value = None, value2 = None):
    print(f"Command reupload used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    check = await check_permission(ctx)
    if not check:
        return
    if option is None or option == "help":
        embed = discord.Embed(title="Reupload command help", description = f"**{prefix}reupload level <level id>**: Reupload a specific level from the original GD server\n" +
                                                                            f"**{prefix}reupload song <song link>**: Reupload a song (Direct links and youtube links accepted)", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    url = None
    database_cursor.execute("select * from gdps_manager_serverdata where serverID = %s", [serverid])
    server_data = database_cursor.fetchall()
    if server_data[0][1] == "127.0.0.1" or server_data[0][1] == "51.178.100.81":
        curl = server_data[0][3]
        patched_curl = curl.replace("gdps_", "")
        if option == "level":
            if value is None:
                await ctx.send("You need to enter a level id!")
                return
            url = f"http://ps.fhgdps.com/{patched_curl}{server_data[0][6]}"
            headers = {"User-Agent": "-"}
            data = {"levelid": value,
                    "server": "http://www.boomlings.com/database/downloadGJLevel22.php"}
            req = requests.post(url, data=data, headers=headers)
            if "Level reuploaded" in str(req.text):
                await ctx.send("Level reuploaded!")
                return
            elif "This level doesn't exist" in str(req.text):
                await ctx.send("This level doesn't exist on the official GD server.")
                return
            else:
                await ctx.send("An error occured.")
                return
        elif option == "song":
            if value is None:
                await ctx.send("You need to enter a song link!")
                return
            if "https://www.youtube.com/" in value or "https://youtu.be/" in value:
                log_channel = client.get_channel(810073425103028294)
                uploaderid = ctx.message.author.id
                song_name = checktitle(value)
                real_name = song_name.replace(":", " -")
                send_link = urllib.parse.quote(song_name.replace(":", " -"), safe='')
                song_list = os.listdir("/var/www/gdps/songs/")
                if str(real_name) not in str(song_list):
                    await ctx.send("Reuploading song please wait...")
                    dlvid = await downloadvid(value)
                    if dlvid == "toolong":
                        await ctx.send("This video is too long, the maximum is 10 minutes")
                        return
                    value = f"http://ps.fhgdps.com/songs/{send_link}.mp3"
                    await log_channel.send("<@" + str(uploaderid) + "> Reuploaded: " + video_title)

            url = f"http://ps.fhgdps.com/{patched_curl}{server_data[0][7]}"
            headers = {"User-Agent": "-"}
            data = {"songlink": value}
            req = requests.post(url, data=data, headers=headers)
            if "song reuploaded" in str(req.text).lower():
                line = req.text.replace(" ", "")
                alphanumeric = ""
                for character in line:
                    if character.isalnum():
                        alphanumeric += character
                get_id = re.search('reuploadedb(.*)bhr', alphanumeric)
                id = str(get_id.group(1))
                await ctx.send(f"Song reuploaded! ID: {id}")
                return
            elif "This song is neither downloadable" in str(req.text):
                await ctx.send("This song couldn't be reuploaded, is this was a youtube link please make a ticket on the GDPS Free Hosting discord.")
                return
            elif "This song already exists" in str(req.text):
                await ctx.send("This song is already reuploaded.")
                return
            else:
                await ctx.send("An error occured.")
                return
        elif option == "changepath":
            if value2 is None:
                await ctx.send("You need to type a file path!")
                return
            if value == "song":
                database_cursor.execute("update gdps_manager_serverdata set songreupload_path = %s where serverID = %s", [value2, ctx.guild.id])
                database_connection.commit()
            elif value == "levelreup":
                database_cursor.execute("update gdps_manager_serverdata set levelreupload_path = %s where serverID = %s", [value2, ctx.guild.id])
                database_connection.commit()
            else:
                await ctx.send("Invalid option.")
                return
            await ctx.send("Path changed!")
        else:
            await ctx.send("Invalid option.")
    else:
        await ctx.send("The reupload feature doesn't currently support external servers.")
        return

@client.command()
async def mappack(ctx, option = None, value = None, *, value2 = None):
    print(f"Command mappack used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    check = await check_permission(ctx)
    if not check:
        return
    if option is None or option == "help":
        embed = discord.Embed(title="Map pack command help", description = f"**{prefix}mappack create**: Create a map pack\n" +
                                                                           f"**{prefix}mappack delete**: Delete a map pack\n"
                                                                           f"**{prefix}mappack list**: List every map packs on your GDPS\n" +
                                                                           f"**{prefix}mappack modify**: Modify any parameters of a map pack", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    if option == "create":
        embed = discord.Embed(description="Enter the name of the pack you want to create", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        pack_name = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        pack_name = pack_name.content

        embed = discord.Embed(description="Enter level IDs you want to be in it. (Note: You need to seperate it with a comma \",\". You can add as many as you want. Example: 25,45,9,36,4)", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        pack_levels = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        pack_levels = pack_levels.content

        embed = discord.Embed(description="Enter the amount of stars you want to get when completing the map pack.", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        pack_stars = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        pack_stars = pack_stars.content

        embed = discord.Embed(description="Enter the amount of gold coins you want to get when completing the map pack.", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        pack_coins = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        pack_coins = pack_coins.content

        embed = discord.Embed(description="Enter the main difficulty for the map pack \n\n**Avaliable answers:** \neasy \nnormal \nhard \nharder \ninsane \ndemon", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        while True:
            pack_difficulty = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            pack_difficulty = pack_difficulty.content.lower()
            if pack_difficulty == "easy":
                pack_difficulty = 1
            elif pack_difficulty == "normal":
                pack_difficulty = 2
            elif pack_difficulty == "hard":
                pack_difficulty = 3
            elif pack_difficulty == "harder":
                pack_difficulty = 4
            elif pack_difficulty == "insane":
                pack_difficulty = 5
            elif pack_difficulty == "demon":
                pack_difficulty = 6
            else:
                await ctx.send("Invalid difficulty, please enter it again.")
                continue
            break

        embed = discord.Embed(description="Enter the main color for the map pack \n\n**Avaliable answers:** \nred \ndark blue \nlight blue \ncyan \norange \ngreen \nblack \nyellow \ngrey \n\nIf you want other colors you can enter \"custom\" for your custom RGB color.", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        pack_color = None
        while True:
            pack_color = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            pack_color = pack_color.content
            if pack_color == "red":
                pack_color = "255,0,0"
            elif pack_color == "dark blue":
                pack_color = "0,0,255"
            elif pack_color == "light blue":
                pack_color = "0,171,255"
            elif pack_color == "cyan":
                pack_color = "51,255,255"
            elif pack_color == "orange":
                pack_color = "255,128,0"
            elif pack_color == "green":
                pack_color = "0,128,0"
            elif pack_color == "black":
                pack_color = "0,0,0"
            elif pack_color == "yellow":
                pack_color = "255,255,0"
            elif pack_color == "grey":
                pack_color = "128,128,128"
            elif pack_color == "custom":
                embed = discord.Embed(description="Type the custom RGB color that you want exactly like the example, if you don't enter exactly the form in the example the color won't work. \n\n**Example for orange:** 255,128,0", color = discord.Colour.from_rgb(255, 128, 0))
                await ctx.send(embed=embed)
                pack_color = await client.wait_for('message', check=lambda message: message.author == ctx.author)
                pack_color = pack_color.content
            else:
                await ctx.send("Invalid answer, please enter it again.")
                continue
            break

        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("insert into mappacks (name, levels, stars, coins, difficulty, rgbcolors) values (%s, %s, %s, %s, %s, %s)", [pack_name, pack_levels, pack_stars, pack_coins, pack_difficulty, pack_color])
        connection.commit()
        await ctx.send("Should be good!")
    elif option == "delete":
        if value is None:
            await ctx.send("You need to enter a map pack ID. (Map packs ids can be found in m!mappack list)")
            return
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("select ID from mappacks where ID = %s", [value])
        if cursor.rowcount == 0:
            await ctx.send("Map pack ID not found. Enter the \"m!mappack list\" command to see a list of avaliable map packs.")
            return
        cursor.execute("delete from mappacks where ID = %s", [value])
        connection.commit()
        embed = discord.Embed(description="Map pack deleted!", color = discord.Colour.green())
        await ctx.send(embed=embed)
    elif option == "list":
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("select * from mappacks")
        quest_list = cursor.fetchall()
        maplist = []
        for mappacks in quest_list:
            maplist.append(f"Pack name: {mappacks[1]} \nPack ID: {mappacks[0]} \n\n")
        embed = discord.Embed(title="Map packs on your GDPS", description="".join(map(str, maplist)), color = discord.Colour.green())
        await ctx.send(embed=embed)
    elif option == "modify":
        if value is None or value == "help":
            embed = discord.Embed(title="Map pack modify command help", description = f"Use this command like this: m!mappack modify <option> <pack name> \n\n**Map pack options:** \nname \nstars_amount \ncoins_amount \ndifficulty \ncolor", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("select ID from mappacks where name = %s", [value2])
        if cursor.rowcount == 0:
            await ctx.send("Map pack not found. Enter the \"m!quest list\" command to see a list of avaliable quests.")
            return
        elif cursor.rowcount > 1:
            await ctx.send("You have multiple map packs with the same name, the bot doesn't support that currently.")
            return
        value2 = value2.lower()
        if value == "name":
            embed = discord.Embed(description="What do you want the new name to be?", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            pack_newname = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            pack_newname = pack_newname.content
            cursor.execute("update mappacks set name = %s where name = %s", [pack_newname, value2])
            connection.commit()
            embed = discord.Embed(description="Map pack name updated!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
        elif value == "stars_amount":
            embed = discord.Embed(description="How much stars should they get when completing the map pack?", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            pack_reward = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            pack_reward = pack_reward.content
            try:
                quest_reward = int(pack_reward)
            except:
                await ctx.send("The amount needs to be a number.")
                return
            cursor.execute("update mappacks set stars = %s where name = %s", [quest_reward, value2])
            connection.commit()
            embed = discord.Embed(description="Map pack reward amount updated!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
        elif value == "coins_amount":
            embed = discord.Embed(description="How much gold coins should they get when completing the map pack?", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            pack_reward = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            pack_reward = pack_reward.content
            try:
                quest_reward = int(pack_reward)
            except:
                await ctx.send("The amount needs to be a number.")
                return
            cursor.execute("update mappacks set coins = %s where name = %s", [quest_reward, value2])
            connection.commit()
            embed = discord.Embed(description="Map pack reward amount updated!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
        elif value == "difficulty":
            embed = discord.Embed(description="Enter the main difficulty for the map pack \n\n**Avaliable answers:** \neasy \nnormal \nhard \nharder \ninsane \ndemon", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            pack_difficulty = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            pack_difficulty = pack_difficulty.content.lower()
            if pack_difficulty == "easy":
                pack_difficulty = 1
            elif pack_difficulty == "normal":
                pack_difficulty = 2
            elif pack_difficulty == "hard":
                pack_difficulty = 3
            elif pack_difficulty == "harder":
                pack_difficulty = 4
            elif pack_difficulty == "insane":
                pack_difficulty = 5
            elif pack_difficulty == "demon":
                pack_difficulty = 6
            else:
                await ctx.send("Invalid difficulty, please enter it again.")
                return
            cursor.execute("update mappacks set difficulty = %s where name = %s", [pack_difficulty, value2])
            connection.commit()
            embed = discord.Embed(description="Map pack difficulty updated!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
        elif value == "color":
            embed = discord.Embed(description="Enter the main color for the map pack \n\n**Avaliable answers:** \nred \ndark blue \nlight blue \ncyan \norange \ngreen \nblack \nyellow \ngrey \n\nIf you want other colors you can enter \"custom\" for your custom RGB color.", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            pack_color = None
            pack_color = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            pack_color = pack_color.content
            if pack_color == "red":
                pack_color = "255,0,0"
            elif pack_color == "dark blue":
                pack_color = "0,0,255"
            elif pack_color == "light blue":
                pack_color = "0,171,255"
            elif pack_color == "cyan":
                pack_color = "51,255,255"
            elif pack_color == "orange":
                pack_color = "255,128,0"
            elif pack_color == "green":
                pack_color = "0,128,0"
            elif pack_color == "black":
                pack_color = "0,0,0"
            elif pack_color == "yellow":
                pack_color = "255,255,0"
            elif pack_color == "grey":
                pack_color = "128,128,128"
            elif pack_color == "custom":
                embed = discord.Embed(description="Type the custom RGB color that you want exactly like the example, if you don't enter exactly the form in the example the color won't work. \n\n**Example for orange:** 255,128,0", color = discord.Colour.from_rgb(255, 128, 0))
                await ctx.send(embed=embed)
                pack_color = await client.wait_for('message', check=lambda message: message.author == ctx.author)
                pack_color = pack_color.content
            else:
                await ctx.send("Invalid answer, please enter it again.")
                return
            cursor.execute("update mappacks set rgbcolors = %s where name = %s", [pack_color, value2])
            connection.commit()
            embed = discord.Embed(description="Map pack color updated!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
    else:
        await ctx.send("Invalid option.")
        return

@client.command()
async def quest(ctx, option = None, value = None, *, value2 = None):
    print(f"Command quest used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    check = await check_permission(ctx)
    if not check:
        return
    if option is None or option == "help":
        embed = discord.Embed(title="Quest command help", description = f"**{prefix}quest create**: Create a quest\n" +
                                                                        f"**{prefix}quest delete**: Delete a quest\n" +
                                                                        f"**{prefix}quest list**: List every quests on your GDPS\n" +
                                                                        f"**{prefix}quest modify**: Modify any parameters of a quest", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    if option == "create":
        embed = discord.Embed(description="Name of the quest", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        quest_name = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        quest_name = quest_name.content

        embed = discord.Embed(title="What do you need to get to complete the quest?", description="**Avaliable answers:** \norbs \nsilver coins \nstars", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        quest_type_value = None
        while True:
            quest_type = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            quest_type = quest_type.content.lower()
            if quest_type == "orbs":
                quest_type_value = 1
            elif quest_type == "silver coins":
                quest_type_value = 2
            elif quest_type == "stars":
                quest_type_value = 3
            else:
                await ctx.send("Invalid answer, please enter it again.")
                continue
            break

        embed = discord.Embed(description=f"How much {quest_type} do they need to complete the quest?", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        quest_type_amount = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        quest_type_amount = quest_type_amount.content

        embed = discord.Embed(description="How much diamonds do they get after completing the quest?", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        quest_reward = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        quest_reward = quest_reward.content

        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("insert into quests (type, amount, reward, name) values (%s, %s, %s, %s)", [quest_type_value, quest_type_amount, quest_reward, quest_name])
        connection.commit()
        embed = discord.Embed(description="Quest added!", color = discord.Colour.green())
        await ctx.send(embed=embed)
        cursor.execute("select * from quests")
        connection.commit()
        if cursor.rowcount < 3:
            embed = discord.Embed(description="Warning: You don't have 3 quests setup yet! The quest button only displays the quests if you have a minimum of 3.", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            return
    elif option == "delete":
        if value is None:
            await ctx.send("You need to enter a quest ID. (Quests ids can be found in m!quest list)")
            return
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("select ID from quests where ID = %s", [value])
        if cursor.rowcount == 0:
            await ctx.send("Quest ID not found. Enter the \"m!quest list\" command to see a list of avaliable quests.")
            return
        cursor.execute("delete from quests where ID = %s", [value])
        connection.commit()
        embed = discord.Embed(description="Quest deleted!", color = discord.Colour.green())
        await ctx.send(embed=embed)
    elif option == "list":
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("select * from quests")
        quest_list = cursor.fetchall()
        qlist = []
        for quests in quest_list:
            qlist.append(f"Quest name: {quests[4]} \nQuest ID: {quests[0]} \n\n")
        embed = discord.Embed(title="Quests on your GDPS", description="".join(map(str, qlist)), color = discord.Colour.green())
        await ctx.send(embed=embed)
    elif option == "modify":
        if value is None or value == "help":
            embed = discord.Embed(title="Quest modify command help", description = f"Use this command like this: m!quest modify <option> <quest name> \n\n**Quest options:** \nname \nreward_amount \ntype", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("select ID from quests where name = %s", [value2])
        if cursor.rowcount == 0:
            await ctx.send("Quest not found. Enter the \"m!quest list\" command to see a list of avaliable quests.")
            return
        elif cursor.rowcount > 1:
            await ctx.send("You have multiple quests with the same name, the bot doesn't support that currently.")
            return
        value2 = value2.lower()
        if value == "name":
            embed = discord.Embed(description="What do you want the new name to be?", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            quest_newname = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            quest_newname = quest_newname.content
            cursor.execute("update quests set name = %s where name = %s", [quest_newname, value2])
            connection.commit()
            embed = discord.Embed(description="Quest name updated!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
        elif value == "reward_amount":
            embed = discord.Embed(description="How much diamonds should they get when completing the quest?", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            quest_reward = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            quest_reward = quest_reward.content
            try:
                quest_reward = int(quest_reward)
            except:
                await ctx.send("The amount needs to be a number.")
                return
            cursor.execute("update quests set amount = %s where name = %s", [quest_reward, value2])
            connection.commit()
            embed = discord.Embed(description="Quest reward amount updated!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
        elif value == "type":
            embed = discord.Embed(title="What do you need to get to complete the quest?", description="**Avaliable answers:** \norbs \nsilver coins \nstars", color = discord.Colour.from_rgb(255, 128, 0))
            await ctx.send(embed=embed)
            quest_type = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            quest_type = quest_type.content.lower()
            if quest_type == "orbs":
                quest_type_value = 1
            elif quest_type == "silver coins":
                quest_type_value = 2
            elif quest_type == "stars":
                quest_type_value = 3
            else:
                await ctx.send("Invalid quest type.")
                return
            cursor.execute("update quests set type = %s where name = %s", [quest_type_value, value2])
            connection.commit()
            embed = discord.Embed(description="Quest type updated!", color = discord.Colour.green())
            await ctx.send(embed=embed)
            return
        else:
            await ctx.send("Invalid option.")
    else:
        await ctx.send("Invalid option.")
        return

@client.command()
async def gauntlet(ctx, option = None, value = None, value2 = None, value3 = None):
    print(f"Command gauntlet used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    check = await check_permission(ctx)
    if not check:
        return
    if option is None or option == "help":
        embed = discord.Embed(title="Gauntlet command help", description = f"**{prefix}gauntlet create**: Create a gauntlet\n" +
                                                                           f"**{prefix}gauntlet delete <gauntlet name>**: Delete a gauntlet\n" +
                                                                           f"**{prefix}gauntlet list**: List all gauntlets on your GDPS\n"
                                                                           f"**{prefix}gauntlet replace <gauntlet name> <level id> <new level id>**: Replace a level in a specific gauntlet", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    if option == "create":
        embed = discord.Embed(description="What gauntlet do you want to create? \n\n**Avaliable answers:** \nFire \nIce \nPoison \nShadow \nLava \nBonus \nChaos \nDemon \nTime \nCrystal \nMagic \nSpike \nMonster \nDoom \nDeath", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        while True:
            gauntlet_id = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            gauntlet_id = gauntlet_id.content.lower()
            if gauntlet_id == "fire":
                gauntlet_id = 1
            elif gauntlet_id == "ice":
                gauntlet_id = 2
            elif gauntlet_id == "poison":
                gauntlet_id = 3
            elif gauntlet_id == "shadow":
                gauntlet_id = 4
            elif gauntlet_id == "lava":
                gauntlet_id = 5
            elif gauntlet_id == "bonus":
                gauntlet_id = 6
            elif gauntlet_id == "chaos":
                gauntlet_id = 7
            elif gauntlet_id == "demon":
                gauntlet_id = 8
            elif gauntlet_id == "time":
                gauntlet_id = 9
            elif gauntlet_id == "crystal":
                gauntlet_id = 10
            elif gauntlet_id == "magic":
                gauntlet_id = 11
            elif gauntlet_id == "spike":
                gauntlet_id = 12
            elif gauntlet_id == "monster":
                gauntlet_id = 13
            elif gauntlet_id == "doom":
                gauntlet_id = 14
            elif gauntlet_id == "death":
                gauntlet_id = 15
            else:
                await ctx.send("Invalid answer, please enter it again.")
                continue
            connection = await get_connection(serverid)
            if connection is None:
                await ctx.send("There was an error while trying to contact the database.")
                return
            cursor = connection.cursor(buffered=True)
            cursor.execute("select ID from gauntlets where ID = %s", [gauntlet_id])
            if cursor.rowcount == 0:
                break
            elif cursor.rowcount == 1:
                await ctx.send("This gauntlet already exists, please try again")
                continue
            elif cursor.rowcount > 1:
                await ctx.send("You messed up your gauntlet configuration in your database, contact the GDPSFH support if you want to get some help. (This error has nothing to do with the bot, you did something wrong in your database)")
                return

        embed = discord.Embed(description="Enter level IDs you want to be in it. (Note: You need to seperate it with a comma \",\". Example: 25,45,9,36,4)", color = discord.Colour.from_rgb(255, 128, 0))
        await ctx.send(embed=embed)
        gauntlet_levels = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        gauntlet_levels = gauntlet_levels.content
        gauntlet_levels = gauntlet_levels.split(",")

        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        try:
            cursor.execute("insert into gauntlets (ID, level1, level2, level3, level4, level5) values (%s, %s, %s, %s, %s, %s)", [gauntlet_id, gauntlet_levels[0], gauntlet_levels[1], gauntlet_levels[2], gauntlet_levels[3], gauntlet_levels[4]])
            connection.commit()
            await ctx.send("Should be good!")
        except:
            await ctx.send("There was an error with the mysql command, its probably because you added / removed a field.")
            return
    elif option == "delete":
        if value is None:
            embed = discord.Embed(description="You need to type a gauntlet name.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        gauntlet_id = value.lower()
        if gauntlet_id == "fire":
            gauntlet_id = 1
        elif gauntlet_id == "ice":
            gauntlet_id = 2
        elif gauntlet_id == "poison":
            gauntlet_id = 3
        elif gauntlet_id == "shadow":
            gauntlet_id = 4
        elif gauntlet_id == "lava":
            gauntlet_id = 5
        elif gauntlet_id == "bonus":
            gauntlet_id = 6
        elif gauntlet_id == "chaos":
            gauntlet_id = 7
        elif gauntlet_id == "demon":
            gauntlet_id = 8
        elif gauntlet_id == "time":
            gauntlet_id = 9
        elif gauntlet_id == "crystal":
            gauntlet_id = 10
        elif gauntlet_id == "magic":
            gauntlet_id = 11
        elif gauntlet_id == "spike":
            gauntlet_id = 12
        elif gauntlet_id == "monster":
            gauntlet_id = 13
        elif gauntlet_id == "doom":
            gauntlet_id = 14
        elif gauntlet_id == "death":
            gauntlet_id = 15
        else:
            embed = discord.Embed(description="Invalid gauntlet name.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        cursor.execute("select ID from gauntlets where ID = %s", [gauntlet_id])
        if cursor.rowcount == 0:
            embed = discord.Embed(description="This gauntlet doesn't exist. If you want to get a list of gauntlets on your gdps enter m!gauntlet list.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        cursor.execute("delete from gauntlets where ID = %s", [gauntlet_id])
        connection.commit()
        embed = discord.Embed(description="Gauntlet deleted!", color = discord.Colour.green())
        await ctx.send(embed=embed)
    elif option == "list":
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("select ID from gauntlets")
        gauntlet_list = cursor.fetchall()
        if cursor.rowcount == 0:
            embed = discord.Embed(description="You don't have any gauntlets on your GDPS.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        glist = []
        for gauntlets in gauntlet_list:
            if gauntlets[0] == 1:
                gauntlet_name = "Fire"
            elif gauntlets[0] == 2:
                gauntlet_name = "Ice"
            elif gauntlets[0] == 3:
                gauntlet_name = "Poison"
            elif gauntlets[0] == 4:
                gauntlet_name = "Shadow"
            elif gauntlets[0] == 5:
                gauntlet_name = "Lava"
            elif gauntlets[0] == 6:
                gauntlet_name = "Bonus"
            elif gauntlets[0] == 7:
                gauntlet_name = "Chaos"
            elif gauntlets[0] == 8:
                gauntlet_name = "Demon"
            elif gauntlets[0] == 9:
                gauntlet_name = "Time"
            elif gauntlets[0] == 10:
                gauntlet_name = "Crystal"
            elif gauntlets[0] == 11:
                gauntlet_name = "Magic"
            elif gauntlets[0] == 12:
                gauntlet_name = "Spike"
            elif gauntlets[0] == 13:
                gauntlet_name = "Monster"
            elif gauntlets[0] == 14:
                gauntlet_name = "Doom"
            elif gauntlets[0] == 15:
                gauntlet_name = "Death"
            glist.append(gauntlet_name + "\n")
        embed = discord.Embed(title="Gauntlets on your GDPS", description="".join(map(str, glist)), color = discord.Colour.green())
        await ctx.send(embed=embed)
    elif option == "replace":
        try:
            value2 = int(value2)
            value3 = int(value3)
        except:
            await ctx.send("Level ids needs to be a number.")
            return
        if value2 is None:
            await ctx.send("You need to enter the id of the level that you want to replace.")
            return
        if value3 is None:
            await ctx.send("You need to enter the id of the new level that you want to replace.")
            return
        gauntlet_id = value.lower()
        if gauntlet_id == "fire":
            gauntlet_id = 1
        elif gauntlet_id == "ice":
            gauntlet_id = 2
        elif gauntlet_id == "poison":
            gauntlet_id = 3
        elif gauntlet_id == "shadow":
            gauntlet_id = 4
        elif gauntlet_id == "lava":
            gauntlet_id = 5
        elif gauntlet_id == "bonus":
            gauntlet_id = 6
        elif gauntlet_id == "chaos":
            gauntlet_id = 7
        elif gauntlet_id == "demon":
            gauntlet_id = 8
        elif gauntlet_id == "time":
            gauntlet_id = 9
        elif gauntlet_id == "crystal":
            gauntlet_id = 10
        elif gauntlet_id == "magic":
            gauntlet_id = 11
        elif gauntlet_id == "spike":
            gauntlet_id = 12
        elif gauntlet_id == "monster":
            gauntlet_id = 13
        elif gauntlet_id == "doom":
            gauntlet_id = 14
        elif gauntlet_id == "death":
            gauntlet_id = 15
        else:
            embed = discord.Embed(description="Invalid gauntlet name.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        connection = await get_connection(serverid)
        if connection is None:
            await ctx.send("There was an error while trying to contact the database.")
            return
        cursor = connection.cursor(buffered=True)
        cursor.execute("select * from gauntlets where ID = %s", [gauntlet_id])
        gauntlet_list = cursor.fetchall()
        if cursor.rowcount == 0:
            embed = discord.Embed(description="This gauntlet doesn't exist on your GDPS.", color = discord.Colour.red())
            await ctx.send(embed=embed)
            return
        cursor.execute("select level1 from gauntlets where ID = %s", [gauntlet_id])
        gauntlet_level1 = cursor.fetchall()
        cursor.execute("select level2 from gauntlets where ID = %s", [gauntlet_id])
        gauntlet_level2 = cursor.fetchall()
        cursor.execute("select level3 from gauntlets where ID = %s", [gauntlet_id])
        gauntlet_level3 = cursor.fetchall()
        cursor.execute("select level4 from gauntlets where ID = %s", [gauntlet_id])
        gauntlet_level4 = cursor.fetchall()
        cursor.execute("select level5 from gauntlets where ID = %s", [gauntlet_id])
        gauntlet_level5 = cursor.fetchall()
        if gauntlet_level1[0][0] == value2:
            cursor.execute("update gauntlets set level1 = %s where ID = %s", [value3, gauntlet_id])
        elif gauntlet_level2[0][0] == value2:
            cursor.execute("update gauntlets set level2 = %s where ID = %s", [value3, gauntlet_id])
        elif gauntlet_level3[0][0] == value2:
            cursor.execute("update gauntlets set level3 = %s where ID = %s", [value3, gauntlet_id])
        elif gauntlet_level4[0][0] == value2:
            cursor.execute("update gauntlets set level4 = %s where ID = %s", [value3, gauntlet_id])
        elif gauntlet_level5[0][0] == value2:
            cursor.execute("update gauntlets set level5 = %s where ID = %s", [value3, gauntlet_id])
        else:
            await ctx.send("The level that you want to replace is not in the gauntlet.")
            return
        connection.commit()
        await ctx.send("Level changed!")
        return
    else:
        embed = discord.Embed(description="Invalid option.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return

@client.command()
async def user(ctx, option = None, user = None):
    print(f"Command user used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    check = await check_permission(ctx)
    if not check:
        return
    if user is None or user == "help":
        embed = discord.Embed(title="User command help", description = f"**{prefix}user banip <ingame name>**: IP ban a specific user\n" +
                                                                       f"**{prefix}user unbanip <ingame name>**: Unban the IP a specific user\n" +
                                                                       f"**{prefix}user leadban <ingame name>**: Ban a specific user from the leaderboard\n"
                                                                       f"**{prefix}user leadunban <ingame name>**: Unban a specific user from the leaderboard", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    if option is None:
        await ctx.send("You need to type an option.")
        return
    connection = await get_connection(serverid)
    if connection is None:
        await ctx.send("There was an error while trying to contact the database.")
        return
    cursor = connection.cursor(buffered=True)
    option = option.lower()
    if option == "banip":
        cursor.execute("select accountID from accounts where userName = %s", [user])
        user_accountid = cursor.fetchall()
        if cursor.rowcount == 0:
            await ctx.send("This user doesn't exist.")
            return
        cursor.execute("select IP from users where extID = %s", [user_accountid[0][0]])
        user_ip = cursor.fetchall()
        if user_ip[0][0] == "127.0.0.1":
            await ctx.send("This user can't be banned because he doesn't have an IP in the database.")
            return
        cursor.execute("select * from bannedips where IP = %s", [user_ip[0][0]])
        if cursor.rowcount > 0:
            await ctx.send("This IP is already banned.")
            return
        cursor.execute("insert into bannedips (IP) values (%s)", [user_ip[0][0]])
        connection.commit()
        await ctx.send("The IP of this user is now banned!")
        return
    if option == "unbanip":
        cursor.execute("select accountID from accounts where userName = %s", [user])
        user_accountid = cursor.fetchall()
        if cursor.rowcount == 0:
            await ctx.send("This user doesn't exist.")
            return
        cursor.execute("select IP from users where extID = %s", [user_accountid[0][0]])
        user_ip = cursor.fetchall()
        if user_ip[0][0] == "127.0.0.1":
            await ctx.send("The IP of this user is not valid.")
            return
        cursor.execute("select * from bannedips where IP = %s", [user_ip[0][0]])
        if cursor.rowcount == 0:
            await ctx.send("This IP is not banned.")
            return
        cursor.execute("delete from bannedips where IP = %s", [user_ip[0][0]])
        connection.commit()
        await ctx.send("The IP of this user is now unbanned!")
        return
    if option == "leadban":
        cursor.execute("select * from accounts where userName = %s", [user])
        if cursor.rowcount == 0:
            await ctx.send("The account that you entered does not exist!")
            return
        cursor.execute("select isBanned from users where userName = %s", [user])
        banned = cursor.fetchall()
        if banned[0][0] == 1:
            await ctx.send("User is already leaderboard banned.")
            return
        cursor.execute("update users set isBanned = 1 where userName = %s", [user])
        connection.commit()
        await ctx.send("User is now leaderboard banned!")
        return
    if option == "leadunban":
        cursor.execute("select * from accounts where userName = %s", [user])
        if cursor.rowcount == 0:
            await ctx.send("The account that you entered does not exist!")
            return
        cursor.execute("select isBanned from users where userName = %s", [user])
        banned = cursor.fetchall()
        if banned[0][0] == 0:
            await ctx.send("User is not leaderboard banned.")
            return
        cursor.execute("update users set isBanned = 0 where userName = %s", [user])
        connection.commit()
        await ctx.send("User is no longer banned from the leaderboard!")
        return
    else:
        await ctx.send("Invalid option.")
        return

@client.command()
async def modsent(ctx, option=None, value=None):
    print(f"Command modsent used by {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})")
    serverid = ctx.guild.id
    check = await check_permission(ctx)
    if not check:
        return
    if option is None or option == "help":
        embed = discord.Embed(title="Modsent command help", description = f"**{prefix}modsent list <page>**: List levels that were sent by moderators \n" +
                                                                          f"**{prefix}modsent accept <suggestion id>**: Accept a moderator sugestion \n" +
                                                                          f"**{prefix}modsent deny <suggestion id>**: Deny a moderator sugestion \n\n" +
                                                                          f"Tip: Suggestions ID can be found in {prefix}modsent list", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return
    connection = await get_connection(serverid)
    if connection is None:
        await ctx.send("There was an error while trying to contact the database.")
        return
    cursor = connection.cursor(buffered=True)
    option = option.lower()
    if value is not None:
        try:
            value = int(value)
        except:
            await ctx.send("The value can only be a number.")
            return
    if option == "list":
        if value is None:
            value = 1
        cursor.execute("select * from suggest order by ID desc limit 12 offset %s", [(int(value)-1)*10])
        level_sent = cursor.fetchall()
        if cursor.rowcount == 0:
            await ctx.send("You reached the end or no levels were sent.")
            return
        embed = discord.Embed(title = "Levels sent by moderators", color = discord.Colour.green())
        for row in level_sent:
            cursor.execute("select userName from accounts where accountID = %s", [row[1]])
            suggestedby = cursor.fetchall()
            cursor.execute("select * from levels where levelID = %s", [row[2]])
            levelinfos = cursor.fetchall()
            if cursor.rowcount == 0:
                continue
            if row[5] == 0:
                feature = "No"
            elif row[5] == 1:
                feature = "Yes"
            else:
                feature = "Error"

            if row[7] == 1:
                difficulty = "Demon"
            elif row[6] == 1:
                difficulty = "Auto"
            elif row[3] == 0:
                difficulty = "NA"
            elif row[3] == 10:
                difficulty = "Easy"
            elif row[3] == 20:
                difficulty = "Normal"
            elif row[3] == 30:
                difficulty = "Hard"
            elif row[3] == 40:
                difficulty = "Harder"
            elif row[3] == 50:
                difficulty = "Insane"
            else:
                difficulty = "Error"
            embed.add_field(name = levelinfos[0][4], value = f"Suggestion ID: {row[0]} \nSuggested by: {suggestedby[0][0]} \nLevel ID: {row[2]} \nFeature: {feature} \nDifficulty: {difficulty} \nStars: {row[4]}", inline = True)
        await ctx.send(embed=embed)
    elif option == "accept":
        if value is None:
            await ctx.send("You need to enter a suggestion ID.")
            return
        cursor.execute("select * from suggest where ID = %s", [value])
        suggestion = cursor.fetchall()
        if cursor.rowcount == 0:
            await ctx.send("This suggestion ID is invalid.")
            return
        cursor.execute("update levels set starDifficulty = %s where levelID = %s", [suggestion[0][3], suggestion[0][2]])
        cursor.execute("update levels set starStars = %s where levelID = %s", [suggestion[0][4], suggestion[0][2]])
        cursor.execute("update levels set starFeatured = %s where levelID = %s", [suggestion[0][5], suggestion[0][2]])
        cursor.execute("update levels set starAuto = %s where levelID = %s", [suggestion[0][6], suggestion[0][2]])
        cursor.execute("update levels set starDemon = %s where levelID = %s", [suggestion[0][7], suggestion[0][2]])
        cursor.execute("select ID from suggest where suggestLevelId = %s", [suggestion[0][2]])
        suggestion_all_levels = cursor.fetchall()
        for rows in suggestion_all_levels:
            cursor.execute("delete from suggest where ID = %s", [rows[0]])
        connection.commit()
        await ctx.send("Suggestion accepted!")
    elif option == "deny":
        if value is None:
            await ctx.send("You need to enter a suggestion ID.")
            return
        cursor.execute("select * from suggest where ID = %s", [value])
        if cursor.rowcount == 0:
            await ctx.send("This suggestion ID is invalid.")
            return
        cursor.execute("delete from suggest where ID = %s", [value])
        connection.commit()
        await ctx.send("Suggestion denied!")
    else:
        await ctx.send("Invalid option.")
        return

@client.command()
async def help(ctx):
    embed = discord.Embed(title = "Bot informations", color = discord.Colour.red())
    embed.add_field(name = "All commands:", value = f"\n**{prefix}link** : Link your GDPS to this discord / Sync discord roles with GDPS roles"
                                                    + f"\n**{prefix}unlink** : Unlink your GDPS from this discord"
                                                    + f"\n**{prefix}whitelist** : Can be used to give permissions to certains users/roles to use commands"
                                                    + f"\n**{prefix}role** : Give people mod"
                                                    + f"\n**{prefix}stats** : Shows some stats about the GDPS"
                                                    + f"\n**{prefix}selfacc** : Manage your GDPS account via discord"
                                                    + f"\n**{prefix}modifylevel** : Modify almost any parameters of a level"
                                                    + f"\n**{prefix}mappack** :Create / manage map packs in your GDPS"
                                                    + f"\n**{prefix}quest** : Create / manage quests in your GDPS"
                                                    + f"\n**{prefix}gauntlet** : Create / manage gauntlet in your GDPS"
                                                    + f"\n**{prefix}reupload** : Reupload a specific level from the original GD server and song reupload"
                                                    + f"\n**{prefix}song** : Disable / Enable a specific custom song from being downloaded"
                                                    + f"\n**{prefix}modsent** : Show levels sent by moderators"
                                                    + f"\n**{prefix}user** : Ban / unban IP a specific user"
                                                    + f"\n**{prefix}credits** : Shows you who created the bot and how to invite it to your server")
    await ctx.send(embed=embed)

@client.command()
async def credits(ctx):
    Members = 0
    for i in client.guilds:
        Members += i.member_count

    embed = discord.Embed(title = "Bot informations", color = discord.Colour.from_rgb(255, 0, 0))
    embed.add_field(name = "Team members", value = "**Owner:** MathieuAR"
                                                 + "\n**Formatting of some messages:** Neptix"
                                                 + "\n**Bot profile picture** : Stolen on the internet"
                                                 + "\n\n**GDPS Free Hosting discord:** [Link](https://discord.gg/CkMV5DV)"
                                                 + "\n**Invite the bot to your server:** [Link](https://discord.com/api/oauth2/authorize?client_id=856516384716881940&permissions=8&scope=bot)"
                                                 + "\n\n**Server count** : " + str(len(client.guilds))  + " servers and " + str(Members) + " members total"
                                                 + "\n**Bot version** : 0.5")
    await ctx.send(embed=embed)

@client.event
async def on_member_update(before, after):
    if prefix == "tm!":
        return
    serverid = before.guild.id
    ingame_name = None
    if str(serverid) not in str(role_link):
        role_link[str(serverid)] = {}
    if str(before.id) not in str(role_link[str(serverid)]):
        database_cursor.execute("select ingame_name from gdps_manager_acclink where serverID = %s and userID = %s", [serverid, before.id])
        if database_cursor.rowcount == 0:
            role_link[str(serverid)][str(before.id)] = 0
            return
        ingame_name = database_cursor.fetchall()[0][0]
        role_link[str(serverid)][str(before.id)] = {"ingame_name": ingame_name}
    if role_link[str(serverid)][str(before.id)] == 0:
        return
    ingame_name = role_link[str(serverid)][str(before.id)]["ingame_name"]
    database_cursor.execute("select roleID,gdps_role_name from gdps_manager_rolelink where serverID = %s", [serverid])
    if database_cursor.rowcount == 0:
        return
    data = database_cursor.fetchall()
    for row in data:
        if row[0] not in str(before.roles) and row[0] in str(after.roles):
            connection = await get_connection(serverid)
            if connection is None:
                return
            cursor = connection.cursor(buffered=True)
            cursor.execute("select roleID from roles where roleName = %s", [row[1]])
            if cursor.rowcount == 0:
                return
            roleid = cursor.fetchall()[0][0]
            cursor.execute("select accountID from accounts where userName = %s", [ingame_name])
            if cursor.rowcount == 0:
                return
            ingame_id = cursor.fetchall()[0][0]
            cursor.execute("select * from roleassign where accountID = %s", [ingame_id])
            if cursor.rowcount == 0:
                cursor.execute("insert into roleassign (roleID,accountID) values (%s, %s)", [roleid, ingame_id])
            elif cursor.rowcount == 1:
                cursor.execute("update roleassign set roleID = %s where accountID = %s", [roleid, ingame_id])
            elif cursor.rowcount > 1:
                cursor.execute("delete from roleassign where accountID = %s", [ingame_id])
                cursor.execute("insert into roleassign (roleID,accountID) values (%s, %s)", [roleid, ingame_id])
            connection.commit()
            await send_log(serverid, f"The {row[1]} role got assigned to {before.mention} on the GDPS.")

        elif row[0] in str(before.roles) and row[0] not in str(after.roles):
            connection = await get_connection(serverid)
            if connection is None:
                return
            cursor = connection.cursor(buffered=True)
            cursor.execute("select roleID from roles where roleName = %s", [row[1]])
            if cursor.rowcount == 0:
                return
            roleid = cursor.fetchall()[0][0]
            cursor.execute("select accountID from accounts where userName = %s", [ingame_name])
            if cursor.rowcount == 0:
                return
            ingame_id = cursor.fetchall()[0][0]
            cursor.execute("select * from roleassign where accountID = %s", [ingame_id])
            if cursor.rowcount >= 1:
                cursor.execute("delete from roleassign where accountID = %s", [ingame_id])
            connection.commit()
            await send_log(serverid, f"The {row[1]} role got removed from {before.mention} on the GDPS.")

def xor_cipher(string: str, key: str) -> str:
    return ("").join(chr(ord(x) ^ ord(y)) for x, y in zip(string, itertools.cycle(key)))

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

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_title_check = info_dict.get('title', None)
    return video_title_check

async def send_log(guildid,message):
    database_cursor.execute("select log_channel_id from gdps_manager_serverdata where serverID = %s", [guildid])
    if database_cursor.rowcount == 0:
        return
    channelid = database_cursor.fetchall()[0][0]
    if channelid is None:
        return
    log_channel = await client.fetch_channel(channelid)
    embed = discord.Embed(description = message, color = discord.Colour.green())
    await log_channel.send(embed=embed)

async def check_permission(ctx):
    serverid = ctx.guild.id
    database_cursor.execute("select * from gdps_manager_serverdata where serverID = %s", [serverid])
    if database_cursor.rowcount == 0:
        await ctx.send("This server is not linked yet.")
        return
    database_cursor.execute("select typeID from gdps_manager_whitelist where serverID = %s and type = 'role'", [serverid])
    whitelisted_roles = database_cursor.fetchall()
    has_allowed_role = False
    for role in ctx.author.roles:
        if str(role.id) in str(whitelisted_roles):
            has_allowed_role = True
            break
    database_cursor.execute("select typeID from gdps_manager_whitelist where serverID = %s and type = 'user'", [serverid])
    whitelisted_users = database_cursor.fetchall()
    #if ctx.author.id not in data[str(serverid)]["allowed_users"] and has_allowed_role is False and ctx.author.id != ownerid and ctx.author.id not in authorised_list:
    if str(ctx.author.id) not in str(whitelisted_users) and has_allowed_role is False and ctx.author.id and not ctx.author.guild_permissions.administrator and ctx.author.id not in authorised_list:
        embed = discord.Embed(description = "Only authorised users can do that.", color = discord.Colour.red())
        await ctx.send(embed=embed)
        return False
    else:
        return True

async def get_connection(serverid):
    if serverid in connection_dictionary:
        connection = connection_dictionary[serverid]["connection"]
        connection.ping(reconnect=True)
        connection.autocommit = 1
        return connection
    elif await init_connection_from_db(serverid):
        return connection_dictionary[serverid]["connection"]
    return None

async def init_connection_from_db(serverid):
    if not serverid in connection_dictionary:
        database_cursor.execute("select * from gdps_manager_serverdata where serverID = %s", [serverid])
        if database_cursor.rowcount == 0:
            return False
        gdps_data = database_cursor.fetchall()[0]
        connection = None
        if prefix == "tm!":
            connection = mysql.connector.connect(host=mysql_ip,
                                                database=gdps_data[3],
                                                user="sysadmin",
                                                password="X5J8RGVixv28G22L6esd8k",
                                                connection_timeout=5)
        else:
            connection = mysql.connector.connect(host=mysql_ip,
                                                database=gdps_data[3],
                                                user=gdps_data[4],
                                                password=gdps_data[5],
                                                connection_timeout=5)
        if connection.is_connected():
            connection_dictionary[serverid] = {"connection": connection}
            return True
        else:
            del connection_dictionary[serverid]
            database_cursor.execute("select * from gdps_manager_serverdata where serverID = %s", [serverid])
            if database_cursor.rowcount == 0:
                return False
            gdps_data = database_cursor.fetchall()
            connection = mysql.connector.connect(host=gdps_host,
                                                 database=gdps_data[0][3],
                                                 user=gdps_data[0][4],
                                                 password=gdps_data[0][5],
                                                 connection_timeout=5)
            if connection.is_connected():
                connection_dictionary[serverid] = {"connection": connection}
                return True
    return False

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name=f"{prefix}help"))
    print("Bot chargé")

client.run(bot_token)