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

# قائمة الآيديهات المسموح لها بالتحكم (أنت وصديقك)
ADMIN_IDS = [7555122412, 1192400659]  

PROOF_CHANNEL = "@nwmbere"  # معرف قناة عمليات الشراء
OWNER_USERNAME = "@Klm_r7"  

ASIA_NUMBER = "07768828482"
ASIA_DEVELOPER = "@Klm_r7"

ATHEER_NUMBER = "07885706331"
ATHEER_DEVELOPER = "@h_4rk"

countries = {
    "iq": {"name": "العراق", "price": 2.6, "flag": "🇮🇶"},
    "us": {"name": "أمريكا", "price": 0.00, "flag": "🇺🇸"},
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

# لوحة تحكم الأدمن السرية المحدثة
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ هذا الأمر خاص بمسؤولي البوت فقط.")
        return
        
    keyboard = []
    for code, c in countries.items():
        count = get_stock_count(code)
        keyboard.append([
            InlineKeyboardButton(f"➕ إضافة لـ {c['flag']}", callback_data=f"adm_addstock_{code}"),
            InlineKeyboardButton(f"🗑️ حذف رقم ({count} متوفر)", callback_data=f"adm_delstock_{code}")
        ])
        
    await update.message.reply_text("🛠️ **لوحة التحكم - إدارة مخزن الأرقام (إضافة وحذف متاح):**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# معالجة الضغط على الأزرار والتنقل
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # شراء الأرقام للمستخدمين
    if query.data == "buy":
        keyboard = []
        for code, c in countries.items():
            count = get_stock_count(code)
            keyboard.append([
                InlineKeyboardButton(f"{c['flag']} {c['name']} - {c['price']}$ [{count} متوفر]", callback_data=f"buy_{code}")
            ])
        keyboard.append([InlineKeyboardButton("🔴 🔙 العودة للقائمة الرئيسية 🔴", callback_data="main_menu")])
        await query.edit_message_text("📱 اختر الدولة التي تريد شراء رقمها (التسليم فوري تلقائي):", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("buy_"):
        code = query.data.split("_")[1]
        c = countries[code]
        user_balance = get_balance(user_id)
        
        stock = load_data(NUMBERS_FILE)
        if not stock.get(code) or len(stock[code]) == 0:
            await query.edit_message_text(f"❌ أرقام {c['flag']} {c['name']} نافذة حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔴 العودة 🔴", callback_data="buy")]]))
            return

        if user_balance < c["price"]:
            await query.edit_message_text(f"❌ رصيدك الحالي غير كافٍ.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 تعبئة الرصيد 🔵", callback_data="deposit_main")]]))
            return

        selected_number_data = stock[code].pop(0)
        save_data(NUMBERS_FILE, stock)
        
        new_bal = update_balance(user_id, -c["price"])
        
        success_text = (
            f"🎉 **تم الشراء والتسليم التلقائي بنجاح!**\n\n"
            f"🏳️ الدولة: {c['flag']} {c['name']}\n"
            f"📞 الرقم: `{selected_number_data['phone']}`\n"
            f"🔑 كود التحقق: `{selected_number_data['code']}`\n"
            f"🔐 التحقق بخطوتين: `{selected_number_data.get('two_step', 'لا يوجد')}`"
        )
        await query.edit_message_text(success_text, parse_mode="Markdown")

    # الأدمن يضغط لإضافة رقم
    elif query.data.startswith("adm_addstock_"):
        if user_id not in ADMIN_IDS: return
        code = query.data.split("_")[2]
        context.user_data["adding_stock_for"] = code
        await query.edit_message_text(f"📥 ارسل بيانات الرقم لـ {countries[code]['name']} بالصيغة:\n`الرقم : الكود : كلمة المرور`")

    # 🗑️ ميزة الحذف التلقائي للأدمن
    elif query.data.startswith("adm_delstock_"):
        if user_id not in ADMIN_IDS: return
        code = query.data.split("_")[2]
        stock = load_data(NUMBERS_FILE)
        
        if not stock.get(code) or len(stock[code]) == 0:
            await query.edit_message_text(f"❌ مخزن {countries[code]['name']} فارغ بالفعل ولا يوجد أرقام لحذفها!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة للوحة الأدمن", callback_data="adm_back")]]))
            return
            
        # حذف آخر رقم تم إضافته للمخزن (Last In, First Out)
        removed_num = stock[code].pop()
        save_data(NUMBERS_FILE, stock)
        
        count = len(stock[code])
        await query.edit_message_text(
            f"🗑️ **تم حذف الرقم التالي من المخزن بنجاح:**\n"
            f"📞 الرقم المحذوف: `{removed_num['phone']}`\n\n"
            f"📊 المتبقي حالياً في المخزن: {count} رقم.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة للوحة الأدمن", callback_data="adm_back")]])
        )

    elif query.data == "adm_back":
        await admin_panel(update, context)

    # بقية أزرار الدفع والرجوع للمستخدمين
    elif query.data == "deposit_main":
        keyboard = [[InlineKeyboardButton("⭐ شحن تلقائي بالنجوم ⭐", callback_data="charge_stars")], [InlineKeyboardButton("🔴 العودة 🔴", callback_data="main_menu")]]
        await query.edit_message_text("💰 اختر وسيلة التحويل:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "charge_stars":
        context.user_data["waiting_for_stars"] = True
        await query.edit_message_text("📥 يرجى إرسال عدد النجوم رقماً:")

    elif query.data == "main_menu":
        await start(update, context)

# استقبال الرسائل النصية لشحن النجوم أو الإضافة للمخزن
async def handle_text_and_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text_received = update.message.text
    
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
        if code not in stock: stock[code] = []
        stock[code].append({"phone": phone, "code": phone_code, "two_step": two_step})
        save_data(NUMBERS_FILE, stock)
        
        await update.message.reply_text(f"✅ تم إضافة الرقم `{phone}` للمخزن.")
        return

    if context.user_data.get("waiting_for_stars"):
        if not text_received or not text_received.isdigit():
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح:")
            return
        stars_amount = int(text_received)
        del context.user_data["waiting_for_stars"]
        prices = [LabeledPrice(label=f"شحن {stars_amount} نجمة", amount=stars_amount)]
        await context.bot.send_invoice(chat_id=update.message.chat_id, title="شحن بالنجوم", description=f"تعبئة لـ {stars_amount} نجمة", payload="wallet_topup_stars", provider_token="", currency="XTR", prices=prices)

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stars_received = update.message.successful_payment.total_amount
    added_amount = stars_received * 0.01
    new_total = update_balance(update.message.from_user.id, added_amount)
    await update.message.reply_text(f"🌟 تم الشحن! رصيدك الحالي: {new_total}$")

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_and_messages))
app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

print("Volt Bot running smoothly with easy delete feature...")
app.run_polling()
