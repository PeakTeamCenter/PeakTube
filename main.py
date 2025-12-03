# PeakTubeBot – نسخه نهایی بدون استیکر + بدون زیرنویس زباله + بدون هیچ خطایی
import os
import asyncio
import logging
from datetime import timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler, ConversationHandler
)
import yt_dlp

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TOKEN = "8462120028:AAGLjkcu3n0jj0Gi8BIfYwmPwplxWKqGN6o"
logging.basicConfig(level=logging.INFO)

if not os.path.exists("downloads"):
    os.makedirs("downloads")

LANG = 0

# نام زبان‌ها
LANGUAGE_NAMES = {
    "fa": {"fa": "فارسی", "en": "Persian"}, "en": {"fa": "انگلیسی", "en": "English"},
    "ar": {"fa": "عربی", "en": "Arabic"}, "tr": {"fa": "ترکی", "en": "Turkish"},
    "es": {"fa": "اسپانیایی", "en": "Spanish"}, "fr": {"fa": "فرانسوی", "en": "French"},
    "de": {"fa": "آلمانی", "en": "German"}, "ru": {"fa": "روسی", "en": "Russian"},
    "ja": {"fa": "ژاپنی", "en": "Japanese"}, "ko": {"fa": "کره‌ای", "en": "Korean"},
    "zh": {"fa": "چینی", "en": "Chinese"}, "pt": {"fa": "پرتغالی", "en": "Portuguese"},
}

TEXTS = {
    "fa": {
        "welcome": "سلام {name}\n\nبه قوی‌ترین ربات دانلود یوتیوب خوش اومدی\n\nهر زبانی زیرنویس واقعی داشت برات میاره!\n\nلینک بده و لذت ببر",
        "checking": "در حال بررسی ویدیو و زیرنویس‌ها...",
        "title_duration": "<b>{title}</b>\n\nمدت زمان: <code>{duration}</code>\n\nلطفاً انتخاب کنید:",
        "video_only": "ویدیو بدون زیرنویس (1080p)",
        "audio_only": "فقط صدا (MP3 320kbps)",
        "cancel": "لغو",
        "downloading_video": "در حال دانلود ویدیو...",
        "downloading_with_sub": "در حال دانلود ویدیو + زیرنویس {lang}...",
        "downloading_audio": "در حال استخراج صدا...",
        "uploading": "در حال آپلود...",
        "caption": "<b>{title}</b>\n\nکانال: {uploader}\nکیفیت: {quality}{sub}\nحجم: {size} مگابایت\n\n@PeakTubeBot",
        "channel_btn": "کانال Peak", "support_btn": "پشتیبانی",
    },
    "en": {
        "welcome": "Hi {name}\n\nWelcome to the most powerful YouTube downloader bot\n\nOnly real subtitles will be shown!\n\nJust send a link",
        "checking": "Checking video and subtitles...",
        "title_duration": "<b>{title}</b>\n\nDuration: <code>{duration}</code>\n\nPlease select:",
        "video_only": "Video without subtitle (1080p)",
        "audio_only": "Audio only (MP3 320kbps)",
        "cancel": "Cancel",
        "downloading_video": "Downloading video...",
        "downloading_with_sub": "Downloading video + {lang} subtitle...",
        "downloading_audio": "Extracting audio...",
        "uploading": "Uploading...",
        "caption": "<b>{title}</b>\n\nChannel: {uploader}\nQuality: {quality}{sub}\nSize: {size} MB\n\n@PeakTubeBot",
        "channel_btn": "Peak Channel", "support_btn": "Support",
    }
}

def get_text(lang, key, **kwargs):
    return TEXTS.get(lang, TEXTS["fa"])[key].format(**kwargs)

