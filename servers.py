import subprocess
from wakeonlan import send_magic_packet

minecraftNameArray = ['mc', 'minecraft', 'mine']
conanExilesNameArray = ['conan', 'conanexiles']
killingFloorNameArray = ['kf2', 'kf', 'killingfloor2', 'killingfloor']
serverNames = [*minecraftNameArray, *conanExilesNameArray, *killingFloorNameArray]


class ServerNotFound(Exception):
    pass


class ServerAlreadyRunning(Exception):
    pass


class ServerNotYetImplemented(Exception):
    pass


class CouldntAccessRemoteServer(Exception):
    pass


class Server:
    def __init__(self):
        self.name = ''
        self.isRunning = False
        self.GameName = ''

    async def run(self, ctx, macAdress):
        if self.name in minecraftNameArray:
            send_magic_packet(macAdress)
            self.GameName = 'Minecraft'
            await ctx.send(f'Abriendo server de {self.GameName}...')
            p = subprocess.run("RunMinecraftServer.bat", stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            err = p.stderr
            if err[2:35] == 'remote_abrir_mcserver.bat started':
                self.isRunning = True
                await ctx.send(f'Server abierto.')
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
            raise ServerNotFound
