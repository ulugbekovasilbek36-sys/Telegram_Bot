import asyncio
import os
import uuid
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from yt_dlp import YoutubeDL

# --- KONFIGURATSIYA ---
TOKEN = "8525511276:AAFjcV7l5HkIf9oAMAkL_2_m7iVzUO5ZGIM"
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- YUKLASH FUNKSIYASI ---
def download_media(url: str, user_id: int, mode: str) -> str:
    uid = uuid.uuid4().hex[:6]
    base_name = f"{mode}_{user_id}_{uid}"
    
    opts = {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "noplaylist": True,
        "outtmpl": f"{base_name}.%(ext)s",
        "socket_timeout": 60,
        "retries": 15,
        "fragment_retries": 15,
        "wait_for_video": (2, 6),
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "geo_bypass": True,
    }

    if mode == "v":
        opts["format"] = "best[height<=480][filesize<50M]/best"
    else:
        opts["format"] = "bestaudio/best"

    with YoutubeDL(opts) as ydl:
        ydl.download([url])

    for ext in ("mp4", "mp3", "m4a", "webm", "mkv"):
        path = f"{base_name}.{ext}"
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Video topilmadi yoki yuklashda xato bo'ldi")

# --- HANDLERLAR ---
@dp.message(F.text.regexp(r"https?://\S+"))
async def handle_link(message: types.Message):
    user_id = message.from_user.id
    url = message.text.strip()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎥 Video", callback_data=f"v_{user_id}"),
         InlineKeyboardButton(text="🎵 Audio", callback_data=f"a_{user_id}")]
    ])
    await message.reply(f"📥 Format tanlang:\n{url}", reply_markup=kb)

@dp.callback_query(F.data.startswith(("v_", "a_")))
async def process_callback(callback: types.CallbackQuery):
    data = callback.data.split("_")
    mode, owner_id = data[0], int(data[1])

    if callback.from_user.id != owner_id:
        return await callback.answer("❗️ Bu sizning so'rovingiz emas!", show_alert=True)

    url = callback.message.text.split("\n")[-1]
    
    await callback.answer()
    status_msg = await callback.message.answer("⚡️ Yuklash boshlandi...")

    file_path = None
    try:
        loop = asyncio.get_running_loop()
        file_path = await loop.run_in_executor(None, download_media, url, owner_id, mode)

        if os.path.getsize(file_path) > 50 * 1024 * 1024:
            await callback.message.answer("⚠️ Fayl hajmi 50 MB dan katta.")
            return

        input_file = FSInputFile(file_path)
        if mode == "v":
            await callback.message.answer_video(video=input_file, caption="✅ @Navo_ai_bot")
        else:
            await callback.message.answer_audio(audio=input_file, caption="✅ @Navo_ai_bot")
        
        await status_msg.delete()

    except Exception as e:
        await callback.message.answer(f"❌ Xato: {str(e)[:100]}")
    finally:
        if file_path and os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass

@dp.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await message.reply("👋 Salom! YouTube yoki Instagram link yuboring.")

# --- ASOSIY QISM (XATOLIK SHU YERDA EDI) ---
async def main():
    print("🚀 Bot optimallashtirilgan rejimda ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Bot to'xtatildi.")
