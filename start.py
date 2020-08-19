from datetime import datetime

import mysql.connector
from aio_timers import Timer
from discord import Embed, Colour, Game
from discord.ext import commands
from discord.ext.commands.context import Context
from mcstatus import MinecraftServer

from options import *

bot = commands.Bot(command_prefix="/")
server = MinecraftServer.lookup(SERVER_IP)
if SEC1_IP:
    server_sec1 = MinecraftServer.lookup(SEC1_IP)
if SEC2_IP:
    server_sec2 = MinecraftServer.lookup(SEC2_IP)


async def timer_task():
    try:
        await update_status()
    except:
        pass
    global timer
    timer = Timer(10, timer_task)


async def timer_task_sec():
    try:
        await ping_secondary()
    except:
        pass
    global timer_sec
    timer_sec = Timer(20, timer_task_sec)


timer = None
timer_sec = None
message = None
first_seen = None
last_seen = None
sec1_online = None
sec2_online = None
sec1_motd = None
sec2_motd = None
sec1_players = 0
sec2_players = 0
sec1_max = 0
sec2_max = 0
sec1_version = ''
sec2_version = ''


def log(text):
    print(f'[{datetime.now().strftime(DATE_FORMAT)}] {text}')


@bot.event
async def on_ready():
    channel = await bot.fetch_channel(STATUS_CHANNEL_ID)
    global message
    message = await channel.fetch_message(STATUS_MESSAGE_ID)

    global timer, timer_sec
    global sec1_online, sec1_motd
    global sec2_online, sec2_motd
    if SEC1_IP:
        sec1_motd = SEC_PINGING_TEXT
    if SEC2_IP:
        sec2_motd = SEC_PINGING_TEXT

    try:
        await update_status()
        await ping_secondary()
    except:
        pass
    timer = Timer(10, timer_task)
    timer_sec = Timer(20, timer_task_sec)


async def ping_secondary():
    log("Pinging server SEC1...")
    global server_sec1, sec1_online, sec1_motd, sec1_players, sec1_max, sec1_version
    try:
        status = server_sec1.status()
        if status.version.protocol > 1:
            if sec1_online is None:
                sec1_online = datetime.now()
            sec1_motd = status.description['text']
            sec1_players = status.players.online
            sec1_max = status.players.max
            sec1_version = status.version.name
            log("SEC1 online")
        else:
            sec1_online = None
            sec1_motd = SEC_OFFLINE_TEXT
            log("SEC1 offline")
    except Exception as e:
        sec1_online = None
        sec1_motd = f"{SEC_DISCONNECTED_TEXT}\n{str(e)}"
        log("!!! SEC1 disconnected")
    

    log("Pinging server SEC2...")
    global server_sec2, sec2_online, sec2_motd, sec2_players, sec2_max, sec2_version
    try:
        status = server_sec2.status()
        if status.version.protocol > 1:
            if sec2_online is None:
                sec2_online = datetime.now()
            sec2_motd = status.description['text']
            sec2_players = status.players.online
            sec2_max = status.players.max
            sec2_version = status.version.name
            log("SEC2 online")
        else:
            sec2_online = None
            sec2_motd = SEC_OFFLINE_TEXT
            log("SEC2 offline")
    except Exception as e:
        sec2_online = None
        sec2_motd = f"{SEC_DISCONNECTED_TEXT}\n{str(e)}"
        log("!!! SEC2 disconnected")


async def server_status(embed):
    global first_seen, last_seen

    if first_seen is not None:  # previously online, try Query directly
        try:
            await server_query(embed)
        except Exception as e:
            pass
        # continue with Status on failure

    log("Pinging server...")
    status = server_sec2.status()

    if status.version.protocol > 1:
        log("Server online")
        if first_seen is None:  # previously offline, try Query now
            await server_query(embed)
        return

    log("Server offline")
    await bot.change_presence(activity=Game(
        name=f"Minecraft - serwer offline"
    ))

    first_seen = None

    embed.colour = Colour.from_rgb(0x4c, 0xaf, 0x50)
    embed.add_field(
        name='Serwer jest wyłączony',
        value=
        'Dołącz do serwera, aby go uruchomić.',
        inline=False
    )
    embed.add_field(
        name='Ostatnio online',
        value='dawno temu' if last_seen is None else last_seen.strftime(DATE_FORMAT)
    )


async def server_query(embed):
    global first_seen, last_seen

    log("Querying server...")
    query = server.query(tries=1)

    if first_seen is None:
        first_seen = datetime.now()
    last_seen = datetime.now()

    await bot.change_presence(activity=Game(
        name=f"Minecraft ({query.players.online}/{query.players.max} graczy)"
    ))

    players = '\n'.join(query.players.names)
    embed.add_field(
        name='Gracze online',
        value=players if players else 'Brak graczy na serwerze',
        inline=False
    )

    embed.add_field(
        name='Adres serwera',
        value=
        '`szkolny.eu`\n'
        '`librus.fun`\n',
        inline=True
    )

    uptime = last_seen - first_seen
    uptime = str(uptime).split('.')[0]

    embed.add_field(
        name='Status serwera',
        value=
        f'**Wersja**: {SERVER_VERSION}\n'
        f'**Aktualnie graczy**: {query.players.online}\n'
        f'**Max graczy**: {query.players.max}\n'
        f'**Uptime**: {uptime}',
        inline=True
    )

    embed.add_field(
        name='Własne skiny',
        value=
        'Aby wgrać własny skin (np. dla kont non-premium) \n'
        f'wejdź na {SKINS_URL} i zaloguj się\n'
        'danymi które podajesz w /login na serwerze.',
        inline=False
    )


