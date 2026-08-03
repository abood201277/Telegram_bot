import json
import random
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)


TOKEN = "8600666559:AAHYg_Nmg212paIeR51Rk3T7eyZ8mloxuh0"
ADMIN_ID = 7555122412


# تخزين المستخدمين
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = {
        "approved": [],
        "rejected": []
    }


last_signal = None


def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)


def signal_generator():
    global last_signal

    if last_signal == "buy":
        signal = random.choices(
            ["buy", "sell"],
            weights=[40, 60]
        )[0]
    else:
        signal = random.choices(
            ["buy", "sell"],
            weights=[60, 40]
        )[0]

    last_signal = signal
    return signal



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    uid = user.id


    if uid in users["approved"]:
        await show_currencies(update)
        return


    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 إرسال طلب دخول",
                callback_data="new_request"
            )
        ]
    ]

    await update.message.reply_text(
        "⏳ جاري التحقق من الدخول...",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def send_request(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user


    keyboard = [
        [
            InlineKeyboardButton(
                "✅ موافقة",
                callback_data=f"approve_{user.id}"
            ),
            InlineKeyboardButton(
                "❌ رفض",
                callback_data=f"reject_{user.id}"
            )
        ]
    ]


    await context.bot.send_message(
        ADMIN_ID,
        f"""
📩 طلب دخول جديد

👤 الاسم: {user.first_name}
🔹 اليوزر: @{user.username}
🆔 الآيدي: {user.id}
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


    await update.message.reply_text(
        "⌛ تم إرسال طلبك، انتظر الموافقة."
    )



async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data


    if data == "new_request":

        await send_request(
            update,
            context
        )


    elif data.startswith("approve_"):

        uid = int(data.split("_")[1])

        if uid not in users["approved"]:
            users["approved"].append(uid)

        save_users()


        await context.bot.send_message(
            uid,
            "✅ تم قبول طلبك، أهلاً بك."
        )

        await context.bot.send_message(
            uid,
            "💱 اختر العملة:",
            reply_markup=currency_keyboard()
        )


    elif data.startswith("reject_"):

        uid = int(data.split("_")[1])


        if uid not in users["rejected"]:
            users["rejected"].append(uid)

        save_users()


        await context.bot.send_message(
            uid,
            "❌ تم رفض طلبك.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 إرسال طلب جديد",
                            callback_data="new_request"
                        )
                    ]
                ]
            )
        )



def currency_keyboard():

    coins = [
        "EUR/USD",
        "GBP/USD",
        "USD/JPY",
        "AUD/USD"
    ]

    buttons=[]

    for c in coins:
        buttons.append(
            [
                InlineKeyboardButton(
                    c,
                    callback_data=f"currency_{c}"
                )
            ]
        )

    return InlineKeyboardMarkup(buttons)



async def show_currencies(update):

    await update.effective_message.reply_text(
        "💱 اختر العملة:",
        reply_markup=currency_keyboard()
    )



async def choose_time(update, context):

    query = update.callback_query
    await query.answer()


    currency = query.data.replace(
        "currency_",
        ""
    )


    context.user_data["currency"] = currency


    now = datetime.now()


    buttons=[]

    for i in range(3):

        t = now + timedelta(minutes=i)

        buttons.append(
            [
                InlineKeyboardButton(
                    t.strftime("%H:%M"),
                    callback_data=f"time_{t.strftime('%H:%M')}"
                )
            ]
        )


    await query.message.reply_text(
        "⏰ اختر وقت الصفقة:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )



async def send_trade(update, context):

    query = update.callback_query
    await query.answer()


    time = query.data.replace(
        "time_",
        ""
    )

    currency = context.user_data.get(
        "currency",
        "EUR/USD"
    )


    signal = signal_generator()


    if signal == "buy":

        text=f"""
📊 إشارة جديدة

💱 العملة: {currency}
⏰ الوقت: {time}

📈 شراء

🟢 شموع صاعدة
"""

        await query.message.reply_photo(
            photo=open("up.png","rb"),
            caption=text
        )


    else:

        text=f"""
📊 إشارة جديدة

💱 العملة: {currency}
⏰ الوقت: {time}

📉 بيع

🔴 شموع هابطة
"""

        await query.message.reply_photo(
            photo=open("down.png","rb"),
            caption=text
        )



app = Application.builder().token(TOKEN).build()


app.add_handler(CommandHandler("start", start))

app.add_handler(
    CallbackQueryHandler(
        buttons,
        pattern="^(new_request|approve_|reject_)"
    )
)

app.add_handler(
    CallbackQueryHandler(
        choose_time,
        pattern="^currency_"
    )
)

app.add_handler(
    CallbackQueryHandler(
        send_trade,
        pattern="^time_"
    )
)


print("BOT STARTED")

app.run_polling()
