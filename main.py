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

# ----------------- الإعدادات الأساسية -----------------
TOKEN = "8690641497:AAGXVjkTtg72dSsIh3De_-ZW32rkhRmAcZw"  # ضع هنا توكن البوت الخاص بك داخل الاقتباسات
ADMIN_ID =7555122412  # ضع هنا الآيدي الخاص بك كأدمن (رقم فقط بدون اقتباسات)

STAR_RATE = 100  # 100 نجمة = 1$
USD_TO_IQD = 1500  # سعر تحويل الدولار للدينار العراقي

ASIA_NUMBER = "07768828482"
ASIA_DEVELOPER = "@Klm_r7"

ATHEER_NUMBER = "07885706331"
ATHEER_DEVELOPER = "@h_4rk"

countries = {
    "iq": {"name": "العراق", "price": 2.6, "flag": "🇮🇶"},
    "us": {"name": "أمريكا", "price": 0.4, "flag": "🇺🇸"},
    "ph": {"name": "الفلبين", "price": 0.10, "flag": "🇵🇭"},
    "bd": {"name": "بنغلاديش", "price": 0.35, "flag": "🇧🇩"},
    "ru": {"name": "روسيا", "price": 0.6, "flag": "🇷🇺"},
    "pk": {"name": "باكستان", "price": 0.8, "flag": "🇵🇰"},
    "lb": {"name": "لبنان", "price": 1.6, "flag": "🇱🇧"},
}

# أمر /start للمستخدمين
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📱 شراء رقم", callback_data="buy")]
    ]
    await update.message.reply_text(
        "👋 أهلاً بك في متجر الأرقام 💵",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# معالجة الضغط على الأزرار والتنقل
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

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

    elif query.data.startswith("ct_"):
        code = query.data.split("_")[1]
        c = countries[code]
        
        keyboard = [
            [InlineKeyboardButton("⭐ الدفع بنجوم تليجرام (تلقائي)", callback_data=f"star_{code}")],
            [InlineKeyboardButton("📱 آسيا سيل (يدوي)", callback_data=f"asia_{code}")],
            [InlineKeyboardButton("🦁 زين عراق / أثير (يدوي)", callback_data=f"atheer_{code}")],
        ]
        await query.edit_message_text(
            f"{c['flag']} الدولة: {c['name']}\n💵 السعر: {c['price']}$\n\nاختر طريقة الدفع المناسبة لك:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 1. الدفع التلقائي بالنجوم
    elif query.data.startswith("star_"):
        code = query.data.split("_")[1]
        c = countries[code]
        stars = int(c["price"] * STAR_RATE)

        await query.message.reply_invoice(
            title=f"شراء رقم {c['name']}",
            description="سيتم الخصم تلقائياً من رصيد نجوم حسابك في تليجرام ⭐",
            payload=f"order_{code}",
            provider_token="",  
            currency="XTR",
            prices=[LabeledPrice("Stars", stars)],
        )

    # 2. خيار آسيا سيل اليدوي
    elif query.data.startswith("asia_"):
        code = query.data.split("_")[1]
        c = countries[code]
        price_iqd = int(c["price"] * USD_TO_IQD)
        
        context.user_data["pending_payment"] = {"code": code, "method": "آسيا سيل", "price_iqd": price_iqd}
        
        await query.edit_message_text(
            f"📱 طريقة الدفع: آسيا سيل\n"
            f"💵 سعر الرقم بالدينار: {price_iqd:,} دينار عراقي\n\n"
            f"قم بتحويل المبلغ إلى الرقم التالي:\n"
            f"`{ASIA_NUMBER}`\n\n"
            f"📥 بعد إتمام عملية تحويل الرصيد، يرجى إرسال صورة إثبات التحويل هنا مباشرة في البوت ليتم مراجعتها من قبل المطور {ASIA_DEVELOPER} وتعبئة رصيدك."
        )

    # 3. خيار أثير اليدوي
    elif query.data.startswith("atheer_"):
        code = query.data.split("_")[1]
        c = countries[code]
        price_iqd = int(c["price"] * USD_TO_IQD)
        
        context.user_data["pending_payment"] = {"code": code, "method": "أثير", "price_iqd": price_iqd}
        
        await query.edit_message_text(
            f"🦁 طريقة الدفع: زين عراق / أثير\n"
            f"💵 سعر الرقم بالدينار: {price_iqd:,} دينار عراقي\n\n"
            f"قم بتحويل المبلغ إلى الرقم التالي:\n"
            f"`{ATHEER_NUMBER}`\n\n"
            f"📥 بعد إتمام عملية تحويل الرصيد، يرجى إرسال صورة إثبات التحويل هنا مباشرة في البوت ليتم مراجعتها من قبل المطور {ATHEER_DEVELOPER} وتعبئة رصيدك."
        )

    # معالجة قبول الأدمن للطلب اليدوي
    elif query.data.startswith("adm_approve_"):
        parts = query.data.split("_")
        user_id = int(parts[2])
        method = parts[3]
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ تم قبول طلبك من قبل الإدارة لحساب ({method})، تم تعبئة رصيدك وشكراً ثقتك بنا!"
            )
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ تم القبول وتعبئة الرصيد بنجاح.")
        except Exception as e:
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n⚠️ تم القبول لكن لم نتمكن من إشعار المستخدم: {e}")

    # معالجة رفض الأدمن للطلب اليدوي
    elif query.data.startswith("adm_reject_"):
        parts = query.data.split("_")
        user_id = int(parts[2])
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ نعتذر منك، تم رفض طلبك وتدقيق عملية الدفع. يرجى التأكد من إرسال الإثبات الصحيح أو التواصل مع المطور."
            )
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ تم رفض هذا الطلب.")
        except Exception as e:
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n⚠️ تم الرفض لكن لم نتمكن من إشعار المستخدم: {e}")

