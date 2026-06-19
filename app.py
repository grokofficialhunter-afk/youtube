import telebot
import yt_dlp
import os
import threading
from flask import Flask

# আপনার দেওয়া বটের আসল টোকেন
TOKEN = "7452913125:AAFd4rlPMXZ_pYGFs1CzNfWuUSwhdHar5Xs"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# Gunicorn সার্ভার যেন বটটিকে ব্যাকগ্রাউন্ডে চালু করতে পারে, তাই এটিকে এখানে রাখা হয়েছে
threading.Thread(target=bot.infinity_polling, daemon=True).start()

@app.route('/')
def home():
    return "Telegram Bot is active and running!"

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
        # ডাউনলোড অপশন কনফিগারেশন (টেলিগ্রামের ৫০ মেগাবাইট লিমিটের মধ্যে রাখার চেষ্টা করবে)
        ydl_opts = {
            'format': 'best[ext=mp4][filesize<50M]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'outtmpl': '%(id)s.%(ext)s',
            'max_filesize': 50 * 1024 * 1024 # ৫০ মেগাবাইটের বেশি হলে এরর দেবে
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text("📤 ভিডিওটি টেলিগ্রামে আপলোড করা হচ্ছে...", message.chat.id, msg.message_id)
            
            # টেলিগ্রামে সরাসরি ভিডিও ফাইল পাঠানো
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=info.get('title'))
            
            # কাজ শেষ হলে সার্ভার থেকে ফাইল ডিলিট করা
            os.remove(filename)
            bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ দুঃখিত! ভিডিওটি পাঠানো যায়নি। ফাইলটি খুব বড় হতে পারে।\nError: {str(e)}", message.chat.id, msg.message_id)
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
