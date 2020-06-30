from discord import Embed, Colour, Game
from discord.ext import commands
from discord.ext.commands.context import Context
from mcstatus import MinecraftServer
from aio_timers import Timer
import mysql.connector
from datetime import datetime

from options import *

bot = commands.Bot(command_prefix="/")
server = MinecraftServer(host=SERVER_IP)


async def timer_task():
    try:
        await update_status()
    except:
        pass
    global timer
    timer = Timer(5, timer_task)


timer = None
message = None
first_seen = None
last_seen = None


def log(text):
    print(f'[{datetime.now().strftime(DATE_FORMAT)}] {text}')


@bot.event
async def on_ready():
    channel = await bot.fetch_channel(STATUS_CHANNEL_ID)
    global message
    message = await channel.fetch_message(STATUS_MESSAGE_ID)

    try:
        await update_status()
    except:
        pass
    global timer
    timer = Timer(10, timer_task)


async def update_status(get_embed=False):
    global first_seen, last_seen

    embed = Embed(
        #title="Szkolny.eu Minecraft",
        color=Colour.from_rgb(0x21, 0x96, 0xf3),
        url=HOMEPAGE_URL
    )

    embed.set_footer(text=f'Aktualizacja: {datetime.now().strftime(DATE_FORMAT)}')

    log("Querying server...")
    try:
        query = server.query()

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
    except Exception as e:
        log(f"!!! Server offline, last seen at {last_seen.strftime(DATE_FORMAT)}")
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
            value=str(e)
        )

    global message
    if message and not get_embed:
        await message.edit(embed=embed)
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