# استلام إثبات الدفع اليدوي من الزبون (صورة حصراً)
async def handle_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "pending_payment" not in context.user_data:
        return  
        
    order = context.user_data["pending_payment"]
    c = countries[order["code"]]
    user = update.effective_user
    
    # رسالة واضحة وبسيطة لضمان وصول الإشعار فوراً للأدمن
    admin_caption = (
        f"🚨 طلب دفع يدوي جديد!\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🆔 الآيدي: {user.id}\n"
        f"💳 طريقة الدفع: {order['method']}\n"
        f"🏳️ الدولة المطلوبة: {c['name']}\n"
        f"💵 المبلغ المطلوب: {order['price_iqd']:,} دينار\n"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول وتعبئة", callback_data=f"adm_approve_{user.id}_{order['method']}"),
            InlineKeyboardButton("❌ رفض الطلب", callback_data=f"adm_reject_{user.id}")
        ]
    ]
    
    try:
        # إرسال الصورة والبيانات لحساب الأدمن مباشرة
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=admin_caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        # تأكيد الاستلام للزبون
        await update.message.reply_text("📥 تم إرسال صورة الإثبات إلى المطورين بنجاح. يرجى الانتظار لحين تدقيق عملية التحويل وتفعيل رصيدك...")
    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء إرسال طلبك للإدارة. يرجى مراسلة المطور مباشرة. الخطأ: {e}")
    
    del context.user_data["pending_payment"]

# تأكيد فاتورة النجوم
async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

# بعد نجاح الدفع بالنجوم تلقائياً
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    stars = payment.total_amount
    usd = stars / STAR_RATE
    
    await update.message.reply_text(
        f"✅ تم الدفع بنجاح عبر نجوم تليجرام\n"
        f"⭐ النجوم المخصومة: {stars}\n"
        f"💵 القيمة المقابلة: {usd}$\n\n"
        f"🎉 تم تأمين وتعبئة طلبك تلقائياً بنجاح!"
    )

# تشغيل وتجهيز الهاندلرات للبوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(PreCheckoutQueryHandler(pre_checkout))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
app.add_handler(MessageHandler(filters.PHOTO, handle_proof))

print("Bot is running with Asia and Atheer modules...")
app.run_polling()
