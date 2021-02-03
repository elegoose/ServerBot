import discord  # noqa
from discord.ext import commands, tasks
import servers as sv

with open('credentials.txt') as f:
    credentialsArray = f.read().splitlines()
token = credentialsArray[0]
serverMacAdress = credentialsArray[2]
activeServers = []
client = commands.Bot(command_prefix=('sv.', 'server.'))


@client.event
async def on_ready():
    print('Bot is ready.')


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Comando inválido.')


@client.command(brief="abre el servidor")
async def abrir(ctx, servername):
    for server in activeServers:
        if servername in sv.serverNames and server.isRunning:
            raise sv.ServerAlreadyRunning
    servername = servername.lower()
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
        else:
            await ctx.send(f'Error de invocación inesperado: {error}')
            raise error
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Ningún servidor seleccionado para abrir. Estos son los disponibles:')
    else:
        await ctx.send(f'Error inesperado: {error}')
        raise error


client.run(token)
