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
        if nombreCoordenada == '':
            raise err.NoCoordinateNameChosen
        name = ctx.message.author.name

        playerlist = await minecraftserver.playerlist()
        notInMinecraft = True
        coordinates = ''

        if name in registeredNamesData:
            name = registeredNamesData[name]

        for player in playerlist:
            if name == player:
                notInMinecraft = False
                with MCRcon(localServerIp, rconPass) as mcr:
                    response = mcr.command(f'whois {player}')
                array = response.split('\n')
                ubic = array[6]
                coordinates = ubic[19:len(ubic) - 1]
                coordinates = coordinates.replace(worldName, "")
                places = ['end', 'nether']
                inOverworld = True
                for place in places:
                    if place in coordinates:
                        inOverworld = False
                        if place == 'nether':
                            coordinates = coordinates.replace('_', '')
                        else:
                            coordinates = coordinates[1:].replace('_', ' ')
                if inOverworld:
                    coordinates = 'Mundo Real' + coordinates
        if notInMinecraft:
            raise err.PlayerNotInGame

        newPlayer = True
        for playername in coordinatesData:
            if name == playername:
                newPlayer = False
        if newPlayer:
            coordinatesData[name] = []

        embed = discord.Embed(title='Coordenadas guardadas', colour=discord.Color.green())
        embed.add_field(name=nombreCoordenada, value=coordinates, inline=False)
        await ctx.send(embed=embed)

        coordinatesData[name].append({'name': nombreCoordenada, 'coordinates': coordinates})
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
            elif isinstance(error, err.NoCoordinateNameChosen):
                await ctx.send('Elige un nombre para tu coordenada.')
            else:
                await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
                raise error
        else:
            await ctx.send(f'Error inesperado: {error}\nAvísale al creador para que lo arregle.')
            raise error

    @commands.command(brief='revisar las coordenadas guardadas', aliases=['mycords', 'savedcords', 'miscoords'])
    async def miscoordenadas(self, ctx):
        sendername = ctx.message.author.name
        if sendername in registeredNamesData:
            sendername = registeredNamesData[sendername]
        if sendername not in coordinatesData:
            raise err.NoCoordinatesSaved
        embed = discord.Embed(title=f'Coordenadas guardadas de {sendername}', colour=discord.Color.blue())
        for info in coordinatesData[sendername]:
            embed.add_field(name=info["name"], value=info["coordinates"], inline=False)

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

    @commands.command(brief='modificar nombre de coordenada', aliases=['modcord', 'changecord'])
    async def cambiarcoord(self, ctx, *args):
        sendername = ctx.message.author.name
        if sendername in registeredNamesData:
            sendername = registeredNamesData[sendername]
        if sendername not in coordinatesData:
            raise err.NoCoordinatesSaved
        nametochange = ''
        for palabra in args:
            nametochange += palabra
            nametochange += ' '
        nametochange = nametochange[: len(nametochange) - 1]
        if nametochange == '':
            raise err.NoCoordinateNameChosen
        for info in coordinatesData[sendername]:
            if info["name"] == nametochange:
                embed = discord.Embed(title=f'Escribe a continuación el nuevo nombre para:',
                                      colour=discord.Color.orange(),
                                      description='Tienes 30 segundos para ingresar un nuevo nombre :clock2:')
                embed.add_field(name=nametochange, value=info["coordinates"])
                msg = await ctx.send(embed=embed)
                newname = await self.client.wait_for('message', check=lambda message: message.author == ctx.author,
                                                     timeout=30)
                newname = newname.content
                info["name"] = newname
                embed = discord.Embed(title=f'Coordenada modificada :white_check_mark:', colour=discord.Color.green())
                embed.add_field(name=f'Nuevo nombre: {newname}', value=f'Antiguo nombre: {nametochange}', inline=False)
                embed.add_field(name='Coordenadas', value=info["coordinates"])
                await msg.edit(embed=embed)
                with open('playercoordinates.json', 'w') as file:
                    json.dump(coordinatesData, file)
                return
        raise err.NoCoordinatesWithThatName

    @cambiarcoord.error
    async def cambiarcoord_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.NoCoordinatesSaved):
                await ctx.send('No has guardado ninguna coordenada.')
            elif isinstance(error, err.NoCoordinatesWithThatName):
                await ctx.send('No se ha encontrado ninguna coordenada guardada con ese nombre.')
            elif isinstance(error, err.NoCoordinateNameChosen):
                await ctx.send('No has escrito ninguna coordenada para cambiar.')
            elif isinstance(error, asyncio.TimeoutError):
                await ctx.send('Se te acabó el tiempo para enviar un nuevo nombre de coordenada')
            else:
                await ctx.send(f'Error de invocación inesperado:{error}\nAvísale al creador para que lo arregle')
                raise error
        else:
            await ctx.send(f'Error inesperado:{error}\nAvísale al creador para que lo arregle')
            raise error

    @commands.command(brief='borrar coordenada que sale en sv.mycords', aliases=['detele', 'del', 'borrar'])
    async def borrarcoord(self, ctx, *args):
        sendername = ctx.message.author.name
        if sendername in registeredNamesData:
            sendername = registeredNamesData[sendername]
        if sendername not in coordinatesData:
            raise err.NoCoordinatesSaved
        nametoerase = ''
        for palabra in args:
            nametoerase += palabra
            nametoerase += ' '
        nametoerase = nametoerase[: len(nametoerase) - 1]
        if nametoerase == '':
            raise err.NoCoordinateNameChosen
        for info in coordinatesData[sendername]:
            if info["name"] == nametoerase:
                embed = discord.Embed(title=f'¿Segur@ que quieres borrar esta coordenada?',
                                      colour=discord.Color.red(),
                                      description='Tienes 30 segundos para ingresar tu respuesta :clock2:')
                embed.add_field(name=nametoerase, value=info["coordinates"])
                embed.add_field(name='Envía tu respuesta:', value='sí :ballot_box_with_check:      no :x: ')
                msg = await ctx.send(embed=embed)
                resp = await self.client.wait_for('message', check=lambda message: message.author == ctx.author,
                                                  timeout=30)
                resp = resp.content
                siResp = ['si', 'sí', 'Si', 'Sí']
                noResp = ['No', 'no']
                if resp in siResp:
                    embed = discord.Embed(title=f'Coordenada borrada :white_check_mark:',
                                          colour=discord.Color.green())
                    embed.add_field(name=nametoerase, value=info["coordinates"])
                    coordinatesData[sendername].remove(info)
                    with open('playercoordinates.json', 'w') as file:
                        json.dump(coordinatesData, file)
                    await msg.edit(embed=embed)
                    return
                elif resp in noResp:
                    await msg.edit(content='La coordenada no será borrada.')
                else:
                    raise err.WrongAnswer
        raise err.NoCoordinatesWithThatName

    @borrarcoord.error
    async def borrarcoord_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.NoCoordinatesSaved):
                await ctx.send('No has guardado ninguna coordenada.')
            elif isinstance(error, err.NoCoordinatesWithThatName):
                await ctx.send('No se ha encontrado ninguna coordenada guardada con ese nombre.')
            elif isinstance(error, err.NoCoordinateNameChosen):
                await ctx.send('No has escrito ninguna coordenada para borrar.')
            elif isinstance(error, asyncio.TimeoutError):
                await ctx.send('Se te acabó el tiempo para enviar una respuesta.')
            elif isinstance(error, err.WrongAnswer):
                await ctx.send('No escribiste una respuesta válida.')
            else:
                await ctx.send(f'Error de invocación inesperado:{error}\nAvísale al creador para que lo arregle')
                raise error
        else:
            await ctx.send(f'Error inesperado:{error}\nAvísale al creador para que lo arregle')
            raise error

    @commands.command(brief='registrar nombre de minecraft para guardar coordenadas', aliases=['register', 'reg'])
    async def registrar(self, ctx, *args):
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
                        value=f'Si quieres modificarlo usa sv.modificar '
                              f'tunuevonombre\nEjemplo: sv.modificar Eleganso', inline=False)

    @registrar.error
    async def registrar_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.AlreadyRegistered):
                await ctx.send('Ya estás registrad@. Si quieres modificar tu registro, usa sv.modificar')
            else:
                await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
                raise error
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Ingresa un nombre para registrar, por favor.')
        else:
            await ctx.send(f'Error de registro inesperado: {error}.\nAvísale al creador para que lo arregle.')
            raise error

    @commands.command(brief='modificar tu nombre de registro para usar sv.guardarcoordenada',
                      aliases=['modify', 'mod', 'modificarregistro'])
    async def modificar(self, ctx, *args):
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

    @modificar.error
    async def modificar_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, err.NotRegistered):
                await ctx.send('No estás registrad@, por lo tanto no hay nada que modificar.')
            else:
                await ctx.send(f'Error de invocación inesperado: {error}\nAvísale al creador para que lo arregle.')
                raise error
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Ingresa un nombre para modificar, por favor.')
        else:
            await ctx.send(f'Error de modificación inesperado: {error}.\nAvísale al creador para que lo arregle.')
            raise error


def setup(client):
    client.add_cog(Minecraft(client))
