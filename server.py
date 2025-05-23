from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
import base64
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔐 مفتاح OpenRouter API
OPENROUTER_API_KEY = "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"

# ✅ الصفحة الرئيسية تعرض صفحة الهبوط
@app.route('/')
def home():
    return render_template('index.html')

# ✅ صفحات HTML (Frontend)
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/designer')
def designer():
    return render_template('designer.html')

@app.route('/confirm-design')
def confirm_design():
    return render_template('confirm-design.html')

# ✅ توليد صورة بالذكاء الاصطناعي
def generate_ai_image(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token r8_NCZAqHJpI7mgxnopzGtikPhoFVvr4BH2l9N5y",
        "Content-Type": "application/json"
    }
    payload = {
        "version": "cc201eaa92792811a960a37f1c5c2f99ef99e320d7299b153c36f48a6b5a1a13",  # Stable Diffusion XL v1.0
        "input": {
            "prompt": prompt
        }
    }

    try:
        # إنشاء الطلب الأولي للتوليد
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 201:
            print("خطأ في بدء التوليد:", response.text)
            return None

        prediction = response.json()
        prediction_url = prediction["urls"]["get"]

        # انتظار التوليد (Polling)
        while True:
            status_response = requests.get(prediction_url, headers=headers)
            status_data = status_response.json()

            if status_data["status"] == "succeeded":
                return status_data["output"][0]  # رابط الصورة
            elif status_data["status"] == "failed":
                print("فشل التوليد:", status_data)
                return None

    except Exception as e:
        print("AI Exception:", str(e))
        return None

# ✅ استقبال بيانات التصميم
@app.route('/submit-design', methods=['POST'])
def submit_design():
    # يدعم استقبال البيانات سواء JSON أو form-data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

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

    prompt = (
        f"تصميم {product_type} بالأبعاد {dimensions}، باللون {color}، "
        f"مكان التركيب: {installation_place}، نوع الفتحة: {faucet_type}، "
        f"شكل الحافة: {edge_style}، عدد الأحواض: {sink_count}. "
        f"ملاحظات إضافية: {notes}. التصميم مودرن وفخم ومناسب للمنزل العصري."
    )

    ai_image_url = generate_ai_image(prompt)

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
        try:
            orders = json.load(f)
        except json.JSONDecodeError:
            orders = []
        orders.append(order)
        f.seek(0)
        json.dump(orders, f, indent=4, ensure_ascii=False)
        f.truncate()

    return jsonify({
        "status": "success",
        "message": "تم استلام التصميم بنجاح!",
        "aiImageUrl": ai_image_url
    })

# ✅ ضروري لتشغيل التطبيق على Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
