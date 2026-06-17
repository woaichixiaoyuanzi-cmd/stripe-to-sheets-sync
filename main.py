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
        print(f"❌ Signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature or payload")

    # 4. 捕捉支付成功事件并提取核心数据
    if event.type == 'checkout.session.completed':
        session = event.data.object

        # 提取事件的全局唯一 ID (用于防重复)
        event_id = event.id

        customer_details = getattr(session, 'customer_details', None)
        email = getattr(customer_details, 'email', 'No email') if customer_details else 'No email'

        # 获取货币种类并转换为大写
        currency = getattr(session, 'currency', '').upper()
        raw_amount = getattr(session, 'amount_total', 0)

        # 智能处理零小数货币 (Zero-decimal currencies)
        zero_decimal_currencies = ['JPY', 'KRW', 'VND', 'CLP', 'PYG']
        if currency in zero_decimal_currencies:
            amount = float(raw_amount)  # 日元等不需要除以 100
        else:
            amount = raw_amount / 100.0  # 美元等需要除以 100

        status = getattr(session, 'payment_status', 'Unknown')
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"💰 Payment captured! User: {email}, Amount: {amount} {currency}")

        # 5. 幂等性校验与写入 Google Sheets
        try:
            sheet = gc.open("Stripe Sync Test").sheet1

            # 【核心防御】读取第一列（A列）现有的所有 Event ID
            existing_ids = sheet.col_values(1)

            # 如果这个订单号已经存在，直接丢弃并返回成功告诉 Stripe 不要再发了
            if event_id in existing_ids:
                print(f"⚠️ Duplicate Webhook intercepted! Event ID {event_id} already exists. Skipping.")
                return {"status": "success", "detail": "Already processed"}

            # 组装数据，把 event_id 放在第一列
            row_data = [event_id, time_now, email, amount, currency, status]
            sheet.append_row(row_data)
            print("✅ Successfully written to Google Sheets!")

        except Exception as e:
            print(f"❌ Failed to write to sheets: {e}")

    return {"status": "success"}