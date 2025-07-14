import telebot
from PIL import Image, ImageEnhance
import pytesseract
import io
import os
from flask import Flask, request
import requests
import logging

# إعداد تسجيل الرسائل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد مسار Tesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# إعداد Flask
app = Flask(__name__)

# إعداد البوت
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

# إعداد Webhook
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL + '/' + TOKEN)

# معالجة الأوامر /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحبًا! أرسل صورة تحتوي على نص وسأقوم باستخراج كلمة 'عقار' منها.")

# معالجة الصور
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        response = requests.get(file_url)
        
        with open('temp_image.jpg', 'wb') as new_file:
            new_file.write(response.content)
        
        # تحميل وتحسين الصورة
        image = Image.open('temp_image.jpg')
        
        # تحويل الصورة إلى لون رمادي
        image = image.convert('L')
        
        # تحسين التباين
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(3.0)
        
        # استخراج النص
        text = pytesseract.image_to_string(image, lang='ara+eng', config='--psm 6')
        logger.info("النص المستخرج: %s", text)  # تسجيل النص المستخرج
        
        if 'عقار' in text.lower() or 'aqar' in text.lower():
            bot.reply_to(message, "تم العثور على كلمة 'عقار' في الصورة!")
        else:
            bot.reply_to(message, "لم يتم العثور على كلمة 'عقار' في الصورة. النص المستخرج: " + text)
        
        with open('temp_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo)
        
        os.remove('temp_image.jpg')
        
    except Exception as e:
        logger.error("حدث خطأ: %s", str(e))  # تسجيل الأخطاء
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
