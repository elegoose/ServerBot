import subprocess
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


class Server:
    def __init__(self):
        self.name = ''
        # self.isRunning = False
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
            await ctx.send(f'Abriendo server de {self.GameName}...')
            p = subprocess.run("RunMinecraftServer.bat", stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            err = p.stderr
            if err[2:35] == 'remote_abrir_mcserver.bat started':
                # self.isRunning = True
                await ctx.send('Server abierto.')
                self.minecraftserver = MinecraftServer(localServerIp)

            else:
                raise CouldntAccessRemoteServer

        elif self.name in conanExilesNameArray:
            # subprocess.Popen("RunConanExilesServer.bat")
            # self.isRunning = True
            # self.GameName = 'Conan Exiles'
            raise ServerNotYetImplemented
        elif self.name in killingFloorNameArray:
            # subprocess.Popen("RunKillingFloorServer.bat")
            # self.isRunning = True
            # self.GameName = 'Conan Exiles'
            raise ServerNotYetImplemented
        else:
            raise UnexpectedRunError

    async def stop(self, ctx, activeServers):  # noqa
        if self.GameName == 'Minecraft':
            if await self.isNotEmpty(activeServers):
                raise CantClosePopulatedServer
            await ctx.send(f'Cerrando server de {self.GameName}...')
            with MCRcon(localServerIp, rconPass) as mcr:
                mcr.command("stop")
            await ctx.send('Server cerrado.')

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
                raise CantClosePopulatedServer
            with MCRcon(localServerIp, rconPass) as mcr:
                mcr.command("stop")
                await self.removeFromActiveServers(activeServers)
