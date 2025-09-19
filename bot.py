import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

GUILD_ID = int(os.getenv("GUILD_ID"))
SUBMISSIONS_CHANNEL_ID = int(os.getenv("SUBMISSIONS_CHANNEL_ID"))
TASKS_CHANNEL_ID = int(os.getenv("TASKS_CHANNEL_ID"))
REPORTS_CHANNEL_ID = int(os.getenv("REPORTS_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен и готов!")

@bot.command()
async def submit(ctx, *, text):
    await ctx.send(f"{ctx.author.mention} отправил задачу: {text}")

TOKEN = os.getenv("BOT_TOKEN")
bot.run(TOKEN)