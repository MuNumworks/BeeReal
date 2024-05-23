## BeeReal Discord Bot - Eratz!
from logging import exception
import os
import discord
from discord.channel import TextChannel
from discord.ext import commands
from discord import app_commands
import aiohttp
from functools import wraps
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext.commands.converter import ColorConverter
#import io
import json
import time
import random
import asyncio
import apscheduler

default_intents = discord.Intents.all()
default_intents.members = True
default_intents.messages = True

bot = commands.Bot(command_prefix="!", intents=default_intents)

DAY_TEMPLATE = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

GUILD_TEMPLATE = {
    "channels": {
        "alert_channel": "",
        "post_channel": "",
        "welcome_channel": "Welcome {member_mention}!",
        "leave_channel": "Goodbye {member_mention}",
    },
    "messages": {
        "welcome_message": "",
        "leave_message": "",
    }
}

global THE_HOUR
THE_HOUR = [-100, False]


def ensure_guild_file():

    def decorator(func):

        @wraps(func)
        async def wrapper(interaction, *args, **kwargs):
            PATH = f"Guilds/{interaction.guild_id}.json"

            if not os.path.exists(PATH):
                with open(PATH, "w") as f:
                    json.dump(GUILD_TEMPLATE, f, indent=4)

            return await func(interaction, *args, **kwargs)

        return wrapper

    return decorator


scheduler = AsyncIOScheduler()


def schedule_daily_message(day, hour, minute):
    # Ajoute une tâche à exécuter à l'heure spécifiée
    #print("DEBUG : schedule_daily_message infunc added")
    scheduler.add_job(send_daily_message,
                      CronTrigger(day_of_week=day, hour=hour, minute=minute))


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        #guild=discord.Object(id=1241425736754008156))
        print(f'Synced {len(synced)} command(s)')
        print(time.localtime().tm_wday)
        schedule_daily_message(DAY_TEMPLATE[time.localtime().tm_wday], 11, 53)
        scheduler.start()
        print('Scheduler started.')

    except Exception as e:
        print(f'Failed to sync commands: {e}')


async def send_daily_message():
    print(">>> DEBUG : SEND DAILY MESSAGE")
    for filename in os.listdir("Guilds/"):
        PATH = f"Guilds/{filename}"
        with open(PATH, "r") as f:
            channel = json.loads(f.read())['channels']['alert_channel']
        if channel:
            channel = bot.get_channel(channel)
            await channel.send(
                "# C'est l'heure du BeeReal !\n### Vous avez 10 minutes pour utiliser */post* afin de poster votre BeeReal"
            )
    bot_webhooks = {}
    THE_HOUR[0] = int(time.time())
    THE_HOUR[1] = True
    # Planifiez la prochaine tâche à une heure aléatoire
    next_hour = random.randint(7, 18)
    next_minute = random.randint(0, 59)
    print(
        f'Prochaine tâche planifiée à {DAY_TEMPLATE[(time.localtime().tm_wday + 1) % 7]} {next_hour:02d}:{next_minute:02d}'
    )

    # Replanifiez la tâche
    for job in scheduler.get_jobs():
        job.remove()
    schedule_daily_message(DAY_TEMPLATE[(time.localtime().tm_wday + 1) % 7],
                           next_hour, next_minute)
    #return time.time()


def admin_only():

    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Vous n'avez pas les permissions d'administrateur pour utiliser cette commande.",
                ephemeral=True)
            return False
        return True

    return app_commands.check(predicate)


@bot.event
async def on_member_remove(member):
    PATH = f"Guilds/{member.guild.id}.json"
    if not os.path.exists(PATH):
        with open(PATH, "w") as f:
            json.dump(GUILD_TEMPLATE, f, indent=4)

    with open(f'Guilds/{member.guild.id}.json', 'r') as f:
        data = json.loads(f.read())
    the_channel = data["channels"]["leave_channel"]
    text = data["messages"]["leave_message"].format(
        member_mention=member.mention,
        guild_name=member.guild.name,
        member_name=member.name,
        member_display=member.display_name)
    if the_channel and text:
        channel = bot.get_channel(int(the_channel))
        embed = discord.Embed(title="Au revoir",
                              description=text,
                              color=0x000000)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=
            f"Required by {member.display_name} at {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())}"
        )
        await channel.send(embed=embed)
    else:
        pass


