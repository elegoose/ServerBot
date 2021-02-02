import discord
from discord.ext import commands, tasks
import os

cogArray = []
for filename in os.listdir('./cogs'):
      if filename.endswith('.py'):
          cogArray.append(filename[:-3])
servers = '\n'
for cog in cogArray:
    servers += cog.capitalize() + '\n'
servers.rstrip()

with open('credentials.txt') as f:
    credentialsArray = f.read().splitlines()
token = credentialsArray[0]

client = commands.Bot(command_prefix = 'sv.')
extension_name = ''
@client.event
async def on_ready():
    print('Bot is ready.')

@client.event
async def on_command_error(ctx,error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Comando inválido.')

@client.command(brief="abre el servidor")
async def abrir(ctx, extension):
    global extension_name
    extension = extension.lower()
    extension_name = extension
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f'Abriendo server de {extension}')

@abrir.error
async def abrir_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Ningún servidor seleccionado para abrir. Estos son los disponibles: {servers}')
    elif isinstance(error, commands.CommandInvokeError):
        error=error.original
        if isinstance(error,commands.ExtensionAlreadyLoaded):
            await ctx.send('Ese servidor ya está abierto o se está abriendo.')
        elif isinstance(error,commands.ExtensionNotFound):
            await ctx.send(f'No existe ningún servidor con ese nombre. Estos son los disponibles: {servers}')
        else:
            await ctx.send(f'Error inesperado: {error}')
    else:
        await ctx.send(f'Ocurrió un error inesperado: {error}')
        raise error
client.run(token)