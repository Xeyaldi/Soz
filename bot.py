import os
import asyncio
import random
import psycopg2
import requests # Lüğəti internetdən çəkmək üçün əlavə edildi
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ChatType
from aiogram.client.default import DefaultBotProperties

# Heroku məlumatları
API_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# --- 📚 AVTOMATİK LÜĞƏT YÜKLƏMƏ ---
def download_dictionary():
    # Azərbaycan dili söz siyahısı mənbəyi
    url = "https://raw.githubusercontent.com/mamedoff/azerbaijani-wordlist/master/az_AZ.txt"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            # Sözləri sətir-sətir oxuyub böyük hərflə siyahıya salır
            words = {line.strip().upper() for line in response.text.split('\n') if line.strip()}
            print(f"✅ Lüğət yükləndi: {len(words)} söz yaddaşdadır.")
            return words
    except Exception as e:
        print(f"❌ Lüğət yüklənmədi: {e}")
    return {"ANA", "ATA", "AZƏRBAYCAN", "MÜSTƏQİLLİK", "VƏTƏN"}

# Bot işə düşəndə lüğəti yaddaşa yığır
AZ_WORDS = download_dictionary()

# --- 🗄 POSTGRESQL (Xallar üçün) ---
def get_db_connection():
    # Heroku linkini PostgreSQL standartına uyğunlaşdırırıq
    db_url = DATABASE_URL
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(db_url, sslmode='require')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id BIGINT PRIMARY KEY, name TEXT, 
                       total_score INTEGER DEFAULT 0, daily_score INTEGER DEFAULT 0)''')
    conn.commit()
    cursor.close()
    conn.close()

def add_score(user_id, name, points):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, name, total_score, daily_score) 
        VALUES (%s, %s, %s, %s) 
        ON CONFLICT (user_id) DO UPDATE 
        SET total_score = users.total_score + %s, 
            daily_score = users.daily_score + %s,
            name = %s""", (user_id, name, points, points, points, points, name))
    conn.commit()
    cursor.close()
    conn.close()

# Bot sazlaması
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# --- 🏆 SIRALAMA ---
async def get_ranking(data_type="total"):
    column = "total_score" if data_type == "total" else "daily_score"
    title = "🏆 Ümumi Top 13" if data_type == "total" else "📊 Günlük Top 13"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT name, {column} FROM users WHERE {column} > 0 ORDER BY {column} DESC LIMIT 13")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    text = f"✨ **{title}**\n━━━━━━━━━━━━━━\n"
    if not rows:
        text += "❌ Hələ ki heç kim xal qazanmayıb."
    else:
        for i, row in enumerate(rows, 1):
            text += f"{i}. {row[0]} ➜ `{row[1]}` xal\n"
    return text

# --- 🏠 START ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎮 Oyuna Başla", callback_data="start_game"))
    builder.row(
        types.InlineKeyboardButton(text="🏆 Ümumi Top 13", callback_data="show_top"),
        types.InlineKeyboardButton(text="📊 Günlük Top 13", callback_data="show_daily")
    )
    builder.row(types.InlineKeyboardButton(text="👑 Sahib", url="https://t.me/aysberqqq"))
    builder.row(types.InlineKeyboardButton(text="💬 Söhbət Qrupu: @sohbetqruprc", url="https://t.me/sohbetqruprc"))
    
    await message.answer(
        f"✨ **Salam {message.from_user.first_name}!**\n\n"
        "Söz Oyunu botuna xoş gəldin. Ana sözün içindən yeni sözlər tap!\n\n"
        "🚀 **Başlamaq üçün botu qrupa əlavə et və düyməyə bas:**",
        reply_markup=builder.as_markup()
    )

# --- 🎮 OYUN STATUSU ---
game = {"active": False, "main_word": "", "found_words": []}
WORDS_BANK = ["MÜBALİĞƏLİ", "AZƏRBAYCAN", "ELEKTRONİKA", "KİBERNETİKA", "MÜSTƏQİLLİK", "KONSTİTUSİYA", "MƏDƏNİYYƏT"]

# --- 🖱 CALLBACKS ---
@dp.callback_query(F.data.in_({"start_game", "show_top", "show_daily"}))
async def callbacks(callback: types.CallbackQuery):
    if callback.message.chat.type == ChatType.PRIVATE:
        await callback.answer("⚠️ Bu düymə yalnız qruplarda işləyir!", show_alert=True)
        return

    if callback.data == "start_game":
        if not game["active"]:
            game["active"] = True
            game["main_word"] = random.choice(WORDS_BANK)
            game["found_words"] = []
            await callback.message.answer(f"🎮 **Oyun başladı!**\n⭐ {'  '.join(game['main_word'])}")
        else:
            await callback.answer("⚠️ Oyun artıq davam edir!")
    
    elif callback.data == "show_top":
        await callback.message.answer(await get_ranking("total"))
    
    elif callback.data == "show_daily":
        await callback.message.answer(await get_ranking("daily"))
    await callback.answer()

# --- 🐍 OYUN LOGİKASI ---
@dp.message()
async def game_handler(message: types.Message):
    if not game["active"] or message.chat.type == ChatType.PRIVATE or not message.text or message.text.startswith("/"):
        return

    word = message.text.strip().upper()
    if word in game["found_words"]: return

    # Hərf yoxlanışı
    main_chars = list(game["main_word"])
    is_valid = True
    for char in word:
        if char in main_chars: main_chars.remove(char)
        else: is_valid = False; break

    if is_valid and len(word) >= 2 and word in AZ_WORDS:
        game["found_words"].append(word)
        add_score(message.from_user.id, message.from_user.first_name, len(word))
        
        await message.reply(
            f"🐍\n**{word.capitalize()}**\n"
            f"🐍 👍 **Cavab Doğrudur!**\n"
            f"**siz {len(word)} xal qazandınız**\n\n"
            f"⭐  {'  '.join(game['main_word'])}"
        )

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
