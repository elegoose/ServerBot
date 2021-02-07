import discord
from discord.ext import commands
import serverclass as sv
import exceptions as err
from mcrcon import MCRcon
import json
import asyncio

with open('registerednames.json') as filename:
    registeredNamesData = json.load(filename)
with open('playercoordinates.json') as coordinatesfilename:
    coordinatesData = json.load(coordinatesfilename)
with open('credentials.txt') as f:
    credentialsArray = f.read().splitlines()
localServerIp = credentialsArray[1]
rconPass = credentialsArray[3]
worldName = credentialsArray[4]


class Minecraft(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(brief='permite guardar posición actual de minecraft',
                      aliases=['savecord', 'guardarpos', 'posactual', 'pos'])
    async def guardarposicion(self, ctx, *args):
        if not args:
            raise err.MissingArgument
        noMinecraft = True
        minecraftserver = None
        for server in sv.activeServers:
            if server.GameName == 'Minecraft':
                noMinecraft = False
                minecraftserver = server
        if noMinecraft:
            raise err.NoMinecraftServerRunning

        nombreCoordenada = ''
        for palabra in args:
            nombreCoordenada += palabra
            nombreCoordenada += ' '
        nombreCoordenada = nombreCoordenada[: len(nombreCoordenada) - 1]
        discordname = ctx.message.author.name
        minecraftname = discordname
        playerlist = await minecraftserver.playerlist()
        notInMinecraft = True
        coordinates = ''
        dimension = ''
        if discordname in registeredNamesData:
            minecraftname = registeredNamesData[discordname]

        for player in playerlist:
            if minecraftname == player:
                notInMinecraft = False
                with MCRcon(localServerIp, rconPass) as mcr:
                    response = mcr.command(f'whois {player}')
                array = response.split('\n')
                ubic = array[6]
                coordinates = ubic[19:len(ubic) - 1]
                coordinates = coordinates.replace(worldName, "")
                coordinatesArray = coordinates.split(',')
                dimension = coordinatesArray[0]
                if not dimension:
                    dimension = '🌎 Mundo Real (Overworld)'
                elif dimension == '_nether':
                    dimension = '🔥 Nether'
                elif dimension == '_the_end':
                    dimension = '🐲 The End'
                coordinatesArray = coordinatesArray[1:]
                coordinatesArray = list(map(lambda coord: coord.replace(" ", ""), coordinatesArray))
                coordinates = ", ".join(coordinatesArray)

        if notInMinecraft:
            raise err.PlayerNotInGame

        newPlayer = True
        for playername in coordinatesData:
            if discordname == playername:
                newPlayer = False
        if newPlayer:
            coordinatesData[discordname] = []
        else:
            for coordinate in coordinatesData[discordname]:
                if coordinate['name'] == nombreCoordenada:
                    raise err.NoDuplicateNamesAllowed
                elif coordinate['coordinates'] == coordinates:
                    raise err.NoDuplicateCoordinatesAllowed

        embed = discord.Embed(title='Coordenadas guardadas', colour=discord.Color.green())
        embed.add_field(name=f'"{nombreCoordenada}" en {dimension}', value=coordinates)
        await ctx.send(embed=embed)

        coordinatesData[discordname].append({'name': nombreCoordenada, 'coordinates': coordinates,
                                             'dimension': dimension})
        with open('playercoordinates.json', 'w') as file:
            json.dump(coordinatesData, file)

    @guardarposicion.error
    async def guardarposicion_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.NoMinecraftServerRunning):
                await ctx.send('Ningún servidor de Minecraft abierto.')
            elif isinstance(error, err.PlayerNotInGame):
                await ctx.send('No estás jugando minecraft, o parece que tu nombre de Minecraft es distinto al de '
                               'Discord.\nRegistra tu nombre de '
                               'minecraft usando sv.registrar tunombredeminecraft\nEjemplo: sv.registrar '
                               'Elegoose\nEsto '
                               'solo lo tendrás que hacer una vez.')
            elif isinstance(error, err.MissingArgument):
                await ctx.send('Debes elegir un nombre para tu coordenada.')
            elif isinstance(error, err.NoDuplicateNamesAllowed):
                await ctx.send('No se permiten nombres duplicados.')
            elif isinstance(error, err.NoDuplicateCoordinatesAllowed):
                await ctx.send('No se permiten coordenadas duplicadas.')
            else:
                await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
                raise error
        else:
            await ctx.send(f'Error inesperado: {error}\nAvísale al creador para que lo arregle.')
            raise error

    @commands.command(brief='revisar las coordenadas guardadas', aliases=['mycoords', 'savedcords', 'miscoords', 'mc'])
    async def miscoordenadas(self, ctx):
        sendername = ctx.message.author.name
        if sendername not in coordinatesData:
            raise err.NoCoordinatesSaved
        embed = discord.Embed(title=f'Coordenadas guardadas de {sendername}', colour=discord.Color.blue())
        for info in coordinatesData[sendername]:
            embed.add_field(name=f'"{info["name"]}" en {info["dimension"]}', value=info["coordinates"], inline=False)
        await ctx.send(embed=embed)

    @miscoordenadas.error
    async def miscoordenadas_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.NoCoordinatesSaved):
                await ctx.send('No has guardado ninguna coordenada.')
            else:
                await ctx.send(f'Error de invocación inesperado:{error}\nAvísale al creador para que lo arregle')
                raise error
        else:
            await ctx.send(f'Error inesperado:{error}\nAvísale al creador para que lo arregle')
            raise error

    @commands.command(brief='modificar nombre de coordenada', aliases=['modcoord', 'changecoord', 'modificar'])
    async def cambiar_nombre_coordenada(self, ctx, *args):
        if not args:
            raise err.MissingArgument
        sendername = ctx.message.author.name
        if sendername not in coordinatesData:
            raise err.NoCoordinatesSaved
        nametochange = ''
        for palabra in args:
            nametochange += palabra
            nametochange += ' '
        nametochange = nametochange[: len(nametochange) - 1]
        for info in coordinatesData[sendername]:
            if info["name"] == nametochange:
                embed = discord.Embed(title=f'Escribe a continuación el nuevo nombre para:',
                                      colour=discord.Color.orange(),
                                      description='Tienes 30 segundos para ingresar un nuevo nombre :clock2:')
                embed.add_field(name=f'{nametochange} en "{info["dimension"]}"', value=info["coordinates"])
                msg = await ctx.send(embed=embed)
                newname = await self.client.wait_for('message', check=lambda message: message.author == ctx.author,
                                                     timeout=30)
                await newname.add_reaction('\N{THUMBS UP SIGN}')
                newname = newname.content
                info["name"] = newname
                embed = discord.Embed(title=f'Coordenada modificada :white_check_mark:', colour=discord.Color.green())
                embed.add_field(name=f'Nuevo nombre: {newname}', value=f'Antiguo nombre: {nametochange}', inline=False)
                embed.add_field(name=info["dimension"], value=info["coordinates"])
                await msg.edit(embed=embed)
                with open('playercoordinates.json', 'w') as file:
                    json.dump(coordinatesData, file)
                return
        raise err.NoCoordinatesWithThatName

    @cambiar_nombre_coordenada.error
    async def cambiarcoord_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.NoCoordinatesSaved):
                await ctx.send('No has guardado ninguna coordenada.')
            elif isinstance(error, err.NoCoordinatesWithThatName):
                await ctx.send('No se ha encontrado ninguna coordenada guardada con ese nombre.')
            elif isinstance(error, err.MissingArgument):
                await ctx.send('No has escrito ninguna coordenada para cambiar.')
            elif isinstance(error, asyncio.TimeoutError):
                await ctx.send('Se te acabó el tiempo para enviar un nuevo nombre de coordenada')
            else:
                await ctx.send(f'Error de invocación inesperado:{error}\nAvísale al creador para que lo arregle')
                raise error
        else:
            await ctx.send(f'Error inesperado:{error}\nAvísale al creador para que lo arregle')
            raise error

    @commands.command(brief='borrar coordenada que sale en sv.mycoords', aliases=['delete', 'del', 'borrar'])
    async def borrarcoord(self, ctx, *args):
        if not args:
            raise err.MissingArgument
        sendername = ctx.message.author.name
        if sendername not in coordinatesData:
            raise err.NoCoordinatesSaved
        nametoerase = ''
        for palabra in args:
            nametoerase += palabra
            nametoerase += ' '
        nametoerase = nametoerase[: len(nametoerase) - 1]
        for info in coordinatesData[sendername]:
            if info["name"] == nametoerase:
                embed = discord.Embed(title=f'¿Segur@ que quieres borrar esta coordenada?',
                                      colour=discord.Color.red(),
                                      description='Tienes 30 segundos para reaccionar :clock2:')
                embed.add_field(name=f'"{nametoerase}" en {info["dimension"]}', value=info["coordinates"])
                embed.add_field(name='Selecciona una opción:', value='sí :ballot_box_with_check:      no :x: ')
                msg = await ctx.send(embed=embed)
                await msg.add_reaction("☑")
                await msg.add_reaction("❌")
                reactions = ["☑", "❌"]

                def check(reac, usr):
                    return usr == ctx.author and str(reac.emoji) in reactions

                reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=check)
                if reaction.emoji == "☑":
                    embed = discord.Embed(title=f'Coordenada borrada :white_check_mark:',
                                          colour=discord.Color.green())
                    embed.add_field(name=f'"{nametoerase}" en {info["dimension"]}', value=info["coordinates"])
                    coordinatesData[sendername].remove(info)
                    with open('playercoordinates.json', 'w') as file:
                        json.dump(coordinatesData, file)
                    await msg.edit(embed=embed)
                    return
                elif reaction.emoji == "❌":
                    embed = discord.Embed(title=f'Operación cancelada :x:',
                                          colour=discord.Color.red(), description='La coordenada no será borrada.')
                    await msg.edit(embed=embed)
                    return
        raise err.NoCoordinatesWithThatName

    @borrarcoord.error
    async def borrarcoord_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.NoCoordinatesSaved):
                await ctx.send('No has guardado ninguna coordenada.')
            elif isinstance(error, err.NoCoordinatesWithThatName):
                await ctx.send('No se ha encontrado ninguna coordenada guardada con ese nombre.')
            elif isinstance(error, err.MissingArgument):
                await ctx.send('No has escrito ninguna coordenada para borrar.')
            elif isinstance(error, asyncio.TimeoutError):
                await ctx.send('Se te acabó el tiempo para enviar una respuesta.')
            else:
                await ctx.send(f'Error de invocación inesperado:{error}\nAvísale al creador para que lo arregle')
                raise error
        else:
            await ctx.send(f'Error inesperado:{error}\nAvísale al creador para que lo arregle')
            raise error

    @commands.command(brief='registrar nombre de minecraft para guardar coordenadas', aliases=['register', 'reg'])
    async def registrar(self, ctx, *args):
        if not args:
            raise err.MissingArgument
        sendername = ctx.message.author.name
        if sendername in registeredNamesData:
            raise err.AlreadyRegistered
        minecraftname = ''
        for palabra in args:
            minecraftname += palabra
            minecraftname += ' '
        minecraftname = minecraftname[: len(minecraftname) - 1]
        registeredNamesData[sendername] = minecraftname
        with open('registerednames.json', 'w') as file:
            json.dump(registeredNamesData, file)
        embed = discord.Embed(title='Registro completado!', colour=discord.Color.green())
        embed.add_field(name=f'Has quedad@ registrad@ como "{minecraftname}"',
                        value=f'Si quieres modificarlo usa sv.modificar_registro '
                              f'tunuevonombre\nEjemplo: sv.modificar_registro Eleganso', inline=False)
        await ctx.send(embed=embed)

    @registrar.error
    async def registrar_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.AlreadyRegistered):
                await ctx.send('Ya estás registrad@. Si quieres modificar tu registro, usa sv.modificar_registro')
            elif isinstance(error, err.MissingArgument):
                await ctx.send('Ingresa un nombre para registrar, por favor.')
            else:
                await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
                raise error
        else:
            await ctx.send(f'Error de registro inesperado: {error}.\nAvísale al creador para que lo arregle.')
            raise error

    @commands.command(brief='modificar tu nombre de registro para usar sv.guardarcoordenada',
                      aliases=['modificarregistro'])
    async def modificar_registro(self, ctx, *args):
        if not args:
            raise err.MissingArgument
        sendername = ctx.message.author.name
        if sendername not in registeredNamesData:
            raise err.NotRegistered
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

    @modificar_registro.error
    async def modificar_registro_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.NotRegistered):
                await ctx.send('No estás registrad@, por lo tanto no hay nada que modificar.')
            elif isinstance(error, err.MissingArgument):
                await ctx.send('Ingresa un nombre para modificar, por favor.')
            else:
                await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
                raise error
        else:
            await ctx.send(f'Error de modificación inesperado: {error}.\nAvísale al creador para que lo arregle.')
            raise error

    @commands.command(brief='Agregar coordenadas manualmente', aliases=['addcoord', 'add'])
    async def agregar_coordenada(self, ctx, *args):
        if not args:
            raise err.MissingArgument
        sendername = ctx.message.author.name
        coordinate = ''
        for palabra in args:
            coordinate += palabra
            coordinate += ' '
        coordinate = coordinate[: len(coordinate) - 1]
        if ',' in coordinate:
            coordinate = coordinate.replace(" ", "")
            coordinatesArray = coordinate.split(',')
        else:
            coordinatesArray = coordinate.split(" ")

        if len(coordinatesArray) != 3:
            raise err.BadCoordinateFormat
        if int(coordinatesArray[1]) < 0:  # Y coordinate cant be negative
            raise err.BadCoordinateFormat
        for i in range(len(coordinatesArray)):
            coordinatesArray[i] = str('{:,}'.format(int(coordinatesArray[i])).replace(',', '.'))
        coordinate = ", ".join(coordinatesArray)
        embed = discord.Embed(title='¿En qué dimensión está tu coordenada?',
                              colour=discord.Color.orange(),
                              description='Tienes 30 segundos para reaccionar :clock2:')
        embed.add_field(name='Mundo Real (Overworld)', value=':earth_americas:', inline=False)
        embed.add_field(name='Nether', value=':fire:', inline=False)
        embed.add_field(name='End', value=':dragon_face:', inline=False)
        botmsgdimention = await ctx.send(embed=embed)
        await botmsgdimention.add_reaction('🌎')
        await botmsgdimention.add_reaction('🔥')
        await botmsgdimention.add_reaction('🐲')
        reactions = ['🌎', '🔥', '🐲']

        def check(reac, usr):
            return usr == ctx.author and str(reac.emoji) in reactions

        reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=check)
        dimension = ''
        if reaction.emoji == '🌎':
            dimension = '🌎 Mundo Real (Overworld)'
        elif reaction.emoji == '🔥':
            dimension = '🔥 Nether'
        elif reaction.emoji == '🐲':
            dimension = '🐲 End'
        embed = discord.Embed(title='Ingresa el nombre de tu coordenada',
                              colour=discord.Color.orange(),
                              description='Tienes 30 segundos para ingresar el nombre :clock2:')
        embed.add_field(name=dimension, value=coordinate, inline=False)
        botmsgname = await ctx.send(embed=embed)
        usermsgname = await self.client.wait_for('message', check=lambda msg: msg.author == ctx.author,
                                                 timeout=30)
        name = usermsgname.content
        embed = discord.Embed(title='¿Agregar coordenada?',
                              colour=discord.Color.blue(),
                              description='Tienes 30 segundos para reaccionar :clock2:')
        embed.add_field(name='Reacciona para confirmar', value='sí :white_check_mark:      no :x: ')
        embed.add_field(name=f'"{name}" en {dimension}', value=coordinate)
        botmsgconfirmation = await ctx.send(embed=embed)
        reactions = ['✅', '❌']
        await botmsgconfirmation.add_reaction('✅')
        await botmsgconfirmation.add_reaction('❌')
        reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=check)
        if reaction.emoji == '❌':
            embed = discord.Embed(title='Operación cancelada',
                                  colour=discord.Color.red(), description=':x:')
            await botmsgconfirmation.edit(embed=embed)
            await botmsgdimention.delete(delay=5)
            await usermsgname.delete(delay=5)
            await botmsgname.delete(delay=5)
        elif reaction.emoji == '✅':
            if sendername not in coordinatesData:
                coordinatesData[sendername] = []
            coordinatesData[sendername].append({'name': name, 'coordinates': coordinate,
                                                'dimension': dimension})
            with open('playercoordinates.json', 'w') as file:
                json.dump(coordinatesData, file)
            embed = discord.Embed(title='Coordenada agregada :white_check_mark:',
                                  colour=discord.Color.green(),
                                  description='Revisa tus coordenadas guardadas usando sv.mycoords!')
            embed.add_field(name=f'"{name}" en {dimension}', value=coordinate)
            await ctx.send(embed=embed)
            await botmsgdimention.delete(delay=5)
            await usermsgname.delete(delay=5)
            await botmsgname.delete(delay=5)
            await botmsgconfirmation.delete(delay=5)

    @agregar_coordenada.error
    async def agregar_coordenada_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.BadCoordinateFormat):
                await ctx.send('Debes ingresar una coordenada válida.')
            elif isinstance(error, asyncio.TimeoutError):
                await ctx.send('Se te acabó el tiempo para enviar una respuesta.')
            elif isinstance(error, err.MissingArgument):
                await ctx.send('Debes escribir una coordenada para usar el comando.')
            else:
                await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
                raise error
        else:
            await ctx.send(f'Error inesperado: {error}.\nAvísale al creador para que lo arregle.')
            raise error


def setup(client):
    client.add_cog(Minecraft(client))
