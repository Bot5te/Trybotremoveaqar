import telebot
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
import io
import os
from flask import Flask, request
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

app = Flask(__name__)

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL + '/' + TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحبًا! أرسل صورة تحتوي على نص وسأقوم باستخراج كلمة 'عقار' منها.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        response = requests.get(file_url)
        
        with open('temp_image.jpg', 'wb') as new_file:
            new_file.write(response.content)
        
        image = Image.open('temp_image.jpg')
        image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(3.0)
        
        # تحويل إلى أبيض وأسود
        image = image.point(lambda x: 0 if x < 128 else 255, '1')
        
        # قص المنطقة العلوية
        box = (image.width // 2 - 50, 0, image.width // 2 + 50, 50)
        cropped_image = image.crop(box)
        
        text = pytesseract.image_to_string(cropped_image, lang='ara+eng', config='--psm 11 --oem 3')
        logger.info("النص المستخرج: %s", text)
        
        if 'عقار' in text.lower() or 'aqar' in text.lower():
            bot.reply_to(message, "تم العثور على كلمة 'عقار' في الصورة!")
        else:
            bot.reply_to(message, "لم يتم العثور على كلمة 'عقار' في الصورة. النص المستخرج: " + text)
        
        with open('temp_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo)
        
        os.remove('temp_image.jpg')
        
    except Exception as e:
        logger.error("حدث خطأ: %s", str(e))
        bot.reply_to(message, f"حدث خطأ: {str(e)}")

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