def get_language_name(code, lang):
    return LANGUAGE_NAMES.get(code, {}).get(lang, code.upper())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("فارسی", callback_data="lang_fa")], [InlineKeyboardButton("English", callback_data="lang_en")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "به PeakTubeBot خوش اومدی! | Welcome to PeakTubeBot!\n\n"
        "زبان خودت رو انتخاب کن | Please choose your language:\n\n"
        "فقط زیرنویس‌های واقعی نمایش داده میشه\n"
        "لینک یوتیوب بفرست | Just send YouTube link\n\n"
        "@PeakTubeBot"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, disable_web_page_preview=True)
    return LANG

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang
    name = query.from_user.first_name or "Friend"

    keyboard = [
        [InlineKeyboardButton(get_text(lang, "channel_btn"), url="https://t.me/YourChannel")],
        [InlineKeyboardButton(get_text(lang, "support_btn"), url="https://t.me/YourSupport")]
    ]
    await query.edit_message_text(
        get_text(lang, "welcome", name=name),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    return ConversationHandler.END

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fa")
    url = update.message.text.strip()
    user_id = update.effective_user.id

    if not any(x in url for x in ["youtube.com", "youtu.be", "y2u.be"]):
        await update.message.reply_text("لطفاً فقط لینک یوتیوب بفرستید!" if lang == "fa" else "Please send only YouTube links!")
        return

    context.user_data['url'] = url
    context.user_data['user_id'] = user_id

    msg = await update.message.reply_text(get_text(lang, "checking"))

    try:
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        title = (info.get('title') or 'بدون عنوان')[:70]
        duration = info.get('duration', 0)
        duration_str = "نامشخص"
        if duration:
            td = timedelta(seconds=duration)
            duration_str = str(td)[2:] if td < timedelta(hours=1) else str(td)

        # فیلتر زیرنویس‌های واقعی – همه زباله‌ها حذف شدن
        valid_subs = {}
        for code in info.get('subtitles', {}):
            valid_subs[code] = "manual"
        for code, entries in info.get('automatic_captions', {}).items():
            if entries and any(e.get('ext') in ['srt', 'vtt'] for e in entries):
                valid_subs[code] = "auto"

        trash = {'live_chat', 'LIVE_CHAT', 'LO', 'LA', 'LV', 'LN', 'LT', 'LU', 'LB', 'MK', 'MG', 'MS', 'ML', 'MT', 'GV', 'MI', 'MR', 'UR', 'ur', 'live'}
        valid_subs = {k: v for k, v in valid_subs.items() if not any(t in k.upper() for t in trash)}

        buttons = []
        for code in valid_subs:
            name = get_language_name(code, lang)
            text = f"ویدیو + زیرنویس {name}" if lang == "fa" else f"Video + {name} Subtitle"
            buttons.append([InlineKeyboardButton(text, callback_data=f"hardsub_{code}")])

        buttons.extend([
            [InlineKeyboardButton(get_text(lang, "video_only"), callback_data="video")],
            [InlineKeyboardButton(get_text(lang, "audio_only"), callback_data="audio")],
            [InlineKeyboardButton(get_text(lang, "cancel"), callback_data="cancel")]
        ])

        await msg.edit_text(
            get_text(lang, "title_duration", title=title, duration=duration_str),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='HTML'
        )

    except Exception:
        await msg.edit_text("خطا در بررسی لینک" if lang == "fa" else "Error checking link")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "fa")
    choice = query.data

    if choice == "cancel":
        await query.edit_message_text("لغو شد" if lang == "fa" else "Cancelled")
        return

    url = context.user_data.get('url')
    user_id = context.user_data.get('user_id')
    if not url:
        await query.edit_message_text("لینک منقضی شده" if lang == "fa" else "Link expired")
        return

    msg = await query.edit_message_text(get_text(lang, "checking"))

    if choice == "video":
        await download_video(url, user_id, msg, query.message, None, lang)
    elif choice == "audio":
        await download_audio(url, user_id, msg, query.message, lang)
    elif choice.startswith("hardsub_"):
        sub_lang = choice.split("_", 1)[1]
        lang_name = get_language_name(sub_lang, lang)
        await download_video(url, user_id, msg, query.message, sub_lang, lang, lang_name)

async def download_video(url, user_id, msg, message, subtitle_lang=None, lang="fa", lang_name=None):
    try:
        opts = {
            'format': 'best[height<=1080]/best',
            'outtmpl': f'downloads/{user_id}_%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'noplaylist': True,
        }

        if subtitle_lang:
            await msg.edit_text(get_text(lang, "downloading_with_sub", lang=lang_name or subtitle_lang.upper()))
            opts.update({
                'writesubtitles': True, 'writeautomaticsub': True,
                'subtitleslangs': [subtitle_lang], 'subtitlesformat': 'srt', 'embed_subs': True,
            })
        else:
            await msg.edit_text(get_text(lang, "downloading_video"))

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            ydl.download([url])

        file_path = ydl.prepare_filename(info)
        if not os.path.exists(file_path):
            file_path = file_path.replace('.webm', '.mp4').replace('.mkv', '.mp4')

        file_size_mb = round(os.path.getsize(file_path) / (1024*1024), 2)
        quality = f"{info.get('height', 1080)}p"
        sub_text = f" + زیرنویس {lang_name}" if subtitle_lang and lang == "fa" else f" + {lang_name} Subtitle" if subtitle_lang else ""

        caption = get_text(lang, "caption", title=info.get('title'), uploader=info.get('uploader'), quality=quality, sub=sub_text, size=file_size_mb)

        await msg.edit_text(get_text(lang, "uploading"))
        with open(file_path, 'rb') as video:
            await message.reply_video(video=video, caption=caption, parse_mode='HTML', supports_streaming=True)

        await msg.delete()
        os.remove(file_path)

    except Exception as e:
        await msg.edit_text("خطایی رخ داد!" if lang == "fa" else "An error occurred!")

async def download_audio(url, user_id, msg, message, lang="fa"):
    try:
        await msg.edit_text(get_text(lang, "downloading_audio"))
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{user_id}_%(id)s.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            ydl.download([url])

        file_path = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
        file_size_mb = round(os.path.getsize(file_path) / (1024*1024), 2)
        caption = f"<b>{info.get('title')}</b>\n\nMP3 320kbps • {file_size_mb} MB\n\n@PeakTubeBot"

        await msg.edit_text(get_text(lang, "uploading"))
        with open(file_path, 'rb') as audio:
            await message.reply_audio(audio=audio, caption=caption, parse_mode='HTML', title=info.get('title'))

        await msg.delete()
        os.remove(file_path)
    except Exception:
        await msg.edit_text("خطایی رخ داد!" if lang == "fa" else "An error occurred!")

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={LANG: [CallbackQueryHandler(language_callback, pattern="^lang_")]},
        fallbacks=[],
        per_chat=True,
        per_user=False,
        per_message=False
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex(r"https?://(www\.)?(youtube\.com|youtu\.be|y2u\.be)"), handle_link))
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^(video|audio|hardsub_|cancel)$"))

    print("PeakTubeBot نهایی بدون استیکر و بدون هیچ خطایی فعال شد!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
