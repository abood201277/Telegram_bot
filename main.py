import json
import os
import random
import logging
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
    MessageHandler,
    filters,
    PreCheckoutQueryHandler,
)

# إعداد الـ Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ----------------- الإعدادات الأساسية -----------------
TOKEN = "8690641497:AAHYHhLEX53A_wRIAF5b2TviZUJR_2xq_aM"  # ضع توكن بوتك الحقيقي هنا

# 👥 هير خلينه قائمة بالآيديهات المسموح لها بالتحكم (أنت وصديقك)
# ضع آيديك وآيدي صديقك بفواصل مثل: [123456789, 987654321]
ADMIN_IDS = [7555122412,1192400659]  

PROOF_CHANNEL = "@nwmbere"  # معرف قناة عمليات الشراء
OWNER_USERNAME = "@Klm_r7"  

ASIA_NUMBER = "07768828482"
ASIA_DEVELOPER = "@Klm_r7"

ATHEER_NUMBER = "07885706331"
ATHEER_DEVELOPER = "@h_4rk"

countries = {
    "iq": {"name": "العراق", "price": 2.6, "flag": "🇮🇶"},
    "us": {"name": "أمريكا", "price": 0.4, "flag": "🇺🇸"},
    "ph": {"name": "الفلبين", "price": 0.50, "flag": "🇵🇭"},
    "bd": {"name": "بنغلاديش", "price": 0.35, "flag": "🇧🇩"},
    "ru": {"name": "روسيا", "price": 0.6, "flag": "🇷🇺"},
    "pk": {"name": "باكستان", "price": 0.8, "flag": "🇵🇰"},
    "lb": {"name": "لبنان", "price": 1.6, "flag": "🇱🇧"},
}

# ------ نظام إدارة وحفظ البيانات تلقائياً ------
BALANCE_FILE = "users_balance.json"
NUMBERS_FILE = "stock_numbers.json"

