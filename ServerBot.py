import discord
from discord.ext import commands, tasks
import serverclass as sv
from mcstatus import MinecraftServer
import socket
import os

with open('credentials.txt') as f:
    credentialsArray = f.read().splitlines()
token = credentialsArray[0]
localServerIp = credentialsArray[1]
client = commands.Bot(command_prefix=('sv.', 'server.'))

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


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


@tasks.loop(seconds=1)
async def change_status():
    current_status = discord.Status.idle
    discord_status = None
    if not sv.activeServers:
        current_status = 'Servers Cerrados'
        discord_status = discord.Status.idle
        await client.change_presence(status=discord_status, activity=discord.Game(name=current_status))
        return
    for server in sv.activeServers:
        playerCount = await server.playerCount()
        if playerCount == 0:
            current_status = server.idleName + 'Server Open ' + 'nadie jugando'
        else:
            current_status = server.idleName + 'Server Open ' + str(playerCount) + ' jugando'
        discord_status = discord.Status.online
    await client.change_presence(status=discord_status, activity=discord.Game(name=current_status))


@tasks.loop(seconds=30)
async def check_minecraft_status():
    if sv.activeServers:
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
        sv.activeServers.append(server)
    except socket.timeout:
        pass


@tasks.loop(seconds=120)
async def automatic_shutdown():
    if not sv.activeServers:
        return
    for server in sv.activeServers:
        playercount = await server.playerCount()
        if playercount != 0:
            server.timer = 0
            return
        if not server.timer_started:
            server.timer_started = True
            return
        server.timer += 120
        if server.timer >= 840:
            await server.shutdown()


client.run(token)
