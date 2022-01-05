import discord
import time
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.utils import get

prefix = "update!"
intents = discord.Intents().all()
client = commands.Bot(command_prefix = prefix, help_command=None, intents=intents)
txt = open("bot_token.txt", "r")
bot_token = txt.readline()

perms_role_id = 743031850435477594
perm_bot_role_id = 743032001229226075
admin_role_id = 743031374251950131
dev_role_id = 746663126338109581
smod_role_id = 789529083372634183
mod_role_id = 743031490870509639
helper_role_id = 775512275141918772
donator_role_id = 803894379982880778
booster_role_id = 763337908211154955
gd_discord_staff_role_id = 762613358620049409
first_gdps_role_id = 765976288250822677
oldest_account_role_id = 796680929712144404
contributor_role_id = 781804718820950046
gdps_stats_tester_role_id = 798164016672407583
friend_role_id = 743031580083355669

@client.command()
@has_permissions(administrator=True)
async def upprefix(ctx):
    perms_role = get(ctx.guild.roles, id=perms_role_id)
    perm_bot_role = get(ctx.guild.roles, id=perm_bot_role_id)
    admin_role = get(ctx.guild.roles, id=admin_role_id)
    dev_role = get(ctx.guild.roles, id=dev_role_id)
    smod_role = get(ctx.guild.roles, id=smod_role_id)
    mod_role = get(ctx.guild.roles, id=mod_role_id)
    helper_role = get(ctx.guild.roles, id=helper_role_id)
    donator_role = get(ctx.guild.roles, id=donator_role_id)
    booster_role = get(ctx.guild.roles, id=booster_role_id)
    gd_discord_staff_role = get(ctx.guild.roles, id=gd_discord_staff_role_id)
    first_gdps_role = get(ctx.guild.roles, id=first_gdps_role_id)
    oldest_account_role = get(ctx.guild.roles, id=oldest_account_role_id)
    contributor_role = get(ctx.guild.roles, id=contributor_role_id)
    gdps_stats_tester_role = get(ctx.guild.roles, id=gdps_stats_tester_role_id)
    friend_role = get(ctx.guild.roles, id=friend_role_id)

    await ctx.send("Updating prefixes...")
    sleep_time = 3

    for member in ctx.guild.members:
        if perms_role in member.roles:
            time.sleep(sleep_time)
            await ctx.send(member.display_name + " can't be edited because he has admin permission.")
        elif perm_bot_role in member.roles:
            print("Can't modify: " + str(member))
        elif admin_role in member.roles:
            time.sleep(sleep_time)
            await ctx.send("Old name: " + member.display_name)
            changednick = "⚡ | " + member.name
            await member.edit(nick=changednick)
            await ctx.send("New name: " + member.display_name)
        elif dev_role in member.roles:
            time.sleep(sleep_time)
            await ctx.send("Old name: " + member.display_name)
            changednick = "💻 | " + member.name
            await member.edit(nick=changednick)
            await ctx.send("New name: " + member.display_name)
        elif smod_role in member.roles:
            time.sleep(sleep_time)
            await ctx.send("Old name: " + member.display_name)
            changednick = "🔨 | " + member.name
            await member.edit(nick=changednick)
            await ctx.send("New name: " + member.display_name)
        elif mod_role in member.roles:
            time.sleep(sleep_time)
            await ctx.send("Old name: " + member.display_name)
            changednick = "📙 | " + member.name
            await member.edit(nick=changednick)
            await ctx.send("New name: " + member.display_name)
        elif helper_role in member.roles:
            time.sleep(sleep_time)
            await ctx.send("Old name: " + member.display_name)
            changednick = "📘 | " + member.name
            await member.edit(nick=changednick)
            await ctx.send("New name: " + member.display_name)
        elif donator_role in member.roles:
            time.sleep(sleep_time)
            await ctx.send("Old name: " + member.display_name)
            changednick = "💛 | " + member.name
            await member.edit(nick=changednick)
            await ctx.send("New name: " + member.display_name)
        elif booster_role in member.roles:
            time.sleep(sleep_time)
            await ctx.send("Old name: " + member.display_name)
            changednick = "✨ | " + member.name
            await member.edit(nick=changednick)
            await ctx.send("New name: " + member.display_name)
        elif (booster_role in member.roles or
              gd_discord_staff_role in member.roles or
              first_gdps_role in member.roles or
              oldest_account_role in member.roles or
              contributor_role in member.roles):
            time.sleep(sleep_time)
            await ctx.send("Old name: " + member.display_name)
            changednick = "🕴️ | " + member.name
            await member.edit(nick=changednick)
            await ctx.send("New name: " + member.display_name)
        elif gdps_stats_tester_role in member.roles:
            time.sleep(sleep_time)
            await ctx.send("Old name: " + member.display_name)
            changednick = "🧪 | " + member.name
            await member.edit(nick=changednick)
            await ctx.send("New name: " + member.display_name)
        elif friend_role in member.roles:
            time.sleep(sleep_time)
            await ctx.send("Old name: " + member.display_name)
            changednick = "👥 | " + member.name
            await member.edit(nick=changednick)
            await ctx.send("New name: " + member.display_name)

    await ctx.send("Prefixes updated!")