def load_data(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_balance(user_id):
    balances = load_data(BALANCE_FILE)
    return balances.get(str(user_id), 0.0)

def update_balance(user_id, amount):
    balances = load_data(BALANCE_FILE)
    current = balances.get(str(user_id), 0.0)
    balances[str(user_id)] = round(current + amount, 2)
    save_data(BALANCE_FILE, balances)
    return balances[str(user_id)]

def get_stock_count(code):
    stock = load_data(NUMBERS_FILE)
    return len(stock.get(code, []))

# أمر /start للمستخدمين
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    
    if "waiting_for_stars" in context.user_data:
        del context.user_data["waiting_for_stars"]
    
    keyboard = [
        [InlineKeyboardButton("🟢 📱 شراء رقم متاح 🟢", callback_data="buy")],
        [InlineKeyboardButton("🔵 💰 تعبئة رصيد المحفظة 🔵", callback_data="deposit_main")]
    ]
    
    text = (
        f"👋 أهلاً بك في **فولت بوت | Volt Bot 💎**\n\n"
        f"💵 رصيد حسابك الحالي: {balance}$\n\n"
        f"اختر ما تريد من الأزرار أدناه لشراء الأرقام بتسليم تلقائي فوري:"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# لوحة تحكم الأدمن السرية (تعديل لتشمل قائمة الأدمنية)
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ هذا الأمر خاص بمسؤولي البوت فقط.")
        return
        
    keyboard = []
    for code, c in countries.items():
        count = get_stock_count(code)
        keyboard.append([InlineKeyboardButton(f"➕ إضافة لـ {c['flag']} {c['name']} ({count} متوفر)", callback_data=f"adm_addstock_{code}")])
        
    await update.message.reply_text("🛠️ **لوحة التحكم - إضافة أرقام جاهزة للمخزن:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# معالجة الضغط على الأزرار والتنقل
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # 1. قائمة شراء الأرقام
    if query.data == "buy":
        keyboard = []
        for code, c in countries.items():
            count = get_stock_count(code)
            keyboard.append([
                InlineKeyboardButton(f"{c['flag']} {c['name']} - {c['price']}$ [{count} متوفر]", callback_data=f"buy_{code}")
            ])
        keyboard.append([InlineKeyboardButton("🔴 🔙 العودة للقائمة الرئيسية 🔴", callback_data="main_menu")])
        await query.edit_message_text("📱 اختر الدولة التي تريد شراء رقمها (التسليم فوري تلقائي):", reply_markup=InlineKeyboardMarkup(keyboard))

    # تنفيذ الشراء التلقائي
    elif query.data.startswith("buy_"):
        code = query.data.split("_")[1]
        c = countries[code]
        user_balance = get_balance(user_id)
        
        stock = load_data(NUMBERS_FILE)
        if not stock.get(code) or len(stock[code]) == 0:
            await query.edit_message_text(
                f"❌ نعتذر منك جداً! أرقام {c['flag']} {c['name']} نافذة حالياً من المخزن.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔴 العودة 🔴", callback_data="buy")]])
            )
            return

        if user_balance < c["price"]:
            await query.edit_message_text(
                f"❌ رصيدك الحالي {user_balance}$ غير كافٍ لشراء رقم بسعر {c['price']}$.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 💰 تعبئة الرصيد 🔵", callback_data="deposit_main")]])
            )
            return

        selected_number_data = stock[code].pop(0)
        save_data(NUMBERS_FILE, stock)
        
        new_bal = update_balance(user_id, -c["price"])
        
        phone_num = selected_number_data["phone"]
        phone_code = selected_number_data["code"]
        two_step = selected_number_data.get("two_step", "لا يوجد")
        
        success_text = (
            f"🎉 **تم الشراء والتسليم التلقائي بنجاح!**\n\n"
            f"🏳️ الدولة: {c['flag']} {c['name']}\n"
            f"💵 السعر: {c['price']}$\n"
            f"💰 رصيدك المتبقي: {new_bal}$\n\n"
            f"📱 **بيانات رقمك الجديد بالكامل:**\n"
            f"📞 الرقم: `{phone_num}`\n"
            f"🔑 كود التحقق: `{phone_code}`\n"
            f"🔐 التحقق بخطوتين: `{two_step}`\n\n"
            f"⚠️ فعل حسابك الآن! شكراً لاستخدامك فولت بوت ⚡"
        )
        await query.edit_message_text(success_text, parse_mode="Markdown")

        try:
            proof_channel_text = (
                f"🛍️ **عملية شراء ناجحة بتسليم تلقائي!**\n\n"
                f"🏳️ الدولة: {c['flag']} {c['name']}\n"
                f"💵 السعر: {c['price']}$\n"
                f"✅ الحالة: تم تسليم الرقم، الكود، وكلمة المرور آلياً.\n\n"
                f"فولت بوت.. سرعة وأمان 💎"
            )
            await context.bot.send_message(chat_id=PROOF_CHANNEL, text=proof_channel_text, parse_mode="Markdown")
        except Exception: pass

    # الأدمن يضغط لإضافة رقم
    elif query.data.startswith("adm_addstock_"):
        if user_id not in ADMIN_IDS: return
        code = query.data.split("_")[2]
        context.user_data["adding_stock_for"] = code
        await query.edit_message_text(
            f"📥 يرجى إرسال بيانات الرقم لـ {countries[code]['name']} بالصيغة التالية تماماً:\n\n"
            f"`الرقم : الكود : كلمة المرور`\n\n"
            f"💡 مثال إذا كان يوجد باسورد:\n`+17025550199 : 44831 : abood123`\n\n"
            f"💡 مثال إذا لا يوجد باسورد:\n`+17025550199 : 44831 : لا يوجد`"
        )

    # الأقسام الأخرى وتعبئة الرصيد
    elif query.data == "deposit_main":
        keyboard = [
            [InlineKeyboardButton("⭐ شحن تلقائي فوري بالنجوم (Stars) ⭐", callback_data="charge_stars")],
            [InlineKeyboardButton("📱 تعبئة يدوية عبر آسيا سيل", callback_data="dep_asia")],
            [InlineKeyboardButton("🦁 تعبئة يدوية عبر أثير / زين", callback_data="dep_atheer")],
            [InlineKeyboardButton("🔴 🔙 العودة للقائمة الرئيسية 🔴", callback_data="main_menu")]
        ]
        await query.edit_message_text("💰 اختر وسيلة التحويل لتعبئة رصيد حسابك داخل البوت:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "dep_asia":
        context.user_data["pending_deposit"] = {"method": "آسيا سيل"}
        await query.edit_message_text(f"📱 شحن آسيا سيل\n\nقم بتحويل الرصيد إلى:\n`{ASIA_NUMBER}`\n\n📥 أرسل صورة الإثبات هنا:")

    elif query.data == "dep_atheer":
        context.user_data["pending_deposit"] = {"method": "أثير"}
        await query.edit_message_text(f"🦁 شحن زين/أثير\n\nقم بتحويل الرصيد إلى:\n`{ATHEER_NUMBER}`\n\n📥 أرسل صورة الإثبات هنا:")

    elif query.data == "charge_stars":
        context.user_data["waiting_for_stars"] = True
        await query.edit_message_text("📥 **يرجى إرسال عدد النجوم رقماً التي تريد شحنها الآن:**\nعلماً أن كل (1) نجمة ⭐ = 0.01$")

    elif query.data == "main_menu":
        balance = get_balance(user_id)
        keyboard = [
            [InlineKeyboardButton("🟢 📱 شراء رقم متاح 🟢", callback_data="buy")],
            [InlineKeyboardButton("🔵 💰 تعبئة رصيد المحفظة 🔵", callback_data="deposit_main")]
        ]
        await query.edit_message_text(f"👋 أهلاً بك في **فولت بوت | Volt Bot 💎**\n\n💵 رصيد حسابك الحالي: {balance}$", reply_markup=InlineKeyboardMarkup(keyboard))

    # قبول التعبئة من قبل أي أدمن من القائمة
    elif query.data.startswith("adm_add_"):
        if user_id not in ADMIN_IDS: return
        parts = query.data.split("_")
        target_user_id = int(parts[2])
        method = parts[3]
        new_total = update_balance(target_user_id, 5.0)
        try:
            await context.bot.send_message(chat_id=target_user_id, text=f"✅ تم قبول التعبئة اليدوية! تم إضافة 5$ لحسابك. رصيدك الحالي: {new_total}$")
        except Exception: pass
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ تم قبول التعبئة بنجاح.")

    elif query.data.startswith("adm_deny_"):
        if user_id not in ADMIN_IDS: return
        parts = query.data.split("_")
        target_user_id = int(parts[2])
        try:
            await context.bot.send_message(chat_id=target_user_id, text="❌ تم رفض إثبات تحويل الرصيد بعد التدقيق.")
        except Exception: pass
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ تم الرفض.")

# استقبال الرسائل النصية
async def handle_text_and_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text_received = update.message.text
    
    # التحقق من أن المرسل أدمن لإضافة رقم
    if user_id in ADMIN_IDS and "adding_stock_for" in context.user_data:
        code = context.user_data["adding_stock_for"]
        del context.user_data["adding_stock_for"]
        
        if text_received.count(":") < 2:
            await update.message.reply_text("❌ صيغة خاطئة! يجب أن ترسلها هكذا `الرقم : الكود : كلمة المرور`.")
            return
            
        parts = text_received.split(":")
        phone = parts[0].strip()
        phone_code = parts[1].strip()
        two_step = parts[2].strip()
        
        stock = load_data(NUMBERS_FILE)
        if code not in stock:
            stock[code] = []
            
        stock[code].append({"phone": phone, "code": phone_code, "two_step": two_step})
        save_data(NUMBERS_FILE, stock)
        
        await update.message.reply_text(f"✅ تم إضافة الرقم بنجاح للمخزن!\n📞 الرقم: `{phone}`\n🔑 الكود: `{phone_code}`\n🔐 الباسورد: `{two_step}`")
        return

    # شحن النجوم للمستخدمين
    if context.user_data.get("waiting_for_stars"):
        if not text_received or not text_received.isdigit():
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح فقط:")
            return
            
        stars_amount = int(text_received)
        del context.user_data["waiting_for_stars"]
        
        prices = [LabeledPrice(label=f"شحن {stars_amount} نجمة", amount=stars_amount)]
        await context.bot.send_invoice(
            chat_id=update.message.chat_id,
            title="شحن المحفظة بالنجوم",
            description=f"تعبئة تلقائية مخصصة لـ {stars_amount} نجمة",
            payload="wallet_topup_stars",
            provider_token="",
            currency="XTR",
            prices=prices
        )
        return

# موافقة الفاتورة
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != "wallet_topup_stars":
        await query.answer(ok=False, error_message="حدث خطأ في الفاتورة.")
    else:
        await query.answer(ok=True)

# استقبال شحن النجوم الناجح
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    user_id = update.message.from_user.id
    stars_received = payment.total_amount
    added_amount = stars_received * 0.01
    new_total_balance = update_balance(user_id, added_amount)
    
    success_text = (
        f"🌟 **تم الشحن التلقائي بنجاح!** 🌟\n\n"
        f"📥 تم استقبال: {stars_received} نجمة تليجرام.\n"
        f"💰 تم إضافة: +{added_amount:.2f}$ لمحفظتك.\n"
        f"💵 رصيدك الكلي الحالي أصبح: {new_total_balance}$"
    )
    await update.message.reply_text(success_text)

# استلام صور إثباتات آسيا وأثير (ترسل لجميع الأدمنية المتاحين بالمستقبل إذا رغبت، حالياً ترسل لأول أدمن)
async def handle_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "pending_deposit" not in context.user_data: return  
    deposit = context.user_data["pending_deposit"]
    user = update.effective_user
    
    admin_caption = f"🚨 **طلب شحن معلق!**\n\n👤 الزبون: {user.first_name}\n🆔 الآيدي: {user.id}\n💳 الوسيلة: {deposit['method']}\n"
    keyboard = [[InlineKeyboardButton("✅ قبول (5$)", callback_data=f"adm_add_{user.id}_{deposit['method']}"), InlineKeyboardButton("❌ رفض", callback_data=f"adm_deny_{user.id}")]]
    
    # ترسل للأدمن الأول في القائمة كإشعار أساسي
    try:
        await context.bot.send_photo(chat_id=ADMIN_IDS[0], photo=update.message.photo[-1].file_id, caption=admin_caption, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception: pass
    await update.message.reply_text("📥 تم إرسال إثبات التعبئة بنجاح للمطور. سيتم مراجعة طلبك...")
    del context.user_data["pending_deposit"]

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_and_messages))
app.add_handler(MessageHandler(filters.PHOTO, handle_proof))
app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

print("Volt Bot Running with Multi-Admin Support...")
app.run_polling()
