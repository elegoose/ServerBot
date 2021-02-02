import discord
from discord.ext import commands

class Minecraft(commands.Cog):

    def __init__(self,client):
        self.client = client
        print("im loaded")
    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'Pong!')

def setup(client):
    client.add_cog(Minecraft(client))
