import telebot
import yt_dlp
import os
from flask import Flask

# @BotFather থেকে পাওয়া টোকেনটি এখানে দিন
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7452913125:AAE0nVKPaPe6RkIS3gV51MSlUbHg-QwvRcM")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is active!"

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
        # ডাউনলোড অপশন কনফিগারেশন
        # টেলিগ্রামের লিমিটের কারণে আমরা ৭২০পি বা তার চেয়ে কম রেজোলিউশন ডাউনলোড করব
        ydl_opts = {
            'format': 'best[ext=mp4][filesize<50M]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'outtmpl': '%(id)s.%(ext)s',
            'max_filesize': 50 * 1024 * 1024 # ৫০ মেগাবাইটের বেশি হলে ডাউনলোড করবে না
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text("📤 ভিডিওটি টেলিগ্রামে আপলোড করা হচ্ছে...", message.chat.id, msg.message_id)
            
            # টেলিগ্রামে ভিডিও পাঠানো
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=info.get('title'))
            
            # কাজ শেষ হলে সার্ভার থেকে ফাইলটি ডিলিট করে দেওয়া (স্পেস বাঁচানোর জন্য)
            os.remove(filename)
            bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ দুঃখিত! ভিডিওটি পাঠানো যায়নি। ফাইলটি ৫০ মেগাবাইটের বড় হতে পারে।\nError: {str(e)}", message.chat.id, msg.message_id)
        # যদি ফাইল ডাউনলোড হয়ে থাকে কিন্তু আপলোড ব্যর্থ হয়, তবে ফাইল ডিলিট করা
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

# Render-এর জন্য বটের পোলিং রান করা
if __name__ == '__main__':
    # Render ব্যাকগ্রাউন্ডে রান রাখার জন্য Flask ব্যবহার করে
    import threading
    threading.Thread(target=bot.infinity_polling).start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
