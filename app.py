import telebot
import yt_dlp
import os
from flask import Flask, request

# ❗ আপনার নতুন টোকেনটি এখানে আপডেট করা হয়েছে
TOKEN = "7452913125:AAHAxtuTV6lR28LRLVD8Ms9ccKDlCPDYTco"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# Render-এর আপনার সাবডোমেন লিঙ্ক
RENDER_URL = "https://youtube-cucg.onrender.com"

@app.route('/')
def home():
    # 💥 এখানে ব্রাউজারে ঢোকার সাথে সাথে প্রতিবার Webhook নতুন করে সেট হবে
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        return "Telegram Bot is active and Webhook successfully updated!"
    except Exception as e:
        return f"Bot is running, but Webhook error: {str(e)}"

# টেলিগ্রাম এই রুটে মেসেজ পাঠাবে
@app.route(f'/{TOKEN}', methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Invalid Request', 403

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 স্বাগতম! আমাকে যেকোনো ইউটিউব ভিডিওর লিঙ্ক দিন, আমি সেটি আপনাকে ভিডিও ফাইল হিসেবে পাঠিয়ে দেব।")

@bot.message_handler(func=lambda message: True)
def download_and_send_video(message):
    url = message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        bot.reply_to(message, "❌ দয়া করে একটি সঠিক ইউটিউব ভিডিও লিঙ্ক দিন।")
        return

    msg = bot.reply_to(message, "⏳ ভিডিওটি প্রসেস করা হচ্ছে... কিছু সময় অপেক্ষা করুন।")

    try:
        cookies_path = 'cookies.txt'
        if not os.path.exists(cookies_path):
            with open(cookies_path, 'w') as f: pass

        ydl_opts = {
            'format': 'best[ext=mp4][filesize<50M]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'outtmpl': '%(id)s.%(ext)s',
            'max_filesize': 50 * 1024 * 1024,
            'cookiefile': cookies_path,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text("📤 ভিডিওটি টেলিগ্রামে আপলোড করা হচ্ছে...", message.chat.id, msg.message_id)
            
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=info.get('title'))
            
            os.remove(filename)
            bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ দুঃখিত! ভিডিওটি পাঠানো যায়নি। ফাইলটি খুব বড় হতে পারে অথবা কুকিজ আপডেট করতে হবে।\nError: {str(e)}", message.chat.id, msg.message_id)
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
