import logging
import os
import requests
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Render အိပ်မပျော်စေရန် Flask Server ပြင်ဆင်ခြင်း
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Gold Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# Logging
logging.basicConfig(level=logging.INFO)

# ကမ္ဘာ့ရွှေဈေး (USD) ယူခြင်း
def get_gold_price_usd():
    try:
        url = "https://api.gold-api.com/price/XAU"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("price")
        return None
    except Exception as e:
        logging.error(f"Error fetching gold price: {e}")
        return None

# မက်ဆေ့ချ် ပို့ပေးသည့် Function (၁၀ မိနစ်တစ်ကြိမ်)
async def send_gold_update(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    world_price = get_gold_price_usd()
    
    # ပြင်ပ ဒေါ်လာ ပေါက်ဈေး (မိမိစိတ်ကြိုက် ပြင်ဆင်နိုင်သည်)
    USD_TO_MMK = 4500 
    
    if world_price:
        # 1 Kyat-tha = 0.533934 Troy Ounce
        price_per_kyattha_usd = world_price * 0.533934
        price_per_kyattha_mmk = price_per_kyattha_usd * USD_TO_MMK
        
        message = (
            f"📈 **ရွှေဈေးနှုန်း အချက်အလက်များ**\n\n"
            f"🌍 **ကမ္ဘာ့ရွှေဈေး:** ${world_price:,.2f} USD / oz\n"
            f"💵 **ဒေါ်လာလဲလှယ်နှုန်း:** {USD_TO_MMK:,} MMK\n\n"
            f"🇲🇲 **မြန်မာ့အခေါက်ရွှေ (၁ ကျပ်သား):**\n"
            f"👉 **{price_per_kyattha_mmk:,.0f} ကျပ်** (ခန့်မှန်း)\n\n"
            f"⏱️️ _(၁၀ မိနစ်တစ်ကြိမ် အလိုအလျောက် ပို့ပေးသော မက်ဆေ့ချ်ဖြစ်ပါသည်)_"
        )
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("👋 Gold Alert Bot စတင်ပါပြီ။ ၁၀ မိနစ်တစ်ကြိမ် ဈေးနှုန်း ပို့ပေးပါမည်။")
    
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
        
    context.job_queue.run_repeating(
        send_gold_update,
        interval=600,
        first=1,
        chat_id=chat_id,
        name=str(chat_id)
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text("🛑 ရွှေဈေး Alert များကို ရပ်တန့်လိုက်ပါပြီ။")

if __name__ == '__main__':
    # Flask Background Thread
    Thread(target=run_flask, daemon=True).start()
    
    # Render Environment Variable မှ Token ကို ယူမည်
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    
    app.run_polling()
  
