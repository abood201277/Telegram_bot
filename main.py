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
TOKEN = "8690641497:AAHYHhLEX53A_wRIAF5b2TviZUJR_2xq_aM"  # ⚠️ ضع توكن بوتك الحقيقي هنا

# قائمة الآيديهات المسموح لها بالتحكم (أنت وصديقك)
ADMIN_IDS = [7555122412, 1192400659]  

PROOF_CHANNEL = "@nwmberbot"  
OWNER_USERNAME = "@Klm_r7"  

ASIA_NUMBER = "07768828482"
ASIA_DEVELOPER = "@Klm_r7"

ATHEER_NUMBER = "07885706331"
ATHEER_DEVELOPER = "@h_4rk"

# 🌟 الأسعار بالنجوم مباشرة
countries = {
    "iq": {"name": "العراق", "price": 260, "flag": "🇮🇶"},
    "us": {"name": "أمريكا", "price": 35, "flag": "🇺🇸"},
    "ph": {"name": "الفلبين", "price": 50, "flag": "🇵🇭"},
    "bd": {"name": "بنغلاديش", "price": 35, "flag": "🇧🇩"},
    "ru": {"name": "روسيا", "price": 60, "flag": "🇷🇺"},
    "pk": {"name": "باكستان", "price": 80, "flag": "🇵🇰"},
    "lb": {"name": "لبنان", "price": 160, "flag": "🇱🇧"},
}

# ------ نظام إدارة وحفظ البيانات تلقائياً ------
BALANCE_FILE = "users_balance.json"
NUMBERS_FILE = "stock_numbers.json"
USERS_FILE = "users_list.json"  
BANNED_FILE = "banned_users.json" # ملف المحظورين الجديد

