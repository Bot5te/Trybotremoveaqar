FROM python:3.9

# تثبيت Tesseract ودعم اللغة العربية
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    && rm -rf /var/lib/apt/lists/*

# إعداد مجلد العمل
WORKDIR /app

# نسخ الملفات
COPY requirements.txt .
COPY . .

# تثبيت التبعيات
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل التطبيق
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
