import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен и готов!")

@bot.command()
async def submit(ctx, *, текст):
    await ctx.send(f"{ctx.author.mention} отправил задачу: {текст}")

TOKEN = os.getenv("BOT_TOKEN")
bot.run(TOKEN)