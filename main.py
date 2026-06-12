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

# إعداد الـ Logging لمعرفة الأخطاء في السيرفر إن وجدت
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ----------------- الإعدادات الأساسية -----------------
TOKEN = "8690641497:AAHYHhLEX53A_wRIAF5b2TviZUJR_2xq_aM"  # ضع توكن بوتك الحقيقي هنا بين العلامتين

ADMIN_ID =7555122412  # ضع هنا الآيدي الخاص بك كأدمن وحيد (رقم فقط)

# معرف قناة الإثباتات العامة
PROOF_CHANNEL = "@nwmbere"  

# يوزرك الشخصي اللي يظهر للمشتري حتى يراسلك وتسلمه الرقم
OWNER_USERNAME = "@Klm_r7"  

USD_TO_IQD = 1500  

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

# ------ نظام إدارة وحفظ الرصيد تلقائياً ------
BALANCE_FILE = "users_balance.json"

def load_balances():
    if os.path.exists(BALANCE_FILE):
        try:
            with open(BALANCE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_balances(balances):
    with open(BALANCE_FILE, "w") as f:
        json.dump(balances, f, indent=4)

def get_balance(user_id):
    balances = load_balances()
    return balances.get(str(user_id), 0.0)

def update_balance(user_id, amount):
    balances = load_balances()
    current = balances.get(str(user_id), 0.0)
    balances[str(user_id)] = round(current + amount, 2)
    save_balances(balances)
    return balances[str(user_id)]


# أمر /start للمستخدمين مع أزرار ملونة بالإيموجي
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🟢 📱 شراء رقم متاح 🟢", callback_query_data="buy")],
        [InlineKeyboardButton("🔵 💰 تعبئة رصيد المحفظة 🔵", callback_query_data="deposit_main")]
    ]
    
    text = (
        f"👋 أهلاً بك في متجر الأرقام المتكامل\n\n"
        f"💵 رصيد حسابك الحالي: {balance}$\n\n"
        f"اختر ما تريد من الأزرار أدناه:"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# معالجة الضغط على الأزرار والتنقل
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # 1. قائمة شراء الأرقام
    if query.data == "buy":
        keyboard = []
        for code, c in countries.items():
            keyboard.append([
                InlineKeyboardButton(f"🔹 {c['flag']} {c['name']} - {c['price']}$ 🔹", callback_data=f"buy_{code}")
            ])
        keyboard.append([InlineKeyboardButton("🔴 🔙 العودة للقائمة الرئيسية 🔴", callback_data="main_menu")])
        await query.edit_message_text("📱 اختر الدولة التي تريد شراء رقمها مباشرة من رصيدك:", reply_markup=InlineKeyboardMarkup(keyboard))

    # تنفيذ الشراء المباشر والخصم من الرصيد
    elif query.data.startswith("buy_"):
        code = query.data.split("_")[1]
        c = countries[code]
        user_balance = get_balance(user_id)
        
        if user_balance < c["price"]:
            await query.edit_message_text(
                f"❌ عذراً، رصيدك الحالي {user_balance}$ غير كافٍ لشراء رقم {c['name']} بسعر {c['price']}$.\n\n"
                f"يرجى الضغط على زر تعبئة الرصيد لشحن حسابك أولاً.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 💰 تعبئة الرصيد الآن 🔵", callback_data="deposit_main")]])
            )
            return

        new_bal = update_balance(user_id, -c["price"])
        order_id = random.randint(100000, 999999)
        
        success_text = (
            f"🎉 **تم الشراء بنجاح وخصم المبلغ!**\n\n"
            f"🏳️ الدولة: {c['flag']} {c['name']}\n"
            f"💵 السعر المخصوم: {c['price']}$\n"
            f"💰 رصيدك المتبقي: {new_bal}$\n\n"
            f"🆔 **رقم طلبك الخاص:** `{order_id}`\n\n"
            f"📥 لاستلام رقمك، يرجى نسخ رقم الطلب أعلاه ومراسلتي مباشرة عبر حسابي: {OWNER_USERNAME}"
        )
        await query.edit_message_text(success_text, parse_mode="Markdown")

        try:
            proof_channel_text = (
                f"🛍️ **عملية شراء رقم جديدة بنجاح!**\n\n"
                f"🆔 رقم الطلب: `{order_id}`\n"
                f"🏳️ الدولة المشترية: {c['flag']} {c['name']}\n"
                f"💵 القيمة المستقطعة: {c['price']}$\n"
                f"✅ الحالة: بانتظار تسليم الرقم للزبون عبر المطور.\n\n"
                f"ثقتكم هي شعارنا دائماً 🚀"
            )
            await context.bot.send_message(chat_id=PROOF_CHANNEL, text=proof_channel_text, parse_mode="Markdown")
        except Exception:
            pass

    # 2. قسم تعبئة الرصيد الملون مع زر النجوم التلقائي المباشر
    elif query.data == "deposit_main":
        keyboard = [
            [InlineKeyboardButton("⭐ شحن تلقائي فوري بالنجوم (Stars) ⭐", callback_query_data="charge_stars")],
            [InlineKeyboardButton("📱 تعبئة يدوية عبر آسيا سيل", callback_query_data="dep_asia")],
            [InlineKeyboardButton("🦁 تعبئة يدوية عبر أثير / زين", callback_query_data="dep_atheer")],
            [InlineKeyboardButton("🔴 🔙 العودة للقائمة الرئيسية 🔴", callback_query_data="main_menu")]
        ]
        await query.edit_message_text("💰 اختر وسيلة التحويل لتعبئة رصيد حسابك بالدولار داخل البوت:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "dep_asia":
        context.user_data["pending_deposit"] = {"method": "آسيا سيل"}
        await query.edit_message_text(
            f"📱 شحن وتعبئة الرصيد: آسيا سيل\n\n"
            f"قم بتحويل الرصيد أو كارت الشحن إلى الرقم التالي:\n`{ASIA_NUMBER}`\n\n"
            f"📥 بعد إتمام عملية التحويل، أرسل صورة إثبات التحويل هنا في البوت مباشرة ليرتفع طلبك للإدارة وتتم إضافة الرصيد لحسابك."
        )

    elif query.data == "dep_atheer":
        context.user_data["pending_deposit"] = {"method": "أثير"}
        await query.edit_message_text(
            f"🦁 شحن وتعبئة الرصيد: زين عراق / أثير\n\n"
            f"قم بتحويل الرصيد أو كارت الشحن إلى الرقم التالي:\n`{ATHEER_NUMBER}`\n\n"
            f"📥 بعد إتمام عملية التحويل، أرسل صورة إثبات التحويل هنا في البوت مباشرة ليرتفع طلبك للإدارة وتتم إضافة الرصيد لحسابك."
        )

    # توليد فاتورة النجوم الفورية (50 نجمة تعطي رصيد 0.50$ بالمحفظة تلقائياً)
    elif query.data == "charge_stars":
        chat_id = query.message.chat_id
        title = "شحن المحفظة بالنجوم"
        description = "شحن تلقائي فوري لرصيدك بمقدار 50 نجمة ($0.50)"
        payload = "wallet_topup_stars"
        currency = "XTR"
        prices = [LabeledPrice(label="شحن 50 نجمة", amount=50)]
        
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",
            currency=currency,
            prices=prices
        )

    # العودة للقائمة الرئيسية
    elif query.data == "main_menu":
        await start(update, context)

    # معالجة قبول الأدمن للشحن اليدوي بالصور
    elif query.data.startswith("adm_add_"):
        parts = query.data.split("_")
        target_user_id = int(parts[2])
        method = parts[3]
        
        deposit_amount = 5.0 
        new_total = update_balance(target_user_id, deposit_amount)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ تم قبول إثبات الشحن الخاص بك ({method})!\n💰 تم شحن وتعبئة حسابك بـ {deposit_amount}$ بنجاح.\n💵 رصيدك الكلي الحالي هو: {new_total}$"
            )
        except Exception:
            pass
            
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ تم قبول التعبئة وإضافة {deposit_amount}$ بنجاح للمستخدم.")

    # معالجة رفض طلب التعبئة اليدوي من الأدمن
    elif query.data.startswith("adm_deny_"):
        parts = query.data.split("_")
        target_user_id = int(parts[2])
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="❌ نعتذر منك، تم رفض إثبات تحويل رصيد التعبئة بعد تدقيقه. يرجى التأكد من إرسال الإثبات الصحيح."
            )
        except Exception:
            pass
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ تم رفض طلب الشحن هذا.")

