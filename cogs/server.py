import discord
from discord.ext import commands
import serverclass as sv
import exceptions as err

with open('credentials.txt') as f:
    credentialsArray = f.read().splitlines()
serverMacAdress = credentialsArray[2]


class Server(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(brief="abre el servidor seleccionado")
    async def abrir(self, ctx, servername):
        servername = servername.lower()
        if servername not in sv.serverNames:
            raise err.ServerNotFound
        for server in sv.activeServers:
            if servername in server.nameArray:
                raise err.ServerAlreadyRunning
        server = sv.Server()
        server.name = servername
        await server.run(ctx, serverMacAdress)
        sv.activeServers.append(server)

    @abrir.error
    async def abrir_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.ServerNotFound):
                await ctx.send(f'No he encontrado ningún servidor para abrir con ese nombre.')
            elif isinstance(error, err.ServerAlreadyRunning):
                await ctx.send('Ese servidor ya está abierto o se está abriendo.')
            elif isinstance(error, err.ServerNotYetImplemented):
                await ctx.send('Aún no implemento este servidor al bot :sob:')
            elif isinstance(error, err.CantAccessRemoteServer):
                await ctx.send('Por alguna razón, no se puede acceder al PC del server.')
            elif isinstance(error, err.UnexpectedRunError):
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

    @commands.command(brief="cierra el servidor seleccionado")
    async def cerrar(self, ctx, servername):
        servername = servername.lower()
        if servername not in sv.serverNames:
            raise err.ServerNotFound
        isRunning = False
        for server in sv.activeServers:
            if servername in server.nameArray:
                isRunning = True
                await server.stop(ctx)
                try:
                    sv.activeServers.remove(server)
                except ValueError:
                    return
        if not isRunning:
            raise err.ServerIsNotRunning

    @cerrar.error
    async def cerrar_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.ServerIsNotRunning):
                await ctx.send('El servidor no está abierto, por lo tanto no se puede cerrar.')
            elif isinstance(error, err.ServerNotFound):
                await ctx.send('No he encontrado ningún servidor para cerrar con ese nombre.')
            elif isinstance(error, err.CantClosePopulatedServer):
                await ctx.send('No se puede cerrar el servidor porque hay jugadores dentro.')
            else:
                await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
                raise error
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Ningún servidor seleccionado para cerrar.')
        else:
            await ctx.send(f'Error inesperado: {error}\nAvísale al creador para que lo arregle.')
            raise error

    @commands.command(brief='muestra la lista de jugadores en el servidor seleccionado',
                      aliases=['playerlist', 'lista', 'jugando'])
    async def jugadores(self, ctx, servername):
        servername = servername.lower()
        if servername not in sv.serverNames:
            raise err.ServerNotFound

        isRunning = False
        playerlist = None
        gameName = None
        for server in sv.activeServers:
            if servername in server.nameArray:
                playerlist = await server.playerlist()
                gameName = server.GameName
                isRunning = True

        if not isRunning:
            raise err.ServerIsNotRunning

        if not playerlist:
            embed = discord.Embed(title=f'No hay nadie jugando en el servidor de {gameName}',
                                  colour=discord.Color.orange())
            embed.set_image(
                url='https://static.planetminecraft.com/files/resource_media/screenshot/1441/sad_steve8222664.jpg')
            await ctx.send(embed=embed)
            return
        playerlistString = '\n'
        for player in playerlist:
            playerlistString += player + '\n'
        embed = discord.Embed(title=f'Jugadores en servidor de {gameName}', colour=discord.Color.blue(),
                              description=playerlistString)
        await ctx.send(embed=embed)

    @jugadores.error
    async def jugadores_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.ServerIsNotRunning):
                await ctx.send('El servidor no está abierto.')
            elif isinstance(error, err.ServerNotFound):
                await ctx.send('No he encontrado ningún servidor con ese nombre.')
            else:
                await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
                raise error
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Ningún servidor seleccionado para ver quién está jugando en ellos.')
        else:
            await ctx.send(f'Error inesperado: {error}\nAvísale al creador para que lo arregle.')
            raise error


def setup(client):
    client.add_cog(Server(client))
