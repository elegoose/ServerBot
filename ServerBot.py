import discord  # noqa
from discord.ext import commands, tasks
import servers as sv
from mcstatus import MinecraftServer
import socket

with open('credentials.txt') as f:
    credentialsArray = f.read().splitlines()
token = credentialsArray[0]
localServerIp = credentialsArray[1]
serverMacAdress = credentialsArray[2]
activeServers = []
client = commands.Bot(command_prefix=('sv.', 'server.'))
timer = 0


@client.event
async def on_ready():
    change_status.start()
    check_minecraft_status.start()
    automatic_shutdown.start()
    print('Bot is ready.')


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Comando inválido.')


@client.command(brief="abre el servidor")
async def abrir(ctx, servername):
    servername = servername.lower()
    if servername not in sv.serverNames:
        raise sv.ServerNotFound
    for server in activeServers:
        if servername in server.nameArray:
            raise sv.ServerAlreadyRunning
    server = sv.Server()
    server.name = servername
    await server.run(ctx, serverMacAdress)
    activeServers.append(server)


@abrir.error
async def abrir_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
        if isinstance(error, sv.ServerNotFound):
            await ctx.send(f'No he encontrado ningún servidor para abrir con ese nombre.')
        elif isinstance(error, sv.ServerAlreadyRunning):
            await ctx.send('Ese servidor ya está abierto o se está abriendo.')
        elif isinstance(error, sv.ServerNotYetImplemented):
            await ctx.send('Aún no implemento este servidor al bot :sob:')
        elif isinstance(error, sv.CouldntAccessRemoteServer):
            await ctx.send('Por alguna razón, no se puede acceder al PC del server.')
        elif isinstance(error, sv.UnexpectedRunError):
            await ctx.send('Error inesperado en método run')
            raise error
        else:
            await ctx.send(f'Error de invocación inesperado: {error}')
            raise error
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Ningún servidor seleccionado para abrir.')
    else:
        await ctx.send(f'Error inesperado: {error}')
        raise error


@client.command(brief="cierra el servidor")
async def cerrar(ctx, servername):
    servername = servername.lower()
    if servername not in sv.serverNames:
        raise sv.ServerNotFound
    isRunning = False
    for server in activeServers:
        if servername in server.nameArray:
            isRunning = True
            await server.stop(ctx, activeServers)
            activeServers.remove(server)
    if not isRunning:
        raise sv.ServerIsNotRunning


@cerrar.error
async def cerrar_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
        if isinstance(error, sv.ServerIsNotRunning):
            await ctx.send('El servidor no está abierto, por lo tanto no se puede cerrar.')
        elif isinstance(error, sv.ServerNotFound):
            await ctx.send('No he encontrado ningún servidor para cerrar con ese nombre.')
        elif isinstance(error, sv.CantClosePopulatedServer):
            await ctx.send('No se puede cerrar el servidor porque hay jugadores dentro.')
        else:
            await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
            raise error
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Ningún servidor seleccionado para cerrar.')
    else:
        await ctx.send(f'Error inesperado: {error}\nAvísale al creador para que lo arregle.')
        raise error


@client.command(brief='muestra la lista de jugadores en el servidor seleccionado',
                aliases=['playerlist', 'lista', 'jugando'])
async def jugadores(ctx, servername):
    servername = servername.lower()
    if servername not in sv.serverNames:
        raise sv.ServerNotFound

    isRunning = False
    playerlist = None
    gameName = None
    for server in activeServers:
        if servername in server.nameArray:
            playerlist = await server.playerlist(activeServers)
            gameName = server.GameName
            isRunning = True

    if not isRunning:
        raise sv.ServerIsNotRunning

    if not playerlist:
        await ctx.send(f'No hay nadie jugando en el servidor de {gameName}')
        return
    playerlistString = '\n'
    for player in playerlist:
        playerlistString += player + '\n'
    await ctx.send(f'Jugadores en servidor de {gameName}:{playerlistString}')


@jugadores.error
async def jugadores_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
        if isinstance(error, sv.ServerIsNotRunning):
            await ctx.send('El servidor no está abierto.')
        elif isinstance(error, sv.ServerNotFound):
            await ctx.send('No he encontrado ningún servidor con ese nombre.')
        else:
            await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
            raise error
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Ningún servidor seleccionado para ver quién está jugando en ellos.')
    else:
        await ctx.send(f'Error inesperado: {error}\nAvísale al creador para que lo arregle.')
        raise error


@tasks.loop(seconds=1)
async def change_status():
    current_status = ''
    discord_status = None
    if not activeServers:
        current_status = 'Servers Cerrados'
        discord_status = discord.Status.idle
        await client.change_presence(status=discord_status, activity=discord.Game(name=current_status))
        return
    for server in activeServers:
        playerCount = await server.playerCount(activeServers)
        if playerCount == 0:
            current_status = server.idleName + 'Server open ' + 'nadie jugando'
        else:
            current_status = server.idleName + 'Server open ' + str(playerCount) + ' jugando'
        discord_status = discord.Status.online
    await client.change_presence(status=discord_status, activity=discord.Game(name=current_status))


@tasks.loop(seconds=30)
async def check_minecraft_status():
    if activeServers:
        return
    mcserver = MinecraftServer(localServerIp)
    try:
        mcserver.status()
        server = sv.Server()
        server.name = 'minecraft'
        server.GameName = 'Minecraft'
        server.minecraftserver = mcserver
        server.nameArray = sv.minecraftNameArray
        server.idleName = 'Mine'
        activeServers.append(server)
    except socket.timeout:
        pass


@tasks.loop(seconds=120)
async def automatic_shutdown():
    if not activeServers:
        return
    for server in activeServers:
        playercount = await server.playerCount(activeServers)
        if playercount == 0 and not server.timer_started:
            server.timer_started = True
        elif playercount == 0 and server.timer_started:
            server.timer += 120
        if server.timer >= 840:
            await server.shutdown(activeServers)


client.run(token)