@bot.event
async def on_member_join(member):
    PATH = f"Guilds/{member.guild.id}.json"
    if not os.path.exists(PATH):
        with open(PATH, "w") as f:
            json.dump(GUILD_TEMPLATE, f, indent=4)

    with open(f'Guilds/{member.guild.id}.json', 'r') as f:
        data = json.loads(f.read())
    the_channel = data["channels"]["welcome_channel"]
    text = data["messages"]["welcome_message"].format(
        member_mention=member.mention,
        guild_name=member.guild.name,
        member_name=member.name,
        member_display=member.display_name)

    if the_channel and text:
        channel = bot.get_channel(int(the_channel))
        embed = discord.Embed(title="Bienvenue",
                              description=text,
                              color=discord.Color.from_str("#000000"))
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=
            f"Required by {member.display_name} at {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())}"
        )
        await channel.send(f"||{member.mention}||", embed=embed)

    else:
        pass


@bot.tree.command(name="hello", description="Says hello to the user")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")


@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Pong! Latency: {round(bot.latency * 1000)}ms")


@bot.tree.command(  #guild=discord.Object(id=1241425736754008156),
    name="set_message",
    description="défini les messages du bot")
@app_commands.describe(
    mode="Le message de ...",
    text=
    "Le message personnalisé : use {member_mention}, {member_name}, {guild_name}, {member_display} to customize"
)
@app_commands.choices(mode=[
    app_commands.Choice(name="welcome", value="welcome"),
    app_commands.Choice(name="leave", value="leave"),
])
@admin_only()
@ensure_guild_file()
async def set_message(
    interaction: discord.Interaction,
    mode: str,
    text: str,
):
    PATH = f"Guilds/{interaction.guild_id}.json"
    #print(">>> DEBUG : set_message command")
    match mode:
        case "welcome":
            #print(">>> DEBUG : welcome step - OK")
            with open(PATH, "r") as f:
                data = json.loads(f.read())
            data["messages"]["welcome_message"] = text
            #print(">>> DEBUG : data load step - OK")
            with open(PATH, "w") as f:
                f.write(json.dumps(data))
            #print(">>> DEBUG : data write step - OK")
            await interaction.response.send_message(
                f"Le message de bienvenue a été défini sur :\n{text}")
            #print(">>> DEBUG : message send step - OK")
        case "leave":
            with open(PATH, "r") as f:
                data = json.loads(f.read())
            data["messages"]["leave_message"] = text
            with open(PATH, "w") as f:
                f.write(json.dumps(data))
            await interaction.response.send_message(
                f"Le message de départ a été défini sur :\n{text}")

        case _:
            await interaction.response.send_message("ERROR")


@bot.tree.command(name="help", description="Comment utiliser le bot")
async def help(interaction: discord.Interaction):
    #await interaction.response.send_message()
    try:
        guild_url = interaction.guild.icon.url
    except:
        guild_url = bot.user.avatar.url
    embed = discord.Embed(title="Description de BeeReal",
                          description="Comment ça marche ?",
                          color=discord.Color.from_str("#000000"))
    embed.set_author(name="BeeReal", icon_url=bot.user.avatar.url)
    embed.set_thumbnail(url=guild_url)
    embed.add_field(name="Présentation",
                    value="""
    \nBonjour, je suis BeeReal, un bot discord créé par systeme_eratz!
    Mon but est le suivant : \n
    Chaque jour, à une heure aléatoire, je vais poster un message dans le salon d'alerte, configurable   avec /channel.
    Ce message préviendra qu'il est l'heure du BeeReal, et que vous aurez 10 minutes pour utiliser /post.\n
    Une fois /post utilisé dans les 10 minutes, vous pourrez, sur le salon définis à cet effet (via /channel), parler entre vous, avec votre photo et votre description du jour. \n\n
    """,
                    inline=True)
    embed.add_field(name="Mes commandes",
                    value="""
    /hello : dit bonjour à l'utilisateur de la commande,
    /ping : affiche la latence du bot,
    /post : poste un BeeReal, requiert comme paramètre une image et du texte,
    /channel : définit le salon voulu, requiert comme paramètre un mode et un salon,
    /set_message : définit le message de bienvenue ou de départ, requiert comme paramètre un mode et un texte.
                    """,
                    inline=False)
    embed.set_footer(
        text=
        f"Required by {interaction.user.display_name} at {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())}",
        icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    #guild=discord.Object(id=1241425736754008156),
    name="channel",
    description=
    "Configure channels for Beereal alerts, posts and welcome message")
