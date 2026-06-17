import os
import json
import stripe
import gspread
from fastapi import FastAPI, Request, HTTPException, Header
from dotenv import load_dotenv
from datetime import datetime

# 1. 加载环境变量
load_dotenv()
stripe.api_key = os.getenv("STRIPE_API_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# 2. 智能初始化 Google Sheets 客户端 (双栖模式)
google_creds_str = os.getenv("GOOGLE_CREDENTIALS_JSON")

if google_creds_str:
    # 云端生产环境：从环境变量读取 JSON 字符串
    creds_dict = json.loads(google_creds_str)
    gc = gspread.service_account_from_dict(creds_dict)
    print("☁️ [System] Using environment variables for Google Auth.")
else:
    # 本地开发环境：兜底读取本地文件
    gc = gspread.service_account(filename='credentials.json')
    print("💻 [System] Using local credentials.json for Google Auth.")

app = FastAPI()


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()

    # 3. 验证 Stripe 签名
    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, endpoint_secret)
    except Exception as e:
        print(f"❌ 签名验证失败: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature or payload")

    # 4. 捕捉支付成功事件并提取核心数据
    if event.type == 'checkout.session.completed':
        session = event.data.object

        customer_details = getattr(session, 'customer_details', None)
        email = getattr(customer_details, 'email', 'No email') if customer_details else 'No email'

        amount = getattr(session, 'amount_total', 0) / 100.0
        currency = getattr(session, 'currency', '').upper()
        status = getattr(session, 'payment_status', 'Unknown')
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"💰 捕捉到支付! 用户: {email}, 金额: {amount} {currency}")

        # 5. 瞬间写入 Google Sheets
        try:
            sheet = gc.open("Stripe Sync Test").sheet1
            row_data = [time_now, email, amount, currency, status]
            sheet.append_row(row_data)
            print("✅ 成功写入 Google Sheets!")
        except Exception as e:
            print(f"❌ 写入表格失败: {e}")

    return {"status": "success"}