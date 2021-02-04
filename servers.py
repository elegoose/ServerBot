import subprocess
import discord
from wakeonlan import send_magic_packet
from mcstatus import MinecraftServer
from mcrcon import MCRcon
import socket

minecraftNameArray = ['mc', 'minecraft', 'mine']
conanExilesNameArray = ['conan', 'conanexiles']
killingFloorNameArray = ['kf2', 'kf', 'killingfloor2', 'killingfloor']
serverNames = [*minecraftNameArray, *conanExilesNameArray, *killingFloorNameArray]
with open('credentials.txt') as f:
    credentialsArray = f.read().splitlines()
localServerIp = credentialsArray[1]
rconPass = credentialsArray[3]


class ServerNotFound(Exception):
    pass


class ServerAlreadyRunning(Exception):
    pass


class ServerNotYetImplemented(Exception):
    pass


class CouldntAccessRemoteServer(Exception):
    pass


class UnexpectedRunError(Exception):
    pass


class ServerIsNotRunning(Exception):
    pass


class CantClosePopulatedServer(Exception):
    pass


class NoMinecraftServerRunning(Exception):
    pass


class PlayerNotInGame(Exception):
    pass


class AlreadyRegistered(Exception):
    pass


class NoCoordinatesSaved(Exception):
    pass


class NotRegistered(Exception):
    pass

class NoCoordinateNameChosen(Exception):
    pass

class NoCoordinatesWithThatName(Exception):
    pass

class WrongAnswer(Exception):
    pass
class Server:
    def __init__(self):
        self.name = ''
        self.GameName = ''
        self.nameArray = []
        self.idleName = ''
        self.minecraftserver = None
        self.timer = 0
        self.timer_started = False

    async def run(self, ctx, macadress):
        if self.name in minecraftNameArray:
            send_magic_packet(macadress)
            self.GameName = 'Minecraft'
            self.nameArray = minecraftNameArray
            self.idleName = 'Mine'
            embed = discord.Embed(title=f'Abriendo server de {self.GameName}', colour=discord.Color.blue())
            embed.set_image(url='https://media0.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif?cid=ecf05e47a59isekwfgivvltr425piiaovjyztl498icy4aer&rid=giphy.gif')

            message = await ctx.send(embed=embed)
            p = subprocess.run("RunMinecraftServer.bat", stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            err = p.stderr
            if err[2:35] == 'remote_abrir_mcserver.bat started':
                embed = discord.Embed(title=f'Servidor de Minecraft abierto :white_check_mark:', colour=discord.Color.green())
                embed.set_image(url = 'https://media1.tenor.com/images/b5947d684ea4b0f0ed083c0b217fb76e/tenor.gif?itemid=15531052')
                await message.edit(embed=embed)
                self.minecraftserver = MinecraftServer(localServerIp)

            else:
                raise CouldntAccessRemoteServer

        elif self.name in conanExilesNameArray:
            # subprocess.Popen("RunConanExilesServer.bat")
            # self.GameName = 'Conan Exiles'
            raise ServerNotYetImplemented
        elif self.name in killingFloorNameArray:
            # subprocess.Popen("RunKillingFloorServer.bat")
            # self.GameName = 'Conan Exiles'
            raise ServerNotYetImplemented
        else:
            raise UnexpectedRunError

    async def stop(self, ctx, activeServers):  # noqa
        if self.GameName == 'Minecraft':
            if await self.isNotEmpty(activeServers):
                raise CantClosePopulatedServer
            # embed = discord.Embed(title=f'Cerrando server de {self.GameName}...', colour=discord.Color.gold())
            # embed.set_image(url='https://es.phoneky.com/gif-animations/?id=s2s30650')
            # msg = await ctx.send(embed = embed)
            with MCRcon(localServerIp, rconPass) as mcr:
                mcr.command("stop")
            embed = discord.Embed(title=f'Server de {self.GameName} cerrado.', colour=discord.Color.green())
            embed.set_image(url='https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/284b6a8e-dc16-4274-bab4-ce7f8d872263/d6byo72-78d16a50-a398-4176-ae84-72c6083b50a7.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOiIsImlzcyI6InVybjphcHA6Iiwib2JqIjpbW3sicGF0aCI6IlwvZlwvMjg0YjZhOGUtZGMxNi00Mjc0LWJhYjQtY2U3ZjhkODcyMjYzXC9kNmJ5bzcyLTc4ZDE2YTUwLWEzOTgtNDE3Ni1hZTg0LTcyYzYwODNiNTBhNy5wbmcifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6ZmlsZS5kb3dubG9hZCJdfQ.qiOeCjNfyNe3RQ7FZekhvvvKTlc1K5BmTdDG75tQSVY')
            await ctx.send(embed=embed)

    async def playerlist(self, activeServers):  # noqa
        if self.GameName == 'Minecraft':
            try:
                query = self.minecraftserver.query()
            except socket.timeout:
                await self.removeFromActiveServers(activeServers)
                raise ServerIsNotRunning
            playerlist = query.players.names
            return playerlist

    async def isNotEmpty(self, activeServers):  # noqa
        if self.GameName == 'Minecraft':
            try:
                status = self.minecraftserver.status()
            except socket.timeout:
                await self.removeFromActiveServers(activeServers)
                raise ServerIsNotRunning
            if status.players.online == 0:
                return False
            else:
                return True

    async def playerCount(self, activeServers):  # noqa
        if self.GameName == 'Minecraft':
            try:
                status = self.minecraftserver.status()
            except socket.timeout:
                await self.removeFromActiveServers(activeServers)
                return
            return status.players.online

    async def removeFromActiveServers(self, activeServers):  # noqa
        for server in activeServers:
            if server.GameName == self.GameName:
                activeServers.remove(server)

    async def shutdown(self, activeServers):
        if self.GameName == 'Minecraft':
            if await self.isNotEmpty(activeServers):
                self.timer = 0
                return
            with MCRcon(localServerIp, rconPass) as mcr:
                mcr.command("stop")
                await self.removeFromActiveServers(activeServers)
