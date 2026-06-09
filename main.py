from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
)

TOKEN = "8690641497:AAGXVjkTtg72dSsIh3De_-ZW32rkhRmAcZw"

STAR_RATE = 100  # 100 نجمة = 1$

countries = {
    "iq": {"name": "العراق", "price": 2.6, "flag": "🇮🇶"},
    "us": {"name": "أمريكا", "price": 0.4, "flag": "🇺🇸"},
    "ph": {"name": "الفلبين", "price": 0.10, "flag": "🇵🇭"},
    "bd": {"name": "بنغلاديش", "price": 0.35, "flag": "🇧🇩"},
    "ru": {"name": "روسيا", "price": 0.6, "flag": "🇷🇺"},
    "pk": {"name": "باكستان", "price": 0.8, "flag": "🇵🇰"},
    "lb": {"name": "لبنان", "price": 1.6, "flag": "🇱🇧"},
}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📱 شراء رقم", callback_data="buy")]
    ]

    await update.message.reply_text(
        "👋 أهلاً بك في متجر الأرقام 💵",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# عرض الدول
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # شراء
    if query.data == "buy":
        keyboard = []

        for code, c in countries.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{c['flag']} {c['name']} - {c['price']}$",
                    callback_data=f"ct_{code}"
                )
            ])

        await query.edit_message_text(
            "📱 اختر الدولة:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # اختيار دولة
    elif query.data.startswith("ct_"):
        code = query.data.split("_")[1]
        c = countries[code]

        keyboard = [
            [
                InlineKeyboardButton(
                    "⭐ الدفع بالنجوم",
                    callback_data=f"star_{code}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🪙 الدفع OKX",
                    callback_data=f"okx_{code}"
                )
            ],
        ]

        await query.edit_message_text(
            f"{c['flag']} الدولة: {c['name']}\n💵 السعر: {c['price']}$\n\nاختر طريقة الدفع:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # OKX (يدوي حالياً)
    elif query.data.startswith("okx_"):
        code = query.data.split("_")[1]
        c = countries[code]

        await query.edit_message_text(
            f"🪙 ادفع {c['price']} USDT إلى محفظة OKX:\n\nYOUR_OKX_WALLET\n\nبعد الدفع سيتم التحقق."
        )

    # ⭐ Stars (إنشاء فاتورة)
    elif query.data.startswith("star_"):
        code = query.data.split("_")[1]
        c = countries[code]

        price_usd = c["price"]
        stars = int(price_usd * STAR_RATE)

        await query.message.reply_invoice(
            title=f"شراء رقم {c['name']}",
            description="الدفع بالنجوم ⭐",
            payload=f"order_{code}",
            provider_token="",  # Stars = فارغ
            currency="XTR",
            prices=[LabeledPrice("Stars", stars)],
        )

# تأكيد الدفع
async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

# بعد الدفع
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment

    stars = payment.total_amount
    usd = stars / STAR_RATE

    await update.message.reply_text(
        f"✅ تم الدفع بنجاح\n"
        f"⭐ النجوم: {stars}\n"
        f"💵 الدولار: {usd}$\n\n"
        f"🎉 سيتم تنفيذ طلبك تلقائياً"
    )

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(PreCheckoutQueryHandler(pre_checkout))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

print("Bot is running...")
app.run_polling()
