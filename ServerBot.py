import discord  # noqa
from discord.ext import commands, tasks
import servers as sv
from mcstatus import MinecraftServer
import socket
from mcrcon import MCRcon
import json

with open('credentials.txt') as f:
    credentialsArray = f.read().splitlines()
with open('registerednames.json') as filename:
    registeredNamesData = json.load(filename)
with open('playercoordinates.json') as coordinatesfilename:
    coordinatesData = json.load(coordinatesfilename)
token = credentialsArray[0]
localServerIp = credentialsArray[1]
serverMacAdress = credentialsArray[2]
rconPass = credentialsArray[3]
worldName = credentialsArray[4]
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


@client.command(brief='permite guardar posición actual de minecraft',
                aliases=['savecord', 'guardarpos', 'posactual', 'pos'])
async def guardarposicion(ctx, *args):
    noMinecraft = True
    minecraftserver = None
    for server in activeServers:
        if server.GameName == 'Minecraft':
            noMinecraft = False
            minecraftserver = server
    if noMinecraft:
        raise sv.NoMinecraftServerRunning

    nombreCoordenada = ''
    for palabra in args:
        nombreCoordenada += palabra
        nombreCoordenada += ' '
    nombreCoordenada = nombreCoordenada[: len(nombreCoordenada) - 1]
    if nombreCoordenada == '':
        raise sv.NoCoordinateNameChosen
    msg = f'Guardando coordenada de nombre "{nombreCoordenada}" '
    name = ctx.message.author.name

    playerlist = await minecraftserver.playerlist(activeServers)
    notInMinecraft = True
    coordinates = ''

    if name in registeredNamesData:
        name = registeredNamesData[name]

    for player in playerlist:
        if name == player:
            notInMinecraft = False
            with MCRcon(localServerIp, rconPass) as mcr:
                response = mcr.command(f'whois {player}')
            array = response.split('\n')
            ubic = array[6]
            coordinates = ubic[19:len(ubic) - 1]
            coordinates = coordinates.replace(worldName, "")
            places = ['end', 'nether']
            inOverworld = True
            for place in places:
                if place in coordinates:
                    inOverworld = False
                    if place == 'nether':
                        coordinates = coordinates.replace('_', '')
                    else:
                        coordinates = coordinates[1:].replace('_', ' ')
            if inOverworld:
                coordinates = 'Mundo Real' + coordinates
    if notInMinecraft:
        raise sv.PlayerNotInGame

    newPlayer = True
    for playername in coordinatesData:
        if name == playername:
            newPlayer = False
    if newPlayer:
        coordinatesData[name] = []

    msg += f' y coordenadas "{coordinates}"'
    await ctx.send(msg)

    coordinatesData[name].append({'name': nombreCoordenada, 'coordinates': coordinates})
    with open('playercoordinates.json', 'w') as file:
        json.dump(coordinatesData, file)


@guardarposicion.error
async def guardarposicion_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
        if isinstance(error, sv.NoMinecraftServerRunning):
            await ctx.send('Ningún servidor de Minecraft abierto.')
        elif isinstance(error, sv.PlayerNotInGame):
            await ctx.send('Parece que tu nombre de Minecraft es distinto al de Discord.\nRegistra tu nombre de '
                           'minecraft usando sv.registrar tunombredeminecraft\nEjemplo: sv.registrar Elegoose\nEsto '
                           'solo lo tendrás que hacer una vez.')
        elif isinstance(error, sv.NoCoordinateNameChosen):
            await ctx.send('Elige un nombre para tu coordenada.')
    else:
        await ctx.send(f'Error inesperado: {error}\nAvísale al creador para que lo arregle.')
        raise error


@client.command(brief='revisar las coordenadas guardadas', aliases=['mycords', 'savedcords', 'miscoords'])
async def miscoordenadas(ctx):
    sendername = ctx.message.author.name
    if sendername in registeredNamesData:
        sendername = registeredNamesData[sendername]
    if sendername not in coordinatesData:
        raise sv.NoCoordinatesSaved
    msg = ''
    for playername in coordinatesData:
        if playername == sendername:
            for info in coordinatesData[playername]:
                msg += f'Nombre: "{info["name"]}" Coordenadas: "{info["coordinates"]}"\n'
    await ctx.send(msg)


@miscoordenadas.error
async def miscoordenadas_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
        if isinstance(error, sv.NoCoordinatesSaved):
            await ctx.send('No has guardado ninguna coordenada.')
    else:
        await ctx.send(f'Error inesperado:{error}\nAvísale al creador para que lo arregle')
        raise error


@client.command(brief='registrar nombre de minecraft para guardar coordenadas', aliases=['register', 'reg'])
async def registrar(ctx, *args):
    sendername = ctx.message.author.name
    if sendername in registeredNamesData:
        raise sv.AlreadyRegistered
    minecraftname = ''
    for palabra in args:
        minecraftname += palabra
        minecraftname += ' '
    minecraftname = minecraftname[: len(minecraftname) - 1]
    registeredNamesData[sendername] = minecraftname
    with open('registerednames.json', 'w') as file:
        json.dump(registeredNamesData, file)
    await ctx.send(
        f'Has quedad@ registrad@ como "{minecraftname}".\nSi quieres modificarlo usa sv.modificar '
        f'tunuevonombre\nEjemplo: sv.modificar Eleganso')


@registrar.error
async def registrar_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
        if isinstance(error, sv.AlreadyRegistered):
            await ctx.send('Ya estás registrad@. Si quieres modificar tu registro, usa sv.modificar')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Ingresa un nombre para registrar, por favor.')
    else:
        await ctx.send(f'Error de registro inesperado: {error}.\nAvísale al creador para que lo arregle.')
        raise error


@client.command(brief='modificar tu nombre de registro para usar sv.guardarcoordenada',
                aliases=['modify', 'mod', 'modificarregistro'])
async def modificar(ctx, *args):
    sendername = ctx.message.author.name
    if sendername not in registeredNamesData:
        raise sv.NotRegistered
    newminecraftname = ''
    for palabra in args:
        newminecraftname += palabra
        newminecraftname += ' '
    newminecraftname = newminecraftname[: len(newminecraftname) - 1]
    oldName = registeredNamesData[sendername]
    registeredNamesData[sendername] = newminecraftname
    with open('registerednames.json', 'w') as file:
        json.dump(registeredNamesData, file)
    await ctx.send(f'Tu nombre de registro fue modificado de "{oldName}" a "{newminecraftname}".')


@modificar.error
async def modificar_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
        if isinstance(error, sv.NotRegistered):
            await ctx.send('No estás registrad@, por lo tanto no hay nada que modificar.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Ingresa un nombre para modificar, por favor.')
    else:
        await ctx.send(f'Error de modificación inesperado: {error}.\nAvísale al creador para que lo arregle.')
        raise error


@tasks.loop(seconds=1)
async def change_status():
    current_status = discord.Status.idle
    discord_status = None
    if not activeServers:
        current_status = 'Servers Cerrados'
        discord_status = discord.Status.idle
        await client.change_presence(status=discord_status, activity=discord.Game(name=current_status))
        return
    for server in activeServers:
        playerCount = await server.playerCount(activeServers)
        if playerCount == 0:
            current_status = server.idleName + 'Server Open ' + 'nadie jugando'
        else:
            current_status = server.idleName + 'Server Open ' + str(playerCount) + ' jugando'
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
