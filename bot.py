import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import aiosqlite
import asyncio

async def init_db():
    async with aiosqlite.connect("studio.db") as db:
        await db.execute("""
            -- tasks: основная карточка задачи
            CREATE TABLE tasks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT,
              scene TEXT,
              assignee_id INTEGER,
              creator_id INTEGER,
              deadline TEXT,        -- ISO string
              status TEXT,          -- open, in_progress, submitted, in_review, approved, rejected
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
        """)
        await db.execute("""
                        
            -- checklist items (опционально)
            CREATE TABLE checklist (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              task_id INTEGER,
              title TEXT,
              done INTEGER DEFAULT 0
            );
            """)
        await db.execute("""
                        -- submissions: ссылки на загруженные файлы
            CREATE TABLE submissions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              task_id INTEGER,
              user_id INTEGER,
              filename TEXT,
              filepath TEXT,        -- локальный путь или S3 URL
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              status TEXT DEFAULT 'submitted'
            );
            """)
        await db.execute("""
                        
            -- audit / лог
            CREATE TABLE audit (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              task_id INTEGER,
              actor_id INTEGER,
              action TEXT,
              details TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
        await db.commit()

asyncio.run(init_db())

UPLOAD_FOLDER = os.path.join(os.getcwd(), "files")

# пример сохранения файла
# file = await attachment.to_file()
# await file.save(os.path.join(UPLOAD_FOLDER, attachment.filename))

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

print(TOKEN)
print(GUILD_ID)
print(SUBMISSIONS_CHANNEL_ID)