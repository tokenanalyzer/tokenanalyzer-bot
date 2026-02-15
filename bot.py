import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = "7552972889:AAG_VJ_pLlAj3_mCmihlCPeIHN-0UNTvT6s"

user_tokens = {}

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Full Analysis", callback_data="full")],
        [InlineKeyboardButton("Risk Score", callback_data="risk"),
         InlineKeyboardButton("Pump Check", callback_data="pump")],
        [InlineKeyboardButton("Price", callback_data="price"),
         InlineKeyboardButton("Liquidity", callback_data="liquidity")],
        [InlineKeyboardButton("Volume", callback_data="volume")]
    ])

def fetch_token_data(token):

    try:

        url = f"https://api.dexscreener.com/latest/dex/search/?q={token}"

        res = requests.get(url)

        data = res.json()

        pair = data["pairs"][0]

        liquidity = float(pair["liquidity"]["usd"])

        volume = float(pair["volume"]["h24"])

        return {
            "name": pair["baseToken"]["name"],
            "price": pair["priceUsd"],
            "liquidity": liquidity,
            "volume": volume,
            "chain": pair["chainId"],
            "dex": pair["dexId"]
        }

    except:
        return None

def calculate_risk(liquidity, volume):

    score = 0

    if liquidity > 100000:
        score += 40
    elif liquidity > 50000:
        score += 30
    elif liquidity > 10000:
        score += 20
    else:
        score += 5

    if volume > 100000:
        score += 40
    elif volume > 50000:
        score += 30
    elif volume > 10000:
        score += 20
    else:
        score += 5

    if score >= 70:
        verdict = "LOW RISK SAFE"
    elif score >= 40:
        verdict = "MODERATE RISK"
    else:
        verdict = "HIGH RISK WARNING"

    return score, verdict

def detect_pump(liquidity, volume):

    ratio = volume / liquidity if liquidity > 0 else 0

    if ratio > 1:
        return "POSSIBLE PUMP DETECTED"
    elif ratio > 0.5:
        return "HIGH ACTIVITY"
    else:
        return "NORMAL ACTIVITY"

async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):

    token = update.message.text.strip()

    user_tokens[update.effective_user.id] = token

    await update.message.reply_text(
        "Token detected. Select analysis:",
        reply_markup=get_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_tokens:
        await query.message.reply_text("Send token first.")
        return

    token = user_tokens[user_id]

    data = fetch_token_data(token)

    if not data:
        await query.message.reply_text("Token not found.")
        return

    score, verdict = calculate_risk(data["liquidity"], data["volume"])

    pump = detect_pump(data["liquidity"], data["volume"])

    if query.data == "full":

        text = (
            f"Name: {data['name']}\n"
            f"Chain: {data['chain']}\n"
            f"DEX: {data['dex']}\n\n"
            f"Price: ${data['price']}\n"
            f"Liquidity: ${data['liquidity']}\n"
            f"Volume: ${data['volume']}\n\n"
            f"Risk Score: {score}/80\n"
            f"Risk Verdict: {verdict}\n\n"
            f"Pump Status: {pump}"
        )

    elif query.data == "risk":

        text = f"Risk Score: {score}/80\nVerdict: {verdict}"

    elif query.data == "pump":

        text = f"Pump Status: {pump}"

    elif query.data == "price":

        text = f"Price: ${data['price']}"

    elif query.data == "liquidity":

        text = f"Liquidity: ${data['liquidity']}"

    elif query.data == "volume":

        text = f"Volume: ${data['volume']}"

    await query.message.reply_text(text, reply_markup=get_keyboard())

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token))

    app.add_handler(CallbackQueryHandler(button_handler))

    print("TokenAnalyzer Pump Detection LIVE")

    app.run_polling()

if __name__ == "__main__":
    main()