@client.event
async def on_member_update(before, after):
    perms_role = get(after.guild.roles, id=perms_role_id)
    perm_bot_role = get(after.guild.roles, id=perm_bot_role_id)
    admin_role = get(after.guild.roles, id=admin_role_id)
    dev_role = get(after.guild.roles, id=dev_role_id)
    smod_role = get(after.guild.roles, id=smod_role_id)
    mod_role = get(after.guild.roles, id=mod_role_id)
    helper_role = get(after.guild.roles, id=helper_role_id)
    booster_role = get(after.guild.roles, id=booster_role_id)
    donator_role = get(after.guild.roles, id=donator_role_id)
    gd_discord_staff_role = get(after.guild.roles, id=gd_discord_staff_role_id)
    first_gdps_role = get(after.guild.roles, id=first_gdps_role_id)
    oldest_account_role = get(after.guild.roles, id=oldest_account_role_id)
    contributor_role = get(after.guild.roles, id=contributor_role_id)
    gdps_stats_tester_role = get(after.guild.roles, id=gdps_stats_tester_role_id)
    friend_role = get(after.guild.roles, id=friend_role_id)

    if perms_role in after.roles or perm_bot_role in after.roles:
        pass
    elif admin_role in after.roles:
        changednick = "⚡ | " + after.name
        await after.edit(nick=changednick)
    elif dev_role in after.roles:
        changednick = "💻 | " + after.name
        await after.edit(nick=changednick)
    elif smod_role in after.roles:
        changednick = "🔨 | " + after.name
        await after.edit(nick=changednick)
    elif mod_role in after.roles:
        changednick = "📙 | " + after.name
        await after.edit(nick=changednick)
    elif helper_role in after.roles:
        changednick = "📘 | " + after.name
        await after.edit(nick=changednick)
    elif donator_role in after.roles:
        changednick = "💛 | " + after.name
        await after.edit(nick=changednick)
    elif booster_role in after.roles:
        changednick = "✨ | " + after.name
        await after.edit(nick=changednick)
    elif (booster_role in after.roles or
         gd_discord_staff_role in after.roles or
         first_gdps_role in after.roles or
         oldest_account_role in after.roles or
         contributor_role in after.roles):
        changednick = "🕴️ | " + after.name
        await after.edit(nick=changednick)
    elif gdps_stats_tester_role in after.roles:
        changednick = "🧪 | " + after.name
        await after.edit(nick=changednick)
    elif friend_role in after.roles:
        changednick = "👥 | " + after.name
        await after.edit(nick=changednick)
    else:
        pass

    if admin_role in before.roles:
        if admin_role in after.roles:
            return None
        else: 
            await after.edit(nick=after.name)
    elif dev_role in before.roles:
        if dev_role in after.roles:
            return None
        else: 
            await after.edit(nick=after.name)
    elif smod_role in before.roles:
        if smod_role in after.roles:
            return None
        else: 
            await after.edit(nick=after.name)
    elif mod_role in before.roles:
        if mod_role in after.roles:
            return None
        else: 
            await after.edit(nick=after.name)
    elif helper_role in before.roles:
        if helper_role in after.roles:
            return None
        else: 
            await after.edit(nick=after.name)
    elif donator_role in before.roles:
        if donator_role in after.roles:
            return None
        else: 
            await after.edit(nick=after.name)
    elif (booster_role in before.roles or
         gd_discord_staff_role in before.roles or
         first_gdps_role in before.roles or
         oldest_account_role in before.roles or
         contributor_role in before.roles):
        if (booster_role in after.roles or
            gd_discord_staff_role in after.roles or
            first_gdps_role in after.roles or
            oldest_account_role in after.roles or
            contributor_role in after.roles):
            return None
        else: 
            await after.edit(nick=after.name)
    elif gdps_stats_tester_role in before.roles:
        if gdps_stats_tester_role in after.roles:
            return None
        else: 
            await after.edit(nick=after.name)
    elif friend_role in before.roles:
        if friend_role in after.roles:
            return None
        else: 
            await after.edit(nick=after.name)

@client.event
async def on_ready():
    print("Bot pret")

client.run(bot_token)