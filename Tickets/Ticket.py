import discord
import json
import os
import asyncio
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv, find_dotenv

intents = discord.Intents().all()
intents.members = True
load_dotenv(find_dotenv())
bot_token = os.environ.get("bot_token")
prefix = os.environ.get("prefix")
client = commands.Bot(command_prefix = prefix, help_command=None, intents=intents)

creating_ticket = []

@client.command()
async def sembed(ctx):
    if (ctx.author.id == 195598321501470720) | (ctx.author.id == 180790976128745472):
        embed = discord.Embed(title="Create a ticket", description="Click on the reaction to create a ticket", color=discord.Colour.green())
        message = await ctx.send(embed=embed)
        await message.add_reaction("<:gdstar:798238253500989460>")

        with open("tickets.json", "r+") as file:
            data = json.load(file)
            file.seek(0)
            data["create_ticket_msg"] = {"channel_id": ctx.message.channel.id,
                                        "msg_id": message.id}
            json.dump(data, file, indent=4)
        await ctx.message.delete()
    else:
        await ctx.send("Pourquoi t'essaye? Tu sais très bien que sa va pas marcher..")

@client.command()
async def user(ctx, arg1="null", arg2: discord.Member="null"):
    user_command = ctx.message.author.id
    if arg1 == "null":
        embed = discord.Embed(title="You need to enter an option!", color=discord.Colour.red())
        await ctx.send(embed=embed)
        return
    if arg2 == "null":
        embed = discord.Embed(title="You need to ping the user that you want to add!", color=discord.Colour.red())
        await ctx.send(embed=embed)
        return
    with open("tickets.json", "r+") as file:
        data = json.load(file)
        channelid = str(ctx.message.channel.id)
        if arg1 == "add":
            if channelid in str(data):
                if data["tickets"][channelid]["created_by"] == user_command:
                    ticket_channel = ctx.message.channel
                    await ticket_channel.set_permissions(arg2, read_messages=True)
                    embed = discord.Embed(description=f"**{arg2.name}** was successfully added to the ticket!", color=discord.Colour.green())
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Only the ticket owner can do that!", color=discord.Colour.red())
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="You need to enter that command in an active ticket!", color=discord.Colour.red())
                await ctx.send(embed=embed)
        elif arg1 == "remove":
            if channelid in str(data):
                if data["tickets"][channelid]["created_by"] == user_command:
                    ticket_channel = ctx.message.channel
                    await ticket_channel.set_permissions(arg2, read_messages=False)
                    embed = discord.Embed(description=f"**{arg2.name}** was successfully removed from the ticket!", color=discord.Colour.green())
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Only the ticket owner can do that!", color=discord.Colour.red())
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="You need to enter that command in an active ticket!", color=discord.Colour.red())
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Invalid option.", color=discord.Colour.red())
            await ctx.send(embed=embed)

@client.command()
async def close(ctx, *, args="null"):
    userid = ctx.author.id
    log_channel = client.get_channel(743038868013580330)
    moderator = discord.utils.get(ctx.guild.roles, id=743031490870509639)
    smod = discord.utils.get(ctx.guild.roles, id=789529083372634183)
    admin = discord.utils.get(ctx.guild.roles, id=743031374251950131)
    owner = discord.utils.get(ctx.guild.roles, id=743031850435477594)
    with open("tickets.json", "r+") as file:
        data = json.load(file)
        file.seek(0)
        channelid = str(ctx.message.channel.id)
        if channelid in str(data):
            ticket_owner = data["tickets"][str(ctx.message.channel.id)]["created_by"]
            owner_account = client.get_user(ticket_owner)
            if ticket_owner == userid or moderator in ctx.author.roles or smod in ctx.author.roles or admin in ctx.author.roles or owner in ctx.author.roles:
                if args == "null":
                    embed = discord.Embed(title=f"{owner_account.name}'s ticket was closed.", description=f"**Deleted by** : {ctx.author.mention} \n**Author mention** : <@!{data['tickets'][str(ctx.message.channel.id)]['created_by']}>", color=discord.Colour.red())
                else:
                    embed = discord.Embed(title=f"{owner_account.name}'s ticket was closed.", description=f"**Deleted by** : {ctx.author.mention} \n**Author mention** : <@!{data['tickets'][str(ctx.message.channel.id)]['created_by']}>\n**Reason** : {args}", color=discord.Colour.red())
                await log_channel.send(embed=embed)
                del data["tickets"][str(ctx.message.channel.id)]
                json.dump(data, file, indent=4)
                file.truncate()
                ticket_channel = ctx.message.channel
                await ticket_channel.delete()
            else:
                embed = discord.Embed(title="Only the ticket owner and staff can do that!", color=discord.Colour.red())
                await ctx.send(embed=embed) 
        else:
            embed = discord.Embed(title="You need to enter that command in an active ticket!", color=discord.Colour.red())
            await ctx.send(embed=embed)

