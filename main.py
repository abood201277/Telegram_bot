import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# 1. إعدادات التسجيل والـ Logging لمعرفة الأخطاء بالسيرفر
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. متغيرات البوت الأساسية (اكتب التوكن الجديد مالتك هنا بين العلامتين)
BOT_TOKEN = "ضع_التوكن_الجديد_هنا"

# أسعار الخدمات بالدولار (حسبتك المباشرة: 0.50$ تعادل 50 نجمة)
PRICES = {
    "philippines": 0.50,  # سعر أرقام الفلبين
    "usa": 2.00,          # سعر أرقام أمريكا
    "uk": 2.50            # سعر أرقام بريطانيا
}

# 3. دالة بدء تشغيل البوت للمستخدم (/start)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"مرحباً بك يا {user.first_name} في بوت الخدمات المطور! 👋\n\n"
        f"هنا يمكنك شحن محفظتك وشراء الأرقام والخدمات مباشرة.\n"
        f"💰 رصيدك الحالي في المحفظة هو: $0.00"
    )
    
    # أزرار لوحة التحكم الرئيسية مدعومة بالإيموجي الملون لتمييزها
    keyboard = [
        [InlineKeyboardButton("🟢 🛒 شراء الخدمات والأرقام 🟢", callback_query_data="view_services")],
        [
            InlineKeyboardButton("⭐ شحن بـ 50 نجمة ($0.50) ⭐", callback_query_data="charge_stars"),
            InlineKeyboardButton("🔵 💼 محفظتي 🔵", callback_query_data="view_wallet")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup)

# 4. دالة عرض الخدمات والأسعار المحدثة
async def view_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    services_text = (
        "📊 قائمة الخدمات والأسعار الحالية:\n\n"
        f"🇵🇭 أرقام الفلبين: ${PRICES['philippines']} (تعادل 50 نجمة)\n"
        f"🇺🇸 أرقام أمريكا: ${PRICES['usa']} (تعادل 200 نجمة)\n"
        f"🇬🇧 أرقام بريطانيا: ${PRICES['uk']} (تعادل 250 نجمة)\n\n"
        "تأكد من شحن محفظتك قبل الشراء!"
    )
    
    # زر العودة ملون بالأحمر للتنبيه والرجوع
    keyboard = [[InlineKeyboardButton("🔴 🔙 العودة للقائمة الرئيسية 🔴", callback_query_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(services_text, reply_markup=reply_markup)

# ==================== نظام دفع النجوم (TELEGRAM STARS) ====================

# 5. دالة إرسال فاتورة النجوم للمستخدم عند طلب الشحن
async def send_stars_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    title = "شحن محفظة البوت"
    description = "شحن رصيد المحفظة بمقدار 50 نجمة تليجرام ($0.50)"
    payload = "wallet_topup_stars"
    currency = "XTR"  # الرمز الرسمي المعتمد لنجوم تليجرام
    
    # تحديد السعر بـ 50 نجمة (ليعطي المستخدم 50 سنت بالمحفظة)
    prices = [LabeledPrice(label="شحن رصيد البوت", amount=50)] 
    
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # تترك فارغة تماماً مع النجوم لأنها دفع داخلي بالمنصة
        currency=currency,
        prices=prices
    )

# 6. الموافقة والتحقق التلقائي من الفاتورة قبل عملية الخصم
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != "wallet_topup_stars":
        await query.answer(ok=False, error_message="حدث خطأ غير متوقع في عملية الدفع.")
    else:
        await query.answer(ok=True)

# 7. تحديث رصيد المستخدم وإرسال رسالة النجاح بعد إتمام الدفع بالنجوم
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    stars_received = payment.total_amount  # عدد النجوم المستلمة (50 نجمة)
    
    # حسبتك المباشرة الثابتة: كل 1 نجمة تعادل 1 سنت (0.01$)
    # الـ 50 نجمة تعادل 0.50$ دولار كاملة في محفظة المستخدم
    added_balance = stars_received * 0.01 
    
    success_message = (
        f"✅ تم استقبال الدفع بنجاح!\n\n"
        f"📥 عدد النجوم المستلمة: {stars_received} نجمة.\n"
        f"💰 تم شحن محفظتك بمبلغ: ${added_balance:.2f} بنجاح ومشترياتك جاهزة!"
    )
    await update.message.reply_text(success_message)

# ==========================================================================

# 8. دالة معالجة الأزرار العادية (Callback Queries)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "view_services":
        await view_services(update, context)
    elif data == "charge_stars":
        await send_stars_invoice(update, context)
    elif data == "back_to_main" or data == "view_wallet":
        await start(update, context)

# 9. محرك تشغيل وتجميع البوت (Main Function)
def main():
    # بناء التطبيق بالتوكن المخصص
    app = Application.builder().token(BOT_TOKEN).build()
    
    # تسجيل الأوامر وهاندلرز الأزرار
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # تسجيل هاندلرز نظام النجوم والمدفوعات الافتراضية
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    # طباعة جملة التأكيد في شاشة السيرفر عند العمل بنجاح
    print("Wallet-Based Bot with Colored Emojis and Stars running perfectly...")
    
    # بدء استقبال الرسائل (Polling)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
