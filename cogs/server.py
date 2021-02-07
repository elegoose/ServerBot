import discord
from discord.ext import commands
import serverclass as sv
import exceptions as err
import sys

with open('credentials.txt') as f:
    credentialsArray = f.read().splitlines()
serverMacAddress = credentialsArray[2]


class Server(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(brief="abre el servidor seleccionado", aliases=['open'])
    async def abrir(self, ctx, servername):
        servername = servername.lower()
        if servername not in sv.serverNames:
            raise err.ServerNotFound
        for server in sv.activeServers:
            if servername in server.nameArray:
                raise err.ServerAlreadyRunning
        await ctx.message.add_reaction('🕑')
        server = sv.Server()
        server.name = servername
        await server.run(ctx, serverMacAddress)
        await ctx.message.clear_reaction('🕑')
        await ctx.message.add_reaction('✅')
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

    @commands.command(brief="cierra el servidor seleccionado", aliases=['stop'])
    async def cerrar(self, ctx, servername):
        servername = servername.lower()
        if servername not in sv.serverNames:
            raise err.ServerNotFound
        isRunning = False
        for server in sv.activeServers:
            if servername in server.nameArray:
                isRunning = True
                await server.stop(ctx, self.client)
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

    @commands.command()
    async def info(self, ctx):
        embed = discord.Embed(title=f'Hola! Mi nombre es ServerBot :robot:',
                              colour=discord.Color.blue(), description='Estos son algunos de los comandos que tengo:')
        embed.set_image(url='https://i.ytimg.com/vi/Sl6v84l5xcg/maxresdefault.jpg')
        embed.add_field(name='sv.guardarposicion',
                        value='Ejemplo: "sv.guardarposicion Mi Casa" guarda tu posición actual de Minecraft como "Mi Casa" en una lista',
                        inline=False)
        embed.add_field(name='sv.mycoords o sv.mc',
                        value='Ejemplo: "sv.mc" te muestra todas las coordenadas que has guardado', inline=False)
        embed.add_field(name='sv.add o sv.addcoord',
                        value='Ejemplo: "sv.add 122 20 -122" permite agregar manualmente una coordenada a la lista',
                        inline=False)
        embed.add_field(name='sv.borrar o sv.delete',
                        value='Ejemplo: "sv.borrar Mi Casa" borra la coordenada de nombre "Mi Casa"', inline=False)
        embed.add_field(name='sv.modificar o sv.changecoord',
                        value='Ejemplo: "sv.modificar Mi Casa" modifica el nombre de la coordenada "Mi Casa"',
                        inline=False)
        embed.add_field(name='sv.jugadores', value='Ejemplo: "sv.jugadores minecraft" muestra quiénes están jugando '
                                                   'en el servidor seleccionado.',inline=False)
        embed.add_field(name='sv.abrir', value='Ejemplo: "sv.abrir minecraft" Clásico del ServerBot :smirk:',inline=False)
        embed.add_field(name='¡Todos los comandos tienen abreviaciones! :open_mouth:', value='"minecraft" se abrevia '
                                                                                             '"mine", "mc" y los '
                                                                                             'comandos también, '
                                                                                             'como por ejemplo '
                                                                                             '"sv.guardarposicion", '
                                                                                             'que se abrevia "sv.pos"',inline=False)
        embed.add_field(name='¡Estado de los servidores en vivo!! :exploding_head:', value='A la derecha donde están '
                                                                                           'los usuarios '
                                                                                           'conectados, abajo de mi '
                                                                                           'nombre dice si '
                                                                                           'están abiertos los '
                                                                                           'servidores y cuántas '
                                                                                           'personas hay jugando en '
                                                                                           'ellos!!')
        embed.add_field(name='Soy versátil :wink: ',
                        value='Puedes ingresar los nombres y coordenadas como quieras, ¿Te gustan las comas? puedes '
                              'hacer sv.add 122,64,197 e igual sirve!')
        embed.add_field(name='Tengo cierre automático :star_struck:',
                        value='Si nadie está jugando, mis servidores se cierran automaticamente, apagando el '
                              'computador donde está el servidor.')
        embed.add_field(name='En un futuro seré multiserver :sunglasses: ',
                        value='Ahora sólo puedo abrir y cerrar un servidor de Minecraft, pero en el futuro también de '
                              'Conan Exiles y Killing Floor 2!', inline=False)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def stop_bot(self, ctx):
        await ctx.send('bot stopped')
        sys.exit()


def setup(client):
    client.add_cog(Server(client))