@app_commands.describe(mode="Select the mode (alert, post, welcome, leave)",
                       channel="Select the channel")
@app_commands.choices(mode=[
    app_commands.Choice(name="alert", value="alert"),
    app_commands.Choice(name="post", value="post"),
    app_commands.Choice(name="welcome", value="welcome"),
    app_commands.Choice(name="leave", value="leave"),
])
@admin_only()
@ensure_guild_file()
async def channel(interaction: discord.Interaction, mode: str,
                  channel: discord.TextChannel):
    PATH = f"Guilds/{interaction.guild_id}.json"
    with open(PATH, "r") as f:
        data = json.loads(f.read())
    match mode:
        case "alert":
            data["channels"]["alert_channel"] = channel.id
            with open(PATH, "w") as f:
                f.write(json.dumps(data))
            await interaction.response.send_message(
                f"Le channel de l'alerte BeeReal sera maintenant {channel.mention}"
            )
        case "welcome":
            data["channels"]["welcome_channel"] = channel.id
            with open(PATH, "w") as f:
                f.write(json.dumps(data))
            await interaction.response.send_message(
                f"Le channel ou les messages de bienvenue seront postés sera maintenant {channel.mention}"
            )

        case "leave":
            data["channels"]["leave_channel"] = channel.id
            with open(PATH, "w") as f:
                f.write(json.dumps(data))
            await interaction.response.send_message(
                f"Le channel ou les messages d'au revoir seront postés sera maintenant {channel.mention}"
            )

        case "post":
            data["channels"]["post_channel"] = channel.id
            with open(PATH, "w") as f:
                f.write(json.dumps(data))
            await interaction.response.send_message(
                f"Le channel ou les BeeReal seront postés sera maintenant {channel.mention}"
            )

        case _:
            await interaction.response.send_message("ERROR")


@bot.tree.command(name="post", description="Poster votre BeeReal")
async def post(interaction: discord.Interaction, image: discord.Attachment,
               text: str):
    print(time.time(), THE_HOUR)
    if abs(THE_HOUR[0] - time.time()) <= 600:
        # Créez le webhook
        PATH = f"Guilds/{interaction.guild_id}.json"
        with open(PATH, "r") as f:
            data = json.loads(f.read())
        channel = data["channels"]["post_channel"]
        post_channel = interaction.guild.get_channel(channel)
        webhook = await post_channel.create_webhook(
            name=f"{interaction.user.name} - {text}")

        # Utilisez l'URL de la photo directement pour obtenir les octets de l'image
        async with aiohttp.ClientSession() as session:
            async with session.get(image.url) as response:
                if response.status != 200:
                    await interaction.response.send_message(
                        "Impossible de télécharger la photo.", ephemeral=True)
                    return
                avatar_data = await response.read()

        # Modifiez le webhook pour utiliser l'image
        await webhook.edit(avatar=avatar_data)

        # Enregistrez le webhook pour une utilisation ultérieure
        if not interaction.guild_id in bot_webhooks:
            bot_webhooks[interaction.guild_id] = dict()
        bot_webhooks[interaction.guild_id][interaction.user.id] = webhook

        await interaction.response.send_message(
            f'BeeReal of {interaction.user.name} posté avec succès.')
    else:
        await interaction.response.send_message(
            f"Désolé {interaction.user.mention}! tu arrives trop tard, il n'est plus l'heure :("
        )


@bot.event
async def on_message(message):
    #print(bot_webhooks)
    with open(f"Guilds/{message.guild.id}.json", "r") as f:
        the_channel = json.loads(f.read())["channels"]["post_channel"]
    if message.guild.id in bot_webhooks.keys(
    ) and message.author.id in bot_webhooks[
            message.guild.id] and message.channel.id == the_channel:
        webhook = bot_webhooks[message.guild.id][message.author.id]
        await message.delete()
        await webhook.send(content=message.content)
    else:
        await bot.process_commands(message)


bot_webhooks = {}

bot.run(os.environ['BOT_TOKEN'])