def load_data(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {} if "list" not in filename and "banned" not in filename else []
    return {} if "list" not in filename and "banned" not in filename else []

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_balance(user_id):
    balances = load_data(BALANCE_FILE)
    return balances.get(str(user_id), 0)  

def update_balance(user_id, amount):
    balances = load_data(BALANCE_FILE)
    current = balances.get(str(user_id), 0)
    balances[str(user_id)] = int(current + amount)
    save_data(BALANCE_FILE, balances)
    return balances[str(user_id)]

def get_stock_count(code):
    stock = load_data(NUMBERS_FILE)
    return len(stock.get(code, []))

def is_banned(user_id):
    banned = load_data(BANNED_FILE)
    return user_id in banned

# أمر /start للمستخدمين
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_banned(user_id):
        await update.message.reply_text("🚫 عذراً، تم حظرك من استخدام البوت من قبل الإدارة.")
        return

    # ميزة تسجيل المستخدم الجديد وإرسال إشعار للأدمنية
    users = load_data(USERS_FILE)
    if not isinstance(users, list): users = []
    if user_id not in users:
        users.append(user_id)
        save_data(USERS_FILE, users)
        # إرسال إشعار للأدمنية بدخول شخص جديد
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 **مستخدم جديد دخل للبوت!**\n\n👤 الاسم: {update.effective_user.first_name}\n🆔 الآيدي: `{user_id}`\n🔗 اليوزر: @{update.effective_user.username if update.effective_user.username else 'لا يوجد'}",
                    parse_mode="Markdown"
                )
            except Exception: pass
    
    balance = get_balance(user_id)
    if "waiting_for_stars" in context.user_data: del context.user_data["waiting_for_stars"]
    
    keyboard = [
        [InlineKeyboardButton("🟢 📱 شراء رقم متاح 🟢", callback_data="buy")],
        [InlineKeyboardButton("🔵 🌟 تعبئة رصيد المحفظة (نجوم) 🔵", callback_data="deposit_main")]
    ]
    
    text = (
        f"👋 أهلاً بك في **فولت بوت | Volt Bot 💎**\n\n"
        f"🌟 رصيد محفظتك الحالي: `{balance}` نجمة\n\n"
        f"اختر ما تريد من الأزرار أدناه لشراء الأرقام بنظام النجوم المباشر:"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# لوحة تحكم الأدمن السرية
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return
        
    users = load_data(USERS_FILE)
    total_users = len(users) if isinstance(users, list) else 0
    
    keyboard = []
    for code, c in countries.items():
        count = get_stock_count(code)
        keyboard.append([
            InlineKeyboardButton(f"➕ إضافة لـ {c['name']}", callback_data=f"adm_addstock_{code}"),
            InlineKeyboardButton(f"🗑️ حذف رقم ({count})", callback_data=f"adm_delstock_{code}")
        ])
        
    admin_text = (
        f"🛠️ **لوحة التحكم - إدارة فولت بوت**\n\n"
        f"📊 **مجموع الداخلين للبوت:** `{total_users}` مستخدم 👥\n\n"
        f"⚙️ **أوامر الإدارة الإضافية:**\n"
        f"📢 للإذاعة: اكتب `/broadcast` متبوعاً بالرسالة.\n"
        f"👤 لإدارة مستخدم (رصيد/حظر): اكتب `/user` متبوعاً بآيدي الشخص."
    )
    await update.message.reply_text(admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# أمر الإذاعة والنشر لجميع المشتركين
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return
    
    if not context.args:
        await update.message.reply_text("❌ يرجى كتابة الرسالة بعد الأمر، مثال:\n`/broadcast أهلاً بكم في البوت`", parse_mode="Markdown")
        return
        
    broadcast_msg = " ".join(context.args)
    users = load_data(USERS_FILE)
    
    success_count = 0
    await update.message.reply_text("⏳ جاري بدء الإذاعة والنشر لجميع المشتركين...")
    
    for u_id in users:
        try:
            await context.bot.send_message(chat_id=u_id, text=broadcast_msg)
            success_count += 1
        except Exception: pass
        
    await update.message.reply_text(f"✅ تم انتهاء الإذاعة بنجاح بنسبة {success_count} من أصل {len(users)} مستخدم.")

# أمر إدارة مستخدم معين (رصيد وحظر)
async def user_manage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ يرجى كتابة آيدي المستخدم الصحيح بعد الأمر، مثال:\n`/user 123456789`", parse_mode="Markdown")
        return
        
    target_id = int(context.args[0])
    target_balance = get_balance(target_id)
    banned_status = "محظور 🚫" if is_banned(target_id) else "نشط ✅"
    
    keyboard = [
        [
            InlineKeyboardButton("➕ إضافة رصيد", callback_data=f"usr_add_{target_id}"),
            InlineKeyboardButton("➖ خصم رصيد", callback_data=f"usr_sub_{target_id}")
        ],
        [
            InlineKeyboardButton("🚫 حظر / فك حظر", callback_data=f"usr_ban_{target_id}")
        ]
    ]
    
    text = (
        f"👤 **لوحة إدارة ملف المستخدم:**\n\n"
        f"🆔 الآيدي: `{target_id}`\n"
        f"🌟 رصيده الحالي: `{target_balance}` نجمة\n"
        f"🚦 حالة الحساب: **{banned_status}**\n\n"
        f"اختر الإجراء الذي تريد تطبيقه عليه:"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# معالجة الضغط على الأزرار والتنقل
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "buy":
        if is_banned(user_id): return
        keyboard = []
        for code, c in countries.items():
            count = get_stock_count(code)
            keyboard.append([InlineKeyboardButton(f"{c['flag']} {c['name']} - {c['price']} 🌟 [{count} متوفر]", callback_data=f"buy_{code}")])
        keyboard.append([InlineKeyboardButton("🔴 🔙 العودة للقائمة الرئيسية 🔴", callback_data="main_menu")])
        await query.edit_message_text("📱 اختر الدولة التي تريد شراء رقمها بالنجوم:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("buy_"):
        if is_banned(user_id): return
        code = query.data.split("_")[1]
        c = countries[code]
        user_balance = get_balance(user_id)
        
        stock = load_data(NUMBERS_FILE)
        if not stock.get(code) or len(stock[code]) == 0:
            await query.edit_message_text(f"❌ أرقام {c['flag']} {c['name']} نافذة حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔴 العودة 🔴", callback_data="buy")]]))
            return

        if user_balance < c["price"]:
            await query.edit_message_text(f"❌ رصيد نجومك الحالي غير كافٍ.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 شحن نجوم 🔵", callback_data="deposit_main")]]))
            return

        selected_number_data = stock[code].pop(0)
        save_data(NUMBERS_FILE, stock)
        update_balance(user_id, -c["price"])
        
        success_text = (
            f"🎉 **تم الشراء والتسليم بنجاح!**\n\n🏳️ الدولة: {c['flag']} {c['name']}\n📞 الرقم: `{selected_number_data['phone']}`\n🔑 كود التحقق: `{selected_number_data['code']}`\n🔐 التحقق بخطوتين: `{selected_number_data.get('two_step', 'لا يوجد')}`"
        )
        await query.edit_message_text(success_text, parse_mode="Markdown")

    # معالجات تحكم الأدمن في المستخدم (إضافة/خصم/حظر)
    elif query.data.startswith("usr_"):
        parts = query.data.split("_")
        action = parts[1]
        target_id = int(parts[2])
        
        if user_id not in ADMIN_IDS: return
        
        if action == "add":
            context.user_data["manage_action"] = ("add", target_id)
            await query.edit_message_text(f"📥 ارسل عدد النجوم التي تريد **إضافتها** لآيدي `{target_id}`:")
        elif action == "sub":
            context.user_data["manage_action"] = ("sub", target_id)
            await query.edit_message_text(f"📥 ارسل عدد النجوم التي تريد **خصمها** من آيدي `{target_id}`:")
        elif action == "ban":
            banned_list = load_data(BANNED_FILE)
            if not isinstance(banned_list, list): banned_list = []
            if target_id in banned_list:
                banned_list.remove(target_id)
                msg = f"✅ تم إلغاء حظر المستخدم `{target_id}` بنجاح."
            else:
                banned_list.append(target_id)
                msg = f"🚫 تم حظر المستخدم `{target_id}` من البوت بنجاح."
            save_data(BANNED_FILE, banned_list)
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="main_menu")]]))

    elif query.data.startswith("adm_addstock_"):
        if user_id not in ADMIN_IDS: return
        code = query.data.split("_")[2]
        context.user_data["adding_stock_for"] = code
        await query.edit_message_text(f"📥 ارسل بيانات الرقم لـ {countries[code]['name']} بالصيغة:\n`الرقم : الكود : كلمة المرور`")

    elif query.data.startswith("adm_delstock_"):
        if user_id not in ADMIN_IDS: return
        code = query.data.split("_")[2]
        stock = load_data(NUMBERS_FILE)
        if not stock.get(code) or len(stock[code]) == 0:
            await query.edit_message_text(f"❌ المخزن فارغ.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة للوحة الأدمن", callback_data="main_menu")]]))
            return
        stock[code].pop()
        save_data(NUMBERS_FILE, stock)
        await query.edit_message_text(f"🗑️ تم حذف الرقم الأخير بنجاح.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="main_menu")]]))

    elif query.data == "deposit_main":
        if is_banned(user_id): return
        keyboard = [[InlineKeyboardButton("⭐ شحن تلقائي بالنجوم ⭐", callback_data="charge_stars")], [InlineKeyboardButton("🔴 العودة 🔴", callback_data="main_menu")]]
        await query.edit_message_text("💰 اضغط على الزر أدناه لشحن محفظتك بالنجوم فوراً:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "charge_stars":
        if is_banned(user_id): return
        context.user_data["waiting_for_stars"] = True
        await query.edit_message_text("📥 يرجى إرسال عدد النجوم التي تريد شحنها لمحفظتك رقماً:")

    elif query.data == "main_menu":
        await start(update, context)

# استقبال الرسائل النصية
async def handle_text_and_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_banned(user_id): return
    text_received = update.message.text
    
    # معالجة إضافة أو خصم الرصيد يدوياً من الأدمن
    if user_id in ADMIN_IDS and "manage_action" in context.user_data:
        action, target_id = context.user_data["manage_action"]
        del context.user_data["manage_action"]
        
        if not text_received.isdigit():
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح فقط.")
            return
            
        amount = int(text_received)
        if action == "add":
            new_b = update_balance(target_id, amount)
            await update.message.reply_text(f"✅ تم إضافة {amount} نجمة للمستخدم. رصيده الجديد: `{new_b}` نجمة.")
            try: await context.bot.send_message(chat_id=target_id, text=f"🎉 تم إضافة `{amount}` نجمة لمحفظتك من قبل الإدارة!")
            except Exception: pass
        elif action == "sub":
            new_b = update_balance(target_id, -amount)
            await update.message.reply_text(f"✅ تم خصم {amount} نجمة من المستخدم. رصيده الجديد: `{new_b}` نجمة.")
            try: await context.bot.send_message(chat_id=target_id, text=f"⚠️ تم خصم `{amount}` نجمة من محفظتك من قبل الإدارة.")
            except Exception: pass
        return

    if user_id in ADMIN_IDS and "adding_stock_for" in context.user_data:
        code = context.user_data["adding_stock_for"]
        del context.user_data["adding_stock_for"]
        if text_received.count(":") < 2:
            await update.message.reply_text("❌ صيغة خاطئة!")
            return
        parts = text_received.split(":")
        stock = load_data(NUMBERS_FILE)
        if code not in stock: stock[code] = []
        stock[code].append({"phone": parts[0].strip(), "code": parts[1].strip(), "two_step": parts[2].strip()})
        save_data(NUMBERS_FILE, stock)
        await update.message.reply_text("✅ تم إضافة الرقم للمخزن.")
        return

    if context.user_data.get("waiting_for_stars"):
        if not text_received or not text_received.isdigit():
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح:")
            return
        stars_amount = int(text_received)
        del context.user_data["waiting_for_stars"]
        prices = [LabeledPrice(label=f"شحن {stars_amount} نجمة", amount=stars_amount)]
        await context.bot.send_invoice(chat_id=update.message.chat_id, title="شحن محفظة فولت بوت", description=f"تعبئة لـ {stars_amount} نجمة", payload="wallet_topup_stars", provider_token="", currency="XTR", prices=prices)

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stars_received = update.message.successful_payment.total_amount
    new_total = update_balance(update.message.from_user.id, stars_received)
    await update.message.reply_text(f"🌟 تم شحن محفظتك بنجاح! رصيدك الحالي: `{new_total}` نجمة.")

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CommandHandler("broadcast", broadcast_command))
app.add_handler(CommandHandler("user", user_manage_command))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_and_messages))
app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

print("Volt Bot is Mega Muted with full interactive admin system...")
app.run_polling()
