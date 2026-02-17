import os
import asyncio
import random
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ChatType
from aiogram.client.default import DefaultBotProperties

# Heroku Config Vars-dan oxunacaq
API_TOKEN = os.getenv('BOT_TOKEN')

# DÜZƏLİŞ: Heroku loqlarındakı TypeError-un həlli
bot = Bot(
    token=API_TOKEN, 
    default=DefaultBotProperties(parse_mode="Markdown")
)
dp = Dispatcher()

# --- 🗄 VERİLƏNLƏR BAZASI ---
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

# --- 📚 500+ SÖZLÜK LÜĞƏT BAZASI ---
AZ_WORDS = {
    "ANA", "ATA", "BACİ", "QARDAS", "ALMA", "ARMUD", "KİTAB", "QALEM", "DEFTER", "MEKTEB", "DENİZ", "SAHİL", "VETEN", "AZERBAYCAN",
    "DÜNYA", "HEYAT", "İNSAN", "DEMİR", "GÜMÜS", "QIZIL", "BULAQ", "ORMAN", "DAGLAR", "CEYRAN", "ASLAN", "PELENG", "TÜLKÜ",
    "DOVŞAN", "SİNCAB", "MARAL", "KOTAN", "TARLA", "BUĞDA", "ARPA", "SÜFRƏ", "ÇÖRƏK", "PENDİR", "ZEYTUN", "SÜRMƏ", "KİRPİK", "GÖZLƏR",
    "BİLİK", "ELİM", "DƏRS", "USTAD", "ŞAGİRD", "TƏLƏBƏ", "MƏKTUB", "XƏBƏR", "DOST", "YOLDAŞ", "SİRR", "KÖNÜL", "SEVGİ", "ÜRƏK", "ARZU",
    "XƏYAL", "GÜNƏŞ", "BULUD", "YAĞIŞ", "KÜLƏK", "ŞAXTA", "BORAN", "DUMAN", "SƏMA", "ULDUZ", "GECƏ", "GÜNDÜZ", "SƏHƏR", "AXŞAM", "BAHAR",
    "YAY", "PAYIZ", "QIŞ", "ÇİÇƏK", "LALƏ", "BƏNÖVŞƏ", "NƏRGİZ", "YASƏMƏN", "SÜMBÜL", "SÜLALƏ", "TARİX", "MƏDƏNİYYƏT", "İNCƏSƏNƏT",
    "MÜSİQİ", "RƏQS", "MAHNI", "SƏS", "NƏFƏS", "HƏYAT", "SÜLH", "AZADLIQ", "ZƏFƏR", "QƏLƏBƏ", "BAYRAQ", "ORDU", "ƏSGƏR", "VƏTƏNDAŞ",
    "DÖVLƏT", "HÜQUQ", "ƏDALƏT", "QANUN", "SİYASƏT", "İQTİSADİYYAT", "TİCARƏT", "BAZAR", "PUL", "SƏRVƏT", "ZƏHMƏT", "İŞ", "PEŞƏ", "SƏNƏT",
    "HƏKİM", "MÜƏLLİM", "MÜHƏNDİS", "POLİS", "HAKİM", "YAZIÇI", "ŞAİR", "RESSAM", "MÜXİBİR", "ALİM", "MEMAR", "DƏRZİ", "DƏMİRÇİ", "DÜLGƏR",
    "BALIQ", "QUŞ", "KƏPƏNƏK", "ARI", "QARIŞQA", "İLAN", "QURBAĞA", "TOSBAĞA", "PİŞİK", "İT", "AT", "İNƏK", "QOYUN", "KEÇİ", "DƏVƏ", "FİL",
    "ZÜRAFƏ", "MEYMUN", "DİNOZAVR", "ƏJDƏHA", "MAŞIN", "GƏMİ", "TƏYYARƏ", "QATAR", "VELOSİPED", "METRO", "AVTOBUS", "YOL", "KÜÇƏ", "MEYDAN",
    "BİNA", "EV", "OTAQ", "PƏNCƏRƏ", "QAPI", "DAM", "HƏYƏT", "BAĞÇA", "MEŞƏ", "ÇAY", "GÖL", "OKEAN", "ADA", "SƏHRA", "VADİ", "MAĞARA",
    "DAŞ", "QUMLU", "TORPAQ", "HAVA", "OD", "SU", "KİBRİT", "ALOV", "KÖMÜR", "KÜL", "DÜYÜ", "ŞƏKƏR", "DUZ", "İSTİOT", "SÜD", "QATIQ",
    "YAĞ", "BAL", "MEYVƏ", "TƏRƏVƏZ", "BİTKİ", "AĞAC", "YARPAQ", "BUDAQ", "KÖK", "MEYVƏ", "ÜZÜM", "NAR", "HEYVA", "GİLAS", "ALBALI",
    "ƏRİK", "ŞAFTALI", "QAVUN", "QARPIZ", "LİMON", "PORTAĞAL", "MANDARİN", "BANAN", "ÇİYƏLƏK", "MƏRCİ", "NUXUD", "LOVYA", "SİRNİYYAT",
    "PAXAVA", "ŞƏKƏRBURA", "SƏMƏNİ", "NOVRUZ", "BAYRAM", "HƏDİYYƏ", "QONAQ", "SÖHBƏT", "ZARAFAT", "GÜLÜŞ", "AĞLAMAQ", "YUXU", "OYANMAQ",
    "GƏZMƏK", "QAÇMAQ", "ÜZMƏK", "UÇMAQ", "OXUMAQ", "YAZMAQ", "DÜŞÜNMƏK", "BAXMAQ", "EŞİTMƏK", "TOXUNMAQ", "İYLƏMƏK", "DADMAQ", "BİLMƏK",
    "GÖRMƏK", "ANLAMAK", "GÜCLÜ", "ZƏİF", "BÖYÜK", "KİÇİK", "UZUN", "QISA", "GENİŞ", "DAR", "AĞİR", "YÜNGÜL", "SÜRƏTLİ", "YAVAŞ", "İSTİ",
    "SOYUQ", "SƏRT", "YUMŞAQ", "GÖZƏL", "ÇİRKİN", "YAXŞI", "PİS", "DOĞRU", "YALAN", "TƏMİZ", "ÇİRKALİ", "YENİ", "KÖHNƏ", "AC", "TOX",
    "ŞİRİN", "ACI", "TURŞ", "DUZLU", "PARLAQ", "SOLĞUN", "RƏNGLİ", "AĞ", "QARA", "QIRMIZI", "MAVİ", "YAŞIL", "SARI", "NARINCI", "BƏNÖVŞƏYİ",
    "QƏHVƏYİ", "BOZ", "GÜMÜŞÜ", "QIZILI", "SƏADƏT", "BƏXT", "TALEY", "QİSMƏT", "SƏBİR", "DÖZÜM", "İNAM", "ÜMİD", "CƏSARƏT", "QORXU",
    "HƏYƏCAN", "MARAQ", "TƏƏCCÜB", "NİFRƏT", "HÖRMƏT", "QAYĞI", "ŞƏFQƏT", "VƏFA", "SƏDAQƏT", "ZƏKA", "AĞIL", "MƏNTİQ", "YADDAŞ", "DİQQƏT",
    "İRADƏ", "HƏDƏF", "MƏQSƏD", "UĞUR", "NƏTİCƏ", "SƏHV", "TƏCRÜBƏ", "HƏRƏKƏT", "DURĞUNLUQ", "DƏYİŞİKLİK", "İNKIŞAF", "TƏRƏQQİ", "SİVİLİZASİYA",
    "KOMPÜTER", "TELEFON", "İNTERNET", "PROQRAM", "OYUN", "EKRAN", "KLAVİATURA", "MOUSE", "YADDAŞ", "KAMERA", "RADİO", "TELEVİZOR", "ENERJİ",
    "İŞIQ", "BATAREYA", "SAAT", "VAXT", "ZAMAN", "ƏSR", "MİLLƏT", "XALQ", "DİL", "LÜĞƏT", "SÖZ", "CÜMLƏ", "MƏTN", "KİTABXANA", "ARXİV",
    "MUZEY", "TEATR", "KİNO", "SİRK", "STADİON", "İDMAN", "FUTBOL", "ŞAHMAT", "GÜLƏŞ", "BOKS", "QAÇIŞ", "MƏŞQ", "YARIŞ", "MÜKAFAT", "MEDAL",
    "KUBOK", "ÇEMPİON", "REKORD", "SƏYAHƏT", "TURİST", "BİLET", "OTEL", "PASPORT", "VİZA", "XƏRİTƏ", "KOMPAS", "DÜRBÜN", "ÇANTAN", "PALTAR",
    "AYAQQABI", "PAPAQ", "ƏLCƏK", "ŞƏRF", "KÖYNƏK", "ŞALVAR", "YUBKA", "PALTO", "ÇƏTİR", "EYNƏK", "SAAT", "ÜZÜK", "SIRĞA", "BOYUNBAĞI",
    "BİLEZİK", "KƏMƏR", "CİB", "PULQABI", "AYNA", "DARAG", "SABUN", "ŞAMPUN", "DƏSMAL", "YATAQ", "YASTIQ", "YORĞAN", "DÖŞƏK", "MEBEL",
    "STOL", "STUL", "DİVAN", "ŞKAF", "RƏF", "XALÇA", "PƏRDƏ", "LAMPA", "SOBA", "SOYUDUCU", "SOBA", "QAZAN", "TAVA", "BOŞQAB", "FİNCAN",
    "QAŞIQ", "VİLKA", "BIÇAQ", "SÜFRƏ", "DƏMLİK", "ÇAYDAN", "SAMOVAR", "FINDIQ", "QOZ", "BADAM", "PUSTƏ", "LEBLƏBİ", "SƏBƏT", "TORBA",
    "BALXAN", "XAN", "BALIQLAR", "ALİ", "BAĞ", "BAĞLAR", "BAĞLI", "İĞLƏ", "LİL", "MİL", "MAL", "MAĞAR", "MİLLİ", "ƏLİ", "ƏLA", "İLİ"
}

