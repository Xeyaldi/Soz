import os
import asyncio
import random
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ChatType

# Heroku-da Config Vars hissəsinə BOT_TOKEN adı ilə əlavə edəcəksən
API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN, parse_mode="Markdown")
dp = Dispatcher()

# --- 🗄 VERİLƏNLƏR BAZASI (Məlumatların itməməsi üçün) ---
def init_db():
    conn = sqlite3.connect('soz_oyunu.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, name TEXT, 
                       total_score INTEGER DEFAULT 0, daily_score INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def add_score(user_id, name, points):
    conn = sqlite3.connect('soz_oyunu.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
    cursor.execute("UPDATE users SET total_score = total_score + ?, daily_score = daily_score + ?, name = ? WHERE user_id = ?", 
                   (points, points, name, user_id))
    conn.commit()
    conn.close()

# --- 🎮 OYUN MEXANİKMASI ---
game = {"active": False, "main_word": "", "found_words": []}
# Söz bazası (istədiyin qədər artıra bilərsən)
WORDS_BANK = ["MÜBALİĞƏLİ", "AZƏRBAYCAN", "ELEKTRONİKA", "KİBERNETİKA", "MÜSTƏQİLLİK", "KAMPANİYA", "KONSTİTUSİYA", "MƏDƏNİYYƏT", "HÜQUQŞÜNAS", "REDAKSİYA"]

# --- 🏠 START MESAJI VƏ BUTONLAR ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    # Oyun və Reytinq düymələri
    builder.row(types.InlineKeyboardButton(text="🎮 Oyuna Başla", callback_data="start_game"))
    builder.row(
        types.InlineKeyboardButton(text="🏆 Ümumi Top 13", callback_data="show_top"),
        types.InlineKeyboardButton(text="📊 Günlük Top 13", callback_data="show_daily")
    )
    # Sahib və Qrup düymələri (Sənin istədiyin tərzdə)
    builder.row(types.InlineKeyboardButton(text="👑 Sahib: aysberqqq", url="https://t.me/aysberqqq"))
    builder.row(types.InlineKeyboardButton(text="💬 Söhbət Qrupu: @sohbetqruprc", url="https://t.me/sohbetqruprc"))
    
    welcome_text = (
        f"✨ **Salam {message.from_user.first_name}!**\n\n"
        "Söz Oyunu botuna xoş gəldin. Ana sözün içindən yeni sözlər tap, xal qazan və sıralamada lider ol!\n\n"
        "🚀 **Başlamaq üçün aşağıdakı düymələrdən istifadə et:**"
    )
    await message.answer(welcome_text, reply_markup=builder.as_markup())

# --- 🏆 REYTİNQ SİSTEMİ (Top 13) ---
async def get_ranking(data_type="total"):
    column = "total_score" if data_type == "total" else "daily_score"
    title = "🏆 Ümumi Sıralama (Top 13)" if data_type == "total" else "📊 Günlük Sıralama (Top 13)"
    
    conn = sqlite3.connect('soz_oyunu.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT name, {column} FROM users WHERE {column} > 0 ORDER BY {column} DESC LIMIT 13")
    rows = cursor.fetchall()
    conn.close()
    
    text = f"✨ **{title}**\n━━━━━━━━━━━━━━\n"
    if not rows:
        text += "❌ Hələ ki heç kim xal qazanmayıb."
    for i, row in enumerate(rows, 1):
        text += f"{i}. {row[0]} ➜ `{row[1]}` xal\n"
    return text

# --- ⌨️ KOMANDALAR (/umumi, /gunluk) ---
@dp.message(Command("umumi"))
async def cmd_umumi(message: types.Message):
    res = await get_ranking("total")
    await message.answer(res)

@dp.message(Command("gunluk"))
async def cmd_gunluk(message: types.Message):
    res = await get_ranking("daily")
    await message.answer(res)

@dp.message(Command("startsoz"))
async def start_logic(message: types.Message):
    # Şəxsi mesajda yazılanda qadağan et
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("⚠️ **Bağışlayın, bu komanda yalnız qruplar üçün nəzərdə tutulub!**")
        return
        
    if game["active"]:
        await message.answer("⚠️ Oyun artıq davam edir!")
        return
    
    game["active"] = True
    game["main_word"] = random.choice(WORDS_BANK)
    game["found_words"] = []
    display_word = "  ".join(game["main_word"])
    await message.answer(f"🎮 **Oyun başladı!**\n⭐ {display_word}")

# --- 🐍 OYUNUN ÖZÜ (SS-dəki vizual format) ---
@dp.message()
async def game_handler(message: types.Message):
    # Oyun aktiv deyilsə və ya komandadırsa baxma
    if not game["active"] or not message.text or message.text.startswith("/"):
        return

    user_word = message.text.strip().capitalize()
    word_upper = user_word.upper()
    
    # Təkrar söz yoxlaması
    if word_upper in game["found_words"]:
        return 

    # Hərf yoxlaması (söz ana sözün içində varmı?)
    temp_main = list(game["main_word"])
    is_valid = True
    for char in word_upper:
        if char in temp_main:
            temp_main.remove(char)
        else:
            is_valid = False; break

    if is_valid and len(word_upper) >= 2:
        game["found_words"].append(word_upper)
        points = len(word_upper)
        add_score(message.from_user.id, message.from_user.full_name, points)
        
        display_word = "  ".join(game["main_word"])
        # Sənin atdığın SS-dəki mesajın eynisi:
        response = (
            f"🐍\n"
            f"**{user_word}**\n"
            f"🐍 👍 **Cavab Doğrudur!**\n"
            f"**siz {points} xal qazandınız**\n\n"
            f"⭐  {display_word}"
        )
        await message.reply(response)

# --- 🖱 DÜYMƏLƏR ÜÇÜN HANDLERLƏR ---
@dp.callback_query(F.data == "show_top")
async def cb_top(callback: types.CallbackQuery):
    res = await get_ranking("total")
    await callback.message.answer(res)
    await callback.answer()

@dp.callback_query(F.data == "show_daily")
async def cb_daily(callback: types.CallbackQuery):
    res = await get_ranking("daily")
    await callback.message.answer(res)
    await callback.answer()

@dp.callback_query(F.data == "start_game")
async def cb_start(callback: types.CallbackQuery):
    if callback.message.chat.type == ChatType.PRIVATE:
        await callback.answer("Bu düymə yalnız qruplarda işləyir!", show_alert=True)
    else:
        await start_logic(callback.message)
    await callback.answer()

# --- 🚀 BOTU İŞƏ SALMA ---
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
