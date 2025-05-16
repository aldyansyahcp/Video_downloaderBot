import os
import re
import telebot
import yt_dlp
from time import sleep

#BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
apik = "5296878013:AAFvVyUdUBGty1vNaj1LNGqU4N4P_EHpzNw"
DOWNLOAD_DIR = 'downloads'
LINKS_FILE = 'user_links.txt'

bot = telebot.TeleBot(apik)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_links = {}

def sanitize(text):
    return re.sub(r'[ \_•|=~*-.":!?*`]', '', text)

def save_link(user_id, username, url):
    user_id = str(user_id)
    found = False

    if not os.path.exists(LINKS_FILE):
        open(LINKS_FILE, 'w').close()

    with open(LINKS_FILE, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if user_id in line or url in line:
            found = True
            break

    if not found:
        with open(LINKS_FILE, 'a') as f:
            f.write(f'{user_id} | {username} | {url}\n')

@bot.message_handler(func=lambda m: m.text and m.text.startswith('http'))
def handle_link(message):
    user_id = message.from_user.id
    username = message.from_user.username or 'noname'
    url = message.text.strip()

    user_links[user_id] = url
    save_link(user_id, username, url)

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("MP3", callback_data="audio"),
        telebot.types.InlineKeyboardButton("MP4", callback_data="video")
    )

    bot.send_message(message.chat.id, "Pilih format file:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["audio", "video"])
def handle_download(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id
    format_type = call.data  # 'audio' atau 'video'

    url = user_links.get(user_id)
    if not url:
        bot.edit_message_text("Link tidak ditemukan.", chat_id, message_id)
        return

    # Edit pesan untuk menunjukkan status sementara
    status_msg = "Audio dipilih. Sedang diproses..." if format_type == 'audio' else "Video dipilih. Sedang diproses..."
    bot.edit_message_text(status_msg, chat_id, message_id)

    bot.send_chat_action(chat_id, 'upload_audio' if format_type == 'audio' else 'upload_video')
    sleep(1)

    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'warnings': False}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = sanitize(info.get('upload_date'))
            uploader = sanitize(info.get('uploader')[:30])
    except Exception:
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "Gagal mengambil informasi video.")
        return

    ext = 'mp3' if format_type == 'audio' else 'mp4'
    filename = f"{uploader}_{title}.{ext}"
    output_path = os.path.join(DOWNLOAD_DIR, filename)
    print(filename)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': output_path
    }

    if format_type == 'video':
        ydl_opts.update({
            'format': 'best',
            'merge_output_format': 'mp4',
        })
    else:
        ydl_opts.update({
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredquality': '192',
            }]
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception:
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "Gagal mendownload file.")
        return

    try:
        with open(output_path, 'rb') as f:
            if format_type == 'video':
                bot.send_video(chat_id, f)
                print("terkirim", chat_id)
            else:
                bot.send_audio(chat_id, f)
                print("terkirim", chat_id)
    except Exception as E:
        print(E)
        bot.send_message(chat_id, "Gagal mengirim file.")
    finally:
        #if os.path.exists(output_path):
            #os.remove(output_path)
        user_links.pop(user_id, None)
        # Hapus pesan status
        bot.delete_message(chat_id, message_id)

print(bot.get_me())
bot.infinity_polling()