# --- 🎮 OYUN MEXANİKMASI ---
game = {"active": False, "main_word": "", "found_words": []}
WORDS_BANK = ["MÜBALİĞƏLİ", "AZƏRBAYCAN", "ELEKTRONİKA", "KİBERNETİKA", "MÜSTƏQİLLİK", "KAMPANİYA", "KONSTİTUSİYA", "MƏDƏNİYYƏT", "SİVİLİZASİYA", "TRANSFORMASİYA"]

# --- 🏠 START MESAJI ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎮 Oyuna Başla", callback_data="start_game"))
    builder.row(
        types.InlineKeyboardButton(text="🏆 Ümumi Top 13", callback_data="show_top"),
        types.InlineKeyboardButton(text="📊 Günlük Top 13", callback_data="show_daily")
    )
    builder.row(types.InlineKeyboardButton(text="👑 Sahib: aysberqqq", url="https://t.me/aysberqqq"))
    builder.row(types.InlineKeyboardButton(text="💬 Söhbət Qrupu: @sohbetqruprc", url="https://t.me/sohbetqruprc"))
    
    welcome_text = (
        f"✨ **Salam {message.from_user.first_name}!**\n\n"
        "Söz Oyunu botuna xoş gəldin. Ana sözün içindən yeni sözlər tap, xal qazan və lider ol!\n\n"
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

# --- 🐍 OYUN LOGİKASI (SS FORMATI) ---
@dp.message()
async def game_handler(message: types.Message):
    if not game["active"] or not message.text or message.text.startswith("/"):
        return

    word_upper = message.text.strip().upper()
    if word_upper in game["found_words"]:
        return 

    temp_main = list(game["main_word"])
    is_valid = True
    for char in word_upper:
        if char in temp_main:
            temp_main.remove(char)
        else:
            is_valid = False
            break

    if is_valid and len(word_upper) >= 2:
        if word_upper in AZ_WORDS:
            game["found_words"].append(word_upper)
            points = len(word_upper)
            add_score(message.from_user.id, message.from_user.first_name, points)
            
            display_word = "  ".join(game["main_word"])
            response = (
                f"🐍\n"
                f"**{word_upper.capitalize()}**\n"
                f"🐍 👍 **Cavab Doğrudur!**\n"
                f"**siz {points} xal qazandınız**\n\n"
                f"⭐  {display_word}"
            )
            await message.reply(response)

# --- 🖱 CALLBACK HANDLERS ---
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

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
