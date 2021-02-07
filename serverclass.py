import subprocess
import discord
from wakeonlan import send_magic_packet
from mcstatus import MinecraftServer
from mcrcon import MCRcon
import socket
import exceptions as er
import asyncio
from concurrent.futures import ThreadPoolExecutor

minecraftNameArray = ['mc', 'minecraft', 'mine']
conanExilesNameArray = ['conan', 'conanexiles']
killingFloorNameArray = ['kf2', 'kf', 'killingfloor2', 'killingfloor']
serverNames = [*minecraftNameArray, *conanExilesNameArray, *killingFloorNameArray]
with open('credentials.txt') as f:
    credentialsArray = f.read().splitlines()
localServerIp = credentialsArray[1]
rconPass = credentialsArray[3]
activeServers = []


def sleepserverpc():
    subprocess.run("SleepServerPC.bat", stdin=None, stdout=None, stderr=None, close_fds=True)


class Server:
    def __init__(self):
        self.name = ''
        self.GameName = ''
        self.nameArray = []
        self.idleName = ''
        self.minecraftserver = None
        self.timer = 0

    async def run(self, ctx, macadress):
        if self.name in minecraftNameArray:
            send_magic_packet(macadress)
            self.GameName = 'Minecraft'
            self.nameArray = minecraftNameArray
            self.idleName = 'Minecraft'
            embed = discord.Embed(title=f'Abriendo server de {self.GameName}', colour=discord.Color.blue(),
                                  description='Puede tardar un poco...')
            embed.set_image(
                url='https://i.pinimg.com/originals/02/a3/09/02a3098f242e38c1b8e76c37bbd3c5d6.gif')

            message = await ctx.send(embed=embed)
            p = subprocess.run("RunMinecraftServer.bat", stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            err = p.stderr
            if err[2:35] == 'remote_abrir_mcserver.bat started':
                embed = discord.Embed(title=f'Servidor de Minecraft abierto :white_check_mark:',
                                      colour=discord.Color.green())
                embed.set_image(
                    url='https://media1.tenor.com/images/b5947d684ea4b0f0ed083c0b217fb76e/tenor.gif?itemid=15531052')
                await message.edit(embed=embed)
                self.minecraftserver = MinecraftServer(localServerIp)

            else:
                raise er.CantAccessRemoteServer

        elif self.name in conanExilesNameArray:
            # subprocess.Popen("RunConanExilesServer.bat")
            # self.GameName = 'Conan Exiles'
            raise er.ServerNotYetImplemented
        elif self.name in killingFloorNameArray:
            # subprocess.Popen("RunKillingFloorServer.bat")
            # self.GameName = 'Conan Exiles'
            raise er.ServerNotYetImplemented
        else:
            raise er.UnexpectedRunError

    async def stop(self, ctx):  # noqa
        if self.GameName == 'Minecraft':
            if await self.isNotEmpty():
                raise er.CantClosePopulatedServer
            with MCRcon(localServerIp, rconPass) as mcr:
                mcr.command("stop")
            embed = discord.Embed(title=f'Server de {self.GameName} cerrado.', colour=discord.Color.green())
            embed.set_image(
                url='https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/284b6a8e-dc16-4274-bab4-ce7f8d872263'
                    '/d6byo72-78d16a50-a398-4176-ae84-72c6083b50a7.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9'
                    '.eyJzdWIiOiJ1cm46YXBwOiIsImlzcyI6InVybjphcHA6Iiwib2JqIjpbW3sicGF0aCI6IlwvZlwvMjg0YjZhOGUtZGMxNi'
                    '00Mjc0LWJhYjQtY2U3ZjhkODcyMjYzXC9kNmJ5bzcyLTc4ZDE2YTUwLWEzOTgtNDE3Ni1hZTg0LTcyYzYwODNiNTBhNy5wbmc'
                    'ifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6ZmlsZS5kb3dubG9hZCJdfQ.qiOeCjNfyNe3RQ7FZekhvvvKTlc1K'
                    '5BmTdDG75tQSVY')
            message = await ctx.send(embed=embed)
            await message.edit(embed=embed)
            await self.removeFromActiveServers()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(ThreadPoolExecutor(), sleepserverpc)

    async def playerlist(self):  # noqa
        if self.GameName == 'Minecraft':
            try:
                query = self.minecraftserver.query()
            except socket.timeout:
                await self.removeFromActiveServers()
                raise er.ServerIsNotRunning
            playerlist = query.players.names
            return playerlist

    async def isNotEmpty(self):  # noqa
        if self.GameName == 'Minecraft':
            try:
                status = self.minecraftserver.status()
            except socket.timeout:
                await self.removeFromActiveServers()
                raise er.ServerIsNotRunning
            if status.players.online == 0:
                return False
            else:
                return True

    async def playerCount(self):  # noqa
        if self.GameName == 'Minecraft':
            try:
                status = self.minecraftserver.status()
            except socket.timeout:
                await self.removeFromActiveServers()
                return
            return status.players.online

    async def removeFromActiveServers(self):  # noqa
        for server in activeServers:
            if server.GameName == self.GameName:
                activeServers.remove(server)

    async def shutdown(self):
        if self.GameName == 'Minecraft':
            if await self.isNotEmpty():
                self.timer = 0
                return
            with MCRcon(localServerIp, rconPass) as mcr:
                mcr.command("stop")
            try:
                await self.removeFromActiveServers()
            except ValueError:
                return
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(ThreadPoolExecutor(), sleepserverpc)