@client.event
async def on_raw_reaction_add(payload):
    guild = client.get_guild(payload.member.guild.id)
    log_channel = client.get_channel(743038868013580330)
    if payload.member.id == 765571424903233577 or payload.member.id in creating_ticket:
        return
    current_channel = client.get_channel(payload.channel_id)
    if "ticket" not in current_channel.name:
        return
    with open("tickets.json", "r+") as file:
        data = json.load(file)
        file.seek(0)
        category = get(guild.categories, id=743038669497303040)
        embed_channel = get(guild.channels, id=data["create_ticket_msg"]["channel_id"])
        if payload.message_id == data["create_ticket_msg"]["msg_id"]:
            msg = await embed_channel.fetch_message(payload.message_id)
            await msg.remove_reaction(payload.emoji, payload.member)
            for tickets in data["tickets"]:
                if data["tickets"][tickets]["created_by"] == payload.member.id:
                    embed = discord.Embed(description=f"{payload.member.mention} You can only have 1 ticket open!", color=discord.Colour.green())
                    err_msg = await embed_channel.send(embed=embed)
                    await asyncio.sleep(5)
                    await err_msg.delete()
                    return
            creating_ticket.append(payload.member.id)
            ticket_channel = await guild.create_text_channel(f"Ticket-{payload.member.name}", category=category)
            embed = discord.Embed(title="Welcome to your ticket", description="Please explain your problem here (If you don't explain your problem you will be warned for creating a useless ticket) \n\nTo close the ticket click on the reaction or type t!close <reason>", color=discord.Colour.green())
            embed.set_footer(text=f"UserID: {payload.member.id}")
            ticket_embed = await ticket_channel.send(embed=embed)
            await ticket_channel.set_permissions(payload.member, read_messages=True, send_messages=True)
            await ticket_embed.add_reaction("<:gdstar:798238253500989460>")
            data["tickets"][str(ticket_channel.id)] = {"created_by": payload.member.id,
                                                       "close_msg_id": ticket_embed.id}
            json.dump(data, file, indent=4)
            discord_user = client.get_user(data["tickets"][str(ticket_channel.id)]["created_by"])
            embed = discord.Embed(title=f"{discord_user.name} created a ticket", description=f"**Author mention** : {discord_user.mention} \n**Channel** : <#{ticket_channel.id}>", color=discord.Colour.green())
            await log_channel.send(embed=embed)
            creating_ticket.remove(payload.member.id)
        else:
            for tickets in data["tickets"]:
                if payload.message_id == data["tickets"][tickets]["close_msg_id"]:
                    discord_user = client.get_user(data["tickets"][str(payload.channel_id)]["created_by"])
                    embed = discord.Embed(title=f"{discord_user.name}'s ticket was closed", description=f"**Deleted by** : {payload.member.mention} \n**Author mention** : {discord_user.mention}", color=discord.Colour.red())
                    await log_channel.send(embed=embed)
                    del data["tickets"][tickets]
                    json.dump(data, file, indent=4)
                    file.truncate()
                    ticket_channel = get(guild.channels, id=payload.channel_id)
                    await ticket_channel.delete()
                    return

@client.event
async def on_ready():
    print("Bot chargé")

client.run(bot_token)
