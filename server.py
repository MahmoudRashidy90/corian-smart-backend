from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import base64
from datetime import datetime
import requests  # استخدمنا requests بدل openai

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔐 مفتاح OpenRouter API (استبدله بمفتاحك الحقيقي)
OPENROUTER_API_KEY = "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"

# ✅ راوت الصفحة الرئيسية لتفادي خطأ Not Found
@app.route('/')
def home():
    return "Corian Designer Backend is running."

def generate_ai_image(prompt):
    url = "https://openrouter.ai/api/v1/generate"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://corian-castle.com",  # عدّل لو عندك دومين
        "X-Title": "Corian Castle Smart Designer"
    }
    payload = {
        "model": "stability-ai/sdxl",
        "prompt": prompt,
        "num_images": 1,
        "size": "1024x1024"
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data["data"][0]["url"]
    else:
        return None

@app.route('/submit-design', methods=['POST'])
def submit_design():
    data = request.json
    product_type = data.get('productType')
    dimensions = data.get('dimensions')
    color = data.get('color')
    notes = data.get('notes')
    image_data = data.get('image')  # base64 image
installation_place = data.get('installationPlace')
faucet_type = data.get('faucetType')
edge_style = data.get('edgeStyle')
sink_count = data.get('sinkCount')

    filename = None
    if image_data and image_data.startswith("data:image"):
        try:
            header, encoded = image_data.split(",", 1)
            binary_data = base64.b64decode(encoded)
            filename = f"design_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            with open(filepath, "wb") as f:
                f.write(binary_data)
        except Exception as e:
            return jsonify({"status": "error", "message": f"خطأ في حفظ الرسم: {str(e)}"}), 400

    # 🧠 توليد صورة من AI بناءً على التصميم
    prompt = (
    f"تصميم {product_type} بالأبعاد {dimensions}، باللون {color}، "
    f"مكان التركيب: {installation_place}، نوع الفتحة: {faucet_type}، "
    f"شكل الحافة: {edge_style}، عدد الأحواض: {sink_count}. "
    f"ملاحظات إضافية: {notes}. التصميم مودرن وفخم ومناسب للمنزل العصري."
)

    ai_image_url = generate_ai_image(prompt)

    # حفظ الطلب في JSON
    order = {
    "productType": product_type,
    "dimensions": dimensions,
    "color": color,
    "notes": notes,
    "installationPlace": installation_place,
    "faucetType": faucet_type,
    "edgeStyle": edge_style,
    "sinkCount": sink_count,
    "imageFilename": filename,
    "aiImageUrl": ai_image_url
}


    if not os.path.exists("smart_orders.json"):
        with open("smart_orders.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)

    with open("smart_orders.json", "r+", encoding="utf-8") as f:
        orders = json.load(f)
        orders.append(order)
        f.seek(0)
        json.dump(orders, f, indent=4, ensure_ascii=False)

    return jsonify({
        "status": "success",
        "message": "تم استلام التصميم بنجاح!",
        "aiImageUrl": ai_image_url
    })
