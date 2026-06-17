
```markdown
# Stripe to Google Sheets Automated Sync 🚀

A lightweight, enterprise-grade serverless integration that listens for successful Stripe payments and instantly logs the transaction data into a Google Sheets document. Built with Python and FastAPI.

## 🌟 Architecture & Features
* **Event-Driven:** Uses Stripe Webhooks (`checkout.session.completed`) for real-time data capture.
* **Secure:** Implements strict Stripe signature verification to prevent spoofed payloads.
* **Lightweight:** Built on FastAPI, making it incredibly fast and perfect for Serverless/Docker deployments.
* **Resilient:** Connects to Google Cloud APIs via Service Accounts for robust, headless authorization.

## ⚙️ Prerequisites
1. **Stripe Account:** Webhook endpoint configured.
2. **Google Cloud Console:** A project with Google Drive API & Google Sheets API enabled.
3. **Google Service Account:** A `credentials.json` key with Editor access to your target Google Sheet.

## 🛠️ Environment Variables
Rename `.env.example` to `.env` and configure your credentials:

```env
STRIPE_API_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret

```

## 🚀 Local Development & Testing (Stripe CLI)

1. **Install dependencies:**
```bash
pip install fastapi uvicorn stripe gspread python-dotenv

```


2. **Start the FastAPI server:**
```bash
uvicorn main:app --reload --port 8000

```


3. **Forward Stripe events to localhost (Requires Stripe CLI):**
```bash
stripe listen --forward-to localhost:8000/webhook/stripe

```


4. **Trigger a test payment:**
```bash
stripe trigger checkout.session.completed

```


*Watch your Google Sheet update in milliseconds!*

## 📦 Deployment Strategy

This service is designed for headless deployment. It is NOT recommended to run this as a local `.exe`.

* **Recommended:** Deploy to cloud platforms like Render, Railway, or Heroku.
* **Docker:** Simply containerize the application and run it on any Linux VPS (Ubuntu/Debian) using Docker Compose.

---

*Designed for reliable payment event processing and automated spreadsheet reporting.*

