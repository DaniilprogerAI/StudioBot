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
            CREATE TABLE IF NOT EXISTS tasks (
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
            CREATE TABLE IF NOT EXISTS checklist (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              task_id INTEGER,
              title TEXT,
              done INTEGER DEFAULT 0
            );
            """)
        await db.execute("""
                        -- submissions: ссылки на загруженные файлы
            CREATE TABLE IF NOT EXISTS submissions (
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
            CREATE TABLE IF NOT EXISTS audit (
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

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен и готов!")

@bot.command(name="добавить_задачу")
async def add_task(ctx, scene: str, *, title: str):
    """
    Добавляет новую задачу в базу.
    Использование: !добавить_задачу Сцена3 Сделать аниматик сцены
    """
    creator_id = ctx.author.id
    status = "open"
    deadline = None  # пока без срока
    assignee_id = None  # пока не назначен

    async with aiosqlite.connect("studio.db") as db:  # асинхронное подключение
        await db.execute(
            """
            INSERT INTO tasks (title, scene, assignee_id, creator_id, deadline, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, scene, assignee_id, creator_id, deadline, status)
        )
        await db.commit()  # коммит внутри async

    await ctx.send(f"✅ Задача '{title}' для {scene} добавлена в базу!")

@bot.command(name="подать")
async def submit(ctx, task_id: int):
    """
    Отправка файла в качестве результата по задаче.
    Использование: !submit 3 (и прикрепить файл)
    """
    if not ctx.message.attachments:
        await ctx.send("❌ Нужно прикрепить файл к сообщению!")
        return

    attachment = ctx.message.attachments[0]  # берём первый прикреплённый файл
    filename = attachment.filename
    filepath = f"submissions/{filename}"  # сохраним локально в папку submissions

    # сохраняем файл на диск
    await attachment.save(filepath)

    # данные для записи в БД
    user_id = ctx.author.id
    status = "submitted"

    async with aiosqlite.connect("studio.db") as db:
        await db.execute("""
            INSERT INTO submissions (task_id, user_id, filename, filepath, status)
            VALUES (?, ?, ?, ?, ?)
        """, (task_id, user_id, filename, filepath, status))
        await db.commit()

    await ctx.send(f"✅ Файл **{filename}** отправлен для задачи #{task_id}")

@bot.command(name="approve")
async def approve(ctx, submission_id: int):
    """
    Одобряет работу (submission).
    Использование: !approve 5
    """
    async with aiosqlite.connect("studio.db") as db:
        # проверим, есть ли такая запись
        cursor = await db.execute("SELECT id, status FROM submissions WHERE id = ?", (submission_id,))
        row = await cursor.fetchone()

        if not row:
            await ctx.send(f"❌ Сабмит #{submission_id} не найден.")
            return

        # обновляем статус
        await db.execute("UPDATE submissions SET status = 'approved' WHERE id = ?", (submission_id,))
        await db.commit()

    await ctx.send(f"✅ Сабмит #{submission_id} одобрен!")


@bot.command(name="reject")
async def reject(ctx, submission_id: int):
    """
    Отклоняет работу (submission).
    Использование: !reject 5
    """
    async with aiosqlite.connect("studio.db") as db:
        cursor = await db.execute("SELECT id, status FROM submissions WHERE id = ?", (submission_id,))
        row = await cursor.fetchone()

        if not row:
            await ctx.send(f"❌ Сабмит #{submission_id} не найден.")
            return

        await db.execute("UPDATE submissions SET status = 'rejected' WHERE id = ?", (submission_id,))
        await db.commit()

    await ctx.send(f"🚫 Сабмит #{submission_id} отклонён.")

@bot.command()
async def submit(ctx, *, text):
    await ctx.send(f"{ctx.author.mention} отправил задачу: {text}")

TOKEN = os.getenv("BOT_TOKEN")
bot.run(TOKEN)

print(TOKEN)
print(GUILD_ID)
print(SUBMISSIONS_CHANNEL_ID)