async def server_disconnected(embed, exception):
    global first_seen, last_seen

    log(f"!!! Server disconnected, last seen at {last_seen.strftime(DATE_FORMAT) if last_seen is not None else 'never'}")
    await bot.change_presence(activity=Game(
        name=f"Minecraft - serwer offline"
    ))

    first_seen = None

    embed.colour = Colour.from_rgb(0xf0, 0x47, 0x47)

    embed.add_field(
        name='Serwer jest offline',
        value=
        'Serwer może być wyłączony, mieć przerwę techniczną,\n'
        'lub nie działać z jakiegoś innego powodu.\n'
        'Nie martw się, nawet najlepszym e-dziennikom\n'
        'się to zdarza.',
        inline=False
    )

    embed.add_field(
        name='Ostatnio online',
        value='dawno temu' if last_seen is None else last_seen.strftime(DATE_FORMAT)
    )

    embed.add_field(
        name='Błąd',
        value=str(exception)
    )


async def update_status(get_embed=False):
    global first_seen, last_seen
    global server_sec1, sec1_online, sec1_motd, sec1_players, sec1_max, sec1_version
    global server_sec2, sec2_online, sec2_motd, sec2_players, sec2_max, sec2_version

    embed = Embed(
        #title="Szkolny.eu Minecraft",
        color=Colour.from_rgb(0x21, 0x96, 0xf3),
        url=HOMEPAGE_URL
    )

    embed.set_footer(text=f'Aktualizacja: {datetime.now().strftime(DATE_FORMAT)}')

    try:
        await server_status(embed)
    except Exception as e:
        await server_disconnected(embed, e)

    if SEC1_IP:
        if sec1_online:
            uptime = datetime.now() - sec1_online
            uptime = str(uptime).split('.')[0]

            embed.add_field(
                name=SEC1_NAME,
                value=f':white_check_mark: {sec1_motd}\n'
                      f'`{sec1_players}/{sec1_max} graczy, {sec1_version}, {uptime}`\n'
                      f'{SEC1_DESCRIPTION}',
                inline=False
            )
        else:
            embed.add_field(
                name=SEC1_NAME,
                value=f':x: {sec1_motd}',
                inline=False
            )

    if SEC2_IP:
        if sec2_online:
            uptime = datetime.now() - sec2_online
            uptime = str(uptime).split('.')[0]

            embed.add_field(
                name=SEC2_NAME,
                value=f':white_check_mark: {sec2_motd}\n'
                      f'`{sec2_players}/{sec2_max} graczy, {sec2_version}, {uptime}`\n'
                      f'{SEC2_DESCRIPTION}',
                inline=False
            )
        else:
            embed.add_field(
                name=SEC2_NAME,
                value=f':x: {sec2_motd}',
                inline=False
            )

    global message
    if message and not get_embed:
        await message.edit(embed=embed, content="")
    elif get_embed:
        return embed


@bot.event
async def on_message(msg):
    if not msg.content.startswith('/mc') \
            and msg.author.id != OP_USER_ID \
            and msg.author.id != bot.user.id \
            and msg.channel.id == STATUS_CHANNEL_ID:
        log(f"Message from {msg.author.name}: {msg.content}")
        await msg.delete()
    if msg.content.startswith('/mc'):
        await mc(Context(message=msg, prefix='/'), msg.content)


async def mc(ctx, arg):
    await ctx.message.delete()

    if arg == "status":
        return

    db = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWORD
    )

    arg = arg.split()
    if len(arg) > 1:
        arg = arg[1]
    else:
        arg = ''

    # global message
    # if arg == "init" and not message:
    #     embed = await update_status(get_embed=True)
    #     message = await ctx.send(embed=embed)
    #     return

    embed = Embed(
        title="Szkolny.eu Minecraft",
        color=Colour.from_rgb(0x21, 0x96, 0xf3),
        url=HOMEPAGE_URL
    )
    embed.set_thumbnail(url=EMBED_IMAGE_URL)
    embed.description = \
        'Użycie:\n' \
        '`/mc <nickname>` - Dodaj swój nickname do whitelisty\n'  # \
    # '`/mc status` - Wyświetl status serwera\n'

    if arg and arg != 'status':
        nickname = arg
        discord_id = ctx.author.id
        discord_tag = f'{ctx.author.name}#{ctx.author.discriminator}'
        cursor = db.cursor(dictionary=True)

        embed.description = f"Dodano gracza {nickname} do whitelisty."

        cursor.execute('SELECT * FROM minecraft.whitelist WHERE name = %s OR discordId = %s', (nickname, discord_id))
        row = cursor.fetchall()
        if len(row) > 0:
            row = row[0]
            if row:
                if row['name'] == nickname and row['discordId'] != discord_id:
                    embed.description = f"Gracz {nickname} został już dodany przez `{row['discordTag']}`."
                    msg = await ctx.send(embed=embed)
                    await msg.delete(delay=5)
                    return
                if row['name'] != nickname: # and row['discordId'] == discord_id:
                    embed.description = f"Dodałeś już gracza {row['name']}, zostanie on zastąpiony graczem {nickname}."

        try:
            cursor.execute(
                'REPLACE INTO minecraft.whitelist (name, discordId, discordTag) VALUES (%s, %s, %s)',
                (nickname, discord_id, discord_tag)
            )
            db.commit()
        except mysql.connector.errors.IntegrityError:
            embed.description = f"To konto Discord ma już gracza na serwerze."

    msg = await ctx.send(embed=embed)
    await msg.delete(delay=5)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
