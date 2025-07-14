import telebot
from PIL import Image
import pytesseract
import io
import os
from flask import Flask, request
import requests

# إعداد مسار Tesseract (سيتم إعداده في Docker)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# إعداد Flask
app = Flask(__name__)

# إعداد البوت
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')  # سيتم إعداده في Render

# إعداد Webhook
bot.remove_webhook()  # إزالة أي Webhook سابق
bot.set_webhook(url=WEBHOOK_URL + '/' + TOKEN)

# معالجة الأوامر /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحبًا! أرسل صورة تحتوي على نص وسأقوم باستخراج كلمة 'عقار' منها.")

# معالجة الصور
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # الحصول على الصورة
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        response = requests.get(file_url)
        
        # حفظ الصورة مؤقتًا
        with open('temp_image.jpg', 'wb') as new_file:
            new_file.write(response.content)
        
        # تحميل الصورة باستخدام PIL
        image = Image.open('temp_image.jpg')
        
        # استخراج النص باستخدام pytesseract
        text = pytesseract.image_to_string(image, lang='ara')
        
        # البحث عن كلمة "عقار"
        if 'عقار' in text:
            bot.reply_to(message, "تم العثور على كلمة 'عقار' في الصورة!")
        else:
            bot.reply_to(message, "لم يتم العثور على كلمة 'عقار' في الصورة.")
        
        # إعادة إرسال الصورة
        with open('temp_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo)
        
        # حذف الصورة المؤقتة
        os.remove('temp_image.jpg')
        
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {str(e)}")

# مسار Webhook
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