# موافقة سيرفر تليجرام التلقائية على فاتورة النجوم
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != "wallet_topup_stars":
        await query.answer(ok=False, error_message="حدث خطأ في الفاتورة.")
    else:
        await query.answer(ok=True)

# استقبال النجوم وشحن ملف الـ JSON فوراً (1 نجمة = 1 سنت)
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    user_id = update.message.from_user.id
    stars_received = payment.total_amount
    
    # الحسبة: 50 نجمة تعادل 0.50$ دولار في حساب المستخدم بالملف
    added_amount = stars_received * 0.01
    new_total_balance = update_balance(user_id, added_amount)
    
    success_text = (
        f"🌟 **تهانينا! تم الشحن التلقائي بنجاح!** 🌟\n\n"
        f"📥 تم استقبال: {stars_received} نجمة تليجرام.\n"
        f"💰 تم شحن محفظتك بـ: +{added_amount}$\n"
        f"💵 رصيدك الكلي الحالي أصبح: {new_total_balance}$"
    )
    await update.message.reply_text(success_text)

# استلام صور إثباتات الشحن اليدوية من الزبائن
async def handle_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "pending_deposit" not in context.user_data:
        return  
        
    deposit = context.user_data["pending_deposit"]
    user = update.effective_user
    
    admin_caption = (
        f"🚨 **طلب شحن وتعبئة رصيد جديد معلق!**\n\n"
        f"👤 اسم الزبون: {user.first_name}\n"
        f"🆔 آيدي الحساب: {user.id}\n"
        f"💳 وسيلة الشحن: {deposit['method']}\n"
        f"⚠️ اضغط قبول لإضافة رصيد شحن تلقائي قيمته (5$) للحساب.\n"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول وشحن الحساب", callback_data=f"adm_add_{user.id}_{deposit['method']}"),
            InlineKeyboardButton("❌ رفض الإثبات", callback_data=f"adm_deny_{user.id}")
        ]
    ]
    
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=admin_caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Error sending to admin: {e}")
            
    await update.message.reply_text("📥 تم إرسال صورة إثبات التعبئة بنجاح إلى المطور. سيتم مراجعة التحويل وإضافة الرصيد لمحفظتك فوراً...")
    del context.user_data["pending_deposit"]

# تشغيل البوت وربط جميع المحركات
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.PHOTO, handle_proof))

# ربط محركات دفع واستلام النجوم التلقائية بالبوت مالتك
app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

print("Wallet-Based Bot with Stars and Emojis running perfectly...")
app.run_polling()
