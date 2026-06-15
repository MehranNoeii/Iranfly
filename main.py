import telebot
import mysql.connector
import random
import time
import logging
from datetime import datetime
from config import *
from DDL import *

bot = telebot.TeleBot(API_TOKEN)
logging.basicConfig(
    filename="iranfly.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
init_database()

def connect_db():
    config = database_config.copy()
    config['database'] = database_name
    return mysql.connector.connect(**config)

def send_message(*args, **kwargs):
    try:
        return bot.send_message(*args, **kwargs)
    except Exception as e:
        logging.error(str(e))

def generate_unique_seat(class_type, used_seats):
    if class_type == "economy":
        rows = ['A', 'B', 'C', 'D', 'E', 'F']
        max_seat = 30
    else:
        rows = ['A', 'B', 'C', 'D']
        max_seat = 20
    
    for _ in range(100):
        seat_letter = random.choice(rows)
        seat_num = random.randint(1, max_seat)
        seat_number = f"{seat_letter}{seat_num}"
        if seat_number not in used_seats:
            return seat_number
    return f"X{random.randint(1, 999)}"

user_steps = {}
user_data = {}
flight_search = {}
reservation_data = {}

def show_main_menu(cid):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("✈️ خرید بلیط")
    keyboard.row("🎫 بلیط های من", "📄 فاکتورهای من")
    keyboard.row("👤 پروفایل من", "☎️ پشتیبانی")
    send_message(cid, "🏠 منوی اصلی", reply_markup=keyboard)

def show_back_menu(cid):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🏠 بازگشت به منوی اصلی")
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    cid = message.chat.id
    logging.info(
    f"User Started Bot | {cid}"
    )
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE cid=%s", (cid,))
    user = cursor.fetchone()
    db.close()
    
    if user:
        show_main_menu(cid)
        return
    
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📝 ثبت نام")
    send_message(cid, "✈️ به ایران فلای خوش آمدید\n\nلطفاً ثبت نام کنید", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "📝 ثبت نام")
def register(message):
    cid = message.chat.id
    user_steps[cid] = "first_name"
    send_message(cid, "نام خود را وارد کنید:")

@bot.message_handler(func=lambda m: m.text == "🏠 بازگشت به منوی اصلی")
def back_main(message):
    cid = message.chat.id
    user_steps.pop(cid, None)
    user_data.pop(cid, None)
    flight_search.pop(cid, None)
    reservation_data.pop(cid, None)
    show_main_menu(cid)

@bot.message_handler(func=lambda m: m.text == "👤 پروفایل من")
def profile(message):
    cid = message.chat.id
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE cid=%s", (cid,))
    user = cursor.fetchone()
    db.close()
    if not user:
        return
    text = f"👤 نام: {user['first_name']} {user['last_name']}\n🆔 کد ملی: {user['national_code']}\n📱 شماره: {user['phone_number']}"
    send_message(cid, text, reply_markup=show_back_menu(cid))

@bot.message_handler(func=lambda m: m.text == "☎️ پشتیبانی")
def support(message):
    send_message(message.chat.id, "☎️ پشتیبانی ایران فلای\n\n@IranFlySupport", reply_markup=show_back_menu(message.chat.id))

@bot.message_handler(func=lambda m: m.text == "✈️ خرید بلیط")
def buy_ticket(message):
    cid = message.chat.id
    send_message(cid, "🛫", reply_markup=show_back_menu(cid))
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("🇮🇷 پرواز داخلی", callback_data="domestic"))
    keyboard.add(telebot.types.InlineKeyboardButton("🌍 پرواز خارجی", callback_data="international"))
    bot.send_message(cid, "نوع پرواز را انتخاب کنید:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data in ["domestic", "international"])
def select_flight_type(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    flight_search[cid] = {"flight_type": call.data}
    
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    if call.data == "domestic":
        cursor.execute("SELECT * FROM airports WHERE airport_type IN ('domestic','both') ORDER BY city")
    else:
        cursor.execute("SELECT * FROM airports WHERE country='ایران' AND airport_type IN ('international','both') ORDER BY city")
    airports = cursor.fetchall()
    db.close()
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    for airport in airports:
        keyboard.add(telebot.types.InlineKeyboardButton(f"{airport['city']} - {airport['airport_name']}", callback_data=f"origin_{airport['airport_id']}"))
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_type"))
    bot.edit_message_text("مبدا را انتخاب کنید:", chat_id=cid, message_id=call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("origin_"))
def select_origin(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    airport_id = int(call.data.split("_")[1])
    flight_search[cid]["origin_airport_id"] = airport_id
    
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    if flight_search[cid]["flight_type"] == "domestic":
        cursor.execute("SELECT * FROM airports WHERE airport_id != %s AND airport_type IN ('domestic','both') ORDER BY city", (airport_id,))
    else:
        cursor.execute("SELECT * FROM airports WHERE country!='ایران' AND airport_type='international' ORDER BY city")
    airports = cursor.fetchall()
    db.close()
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    for airport in airports:
        keyboard.add(telebot.types.InlineKeyboardButton(f"{airport['city']} - {airport['airport_name']}", callback_data=f"destination_{airport['airport_id']}"))
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_origin"))
    bot.edit_message_text("مقصد را انتخاب کنید:", chat_id=cid, message_id=call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("destination_"))
def select_destination(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    destination_id = int(call.data.split("_")[1])
    flight_search[cid]["destination_airport_id"] = destination_id
    bot.delete_message(chat_id=cid, message_id=call.message.message_id)
    user_steps[cid] = "flight_date"
    send_message(cid, "📅 تاریخ پرواز را وارد کنید:\nمثال: 2026-07-01")

@bot.callback_query_handler(func=lambda call: call.data.startswith("flight_"))
def choose_flight(call):
    cid = call.message.chat.id
    
    flight_id = int(call.data.split("_")[1])
    flight_search[cid]["flight_id"] = flight_id
    logging.info(
    f"New User Registered | {cid}"
)
    
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
    SELECT f.*, 
           a1.city as origin_city, a1.airport_name as origin_name,
           a2.city as destination_city, a2.airport_name as destination_name,
           al.airline_name
    FROM flights f
    JOIN airports a1 ON f.origin_airport_id = a1.airport_id
    JOIN airports a2 ON f.destination_airport_id = a2.airport_id
    JOIN airlines al ON f.airline_id = al.airline_id
    WHERE f.flight_id = %s
    """, (flight_id,))
    
    flight = cursor.fetchone()
    db.close()
    
    bot.delete_message(chat_id=cid, message_id=call.message.message_id)
    
    flight_type_text = "🇮🇷 پرواز داخلی" if flight['flight_type'] == 'domestic' else "🌍 پرواز خارجی"
    
    text = f"""
✈️ *اطلاعات پرواز*

{flight_type_text}

🆔 *شماره پرواز:* {flight['flight_number']}
🏢 *هواپیمایی:* {flight['airline_name']}

📍 *مبدا:* {flight['origin_city']} ({flight['origin_name']})
📍 *مقصد:* {flight['destination_city']} ({flight['destination_name']})

📅 *تاریخ پرواز:* {flight['departure_date']}
🕐 *ساعت حرکت:* {flight['departure_time']}
🕓 *ساعت رسیدن:* {flight['arrival_time']}


💺 *کلاس اقتصادی:* {flight['economy_price']:,.0f} تومان
💼 *کلاس بیزینس:* {flight['business_price']:,.0f} تومان


لطفاً کلاس مورد نظر خود را انتخاب کنید:
"""
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton("💺 اکونومی", callback_data="class_economy"),
        telebot.types.InlineKeyboardButton("💼 بیزینس", callback_data="class_business")
    )
    
    bot.send_message(cid, text, reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("class_"))
def choose_class(call):
    cid = call.message.chat.id
    
    bot.delete_message(chat_id=cid, message_id=call.message.message_id)
    
    class_type = call.data.split("_")[1]
    
    reservation_data[cid] = {
        "class_type": class_type,
        "passengers": []
    }
    
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("👤 خودم", "➕ مسافر جدید")
    keyboard.row("🏠 بازگشت به منوی اصلی")
    
    user_steps[cid] = "select_passenger_type"
    
    bot.send_message(
        cid,
        "مسافر را انتخاب کنید:\n\n👤 خودم - اطلاعات من استفاده شود\n➕ مسافر جدید - اطلاعات جدید وارد کنم",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_type")
def back_to_type(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    flight_search.pop(cid, None)
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("🇮🇷 پرواز داخلی", callback_data="domestic"))
    keyboard.add(telebot.types.InlineKeyboardButton("🌍 پرواز خارجی", callback_data="international"))
    bot.edit_message_text("نوع پرواز را انتخاب کنید:", chat_id=cid, message_id=call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_origin")
def back_to_origin(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    flight_type = flight_search.get(cid, {}).get("flight_type", "domestic")
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    if flight_type == "domestic":
        cursor.execute("SELECT * FROM airports WHERE airport_type IN ('domestic','both') ORDER BY city")
    else:
        cursor.execute("SELECT * FROM airports ORDER BY city")
    airports = cursor.fetchall()
    db.close()
    keyboard = telebot.types.InlineKeyboardMarkup()
    for airport in airports:
        keyboard.add(telebot.types.InlineKeyboardButton(airport["city"], callback_data=f"origin_{airport['airport_id']}"))
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_type"))
    bot.edit_message_text("مبدا را انتخاب کنید:", chat_id=cid, message_id=call.message.message_id, reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "🎫 بلیط های من")
def my_tickets(message):
    cid = message.chat.id
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
    SELECT t.ticket_code, t.class_type, f.flight_number, f.departure_date, f.departure_time,
           o.city as origin_city, d.city as destination_city,
           p.first_name_fa, p.last_name_fa, p.national_code, r.reservation_code
    FROM tickets t
    JOIN passengers p ON t.passenger_id = p.passenger_id
    JOIN flights f ON t.flight_id = f.flight_id
    JOIN airports o ON f.origin_airport_id = o.airport_id
    JOIN airports d ON f.destination_airport_id = d.airport_id
    JOIN reservations r ON p.reservation_id = r.reservation_id
    JOIN users u ON r.user_id = u.user_id
    WHERE u.cid = %s AND t.status = 'issued'
    """, (cid,))
    tickets = cursor.fetchall()
    db.close()
    if not tickets:
        send_message(cid, "❌ شما هیچ بلیطی ندارید.", reply_markup=show_back_menu(cid))
        return
    for t in tickets:
        class_icon = "💺" if t['class_type'] == 'economy' else "💼"
        text = f"""
🎫 *بلیط پرواز*

👤 *مسافر:* {t['first_name_fa']} {t['last_name_fa']}
🆔 *کد ملی:* {t['national_code']}

✈️ *شماره پرواز:* {t['flight_number']}
📍 *مسیر:* {t['origin_city']} ➜ {t['destination_city']}
📅 *تاریخ:* {t['departure_date']}
🕐 *ساعت:* {t['departure_time']}
{class_icon} *کلاس:* {t['class_type']}

🎟️ *کد بلیط:* `{t['ticket_code']}`
📋 *کد رزرو:* `{t['reservation_code']}`
"""
        send_message(cid, text, reply_markup=show_back_menu(cid), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📄 فاکتورهای من")
def my_invoices(message):
    cid = message.chat.id
    
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
    SELECT r.reservation_id, r.reservation_code, r.total_amount, r.status, r.created_at,
           p.status as payment_status, p.payment_id,
           COUNT(pass.passenger_id) as passenger_count
    FROM reservations r
    LEFT JOIN payments p ON r.reservation_id = p.reservation_id
    LEFT JOIN passengers pass ON r.reservation_id = pass.reservation_id
    JOIN users u ON r.user_id = u.user_id
    WHERE u.cid = %s
    GROUP BY r.reservation_id
    ORDER BY r.created_at DESC
    """, (cid,))
    
    invoices = cursor.fetchall()
    db.close()
    
    if not invoices:
        send_message(cid, "❌ هیچ فاکتوری یافت نشد.", reply_markup=show_back_menu(cid))
        return
    
    for inv in invoices:
        if inv['payment_status'] == 'verified':
            status_text = "✅ پرداخت شده"
            can_pay = False
            can_delete = False
        elif inv['payment_status'] == 'pending':
            status_text = "⏳ در انتظار تایید"
            can_pay = False
            can_delete = True
        else:
            status_text = "❌ پرداخت نشده"
            can_pay = True
            can_delete = True
        
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        
        if can_pay and can_delete:
            keyboard.add(
                telebot.types.InlineKeyboardButton("💳 پرداخت فاکتور", callback_data=f"pay_invoice_{inv['reservation_id']}"),
                telebot.types.InlineKeyboardButton("🗑 حذف فاکتور", callback_data=f"delete_invoice_{inv['reservation_id']}")
            )
        elif can_delete:
            keyboard.add(
                telebot.types.InlineKeyboardButton("🗑 حذف فاکتور", callback_data=f"delete_invoice_{inv['reservation_id']}")
            )
        
        text = f"""
📄 *فاکتور خرید*

🎫 *کد رزرو:* `{inv['reservation_code']}`
👥 *تعداد مسافران:* {inv['passenger_count']}
💰 *مبلغ کل:* {inv['total_amount']:,.0f} تومان
✅ *وضعیت:* {status_text}
📅 *تاریخ ثبت:* {inv['created_at']}
"""
        send_message(cid, text, reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_invoice_"))
def delete_invoice(call):
    cid = call.message.chat.id
    reservation_id = int(call.data.split("_")[2])
    
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
    SELECT r.status, p.status as payment_status
    FROM reservations r
    LEFT JOIN payments p ON r.reservation_id = p.reservation_id
    WHERE r.reservation_id = %s
    """, (reservation_id,))
    
    inv = cursor.fetchone()
    
    if not inv:
        bot.answer_callback_query(call.id, "❌ فاکتور یافت نشد")
        db.close()
        return
    
    if inv['payment_status'] == 'verified':
        bot.answer_callback_query(call.id, "❌ این فاکتور قبلاً پرداخت شده و قابل حذف نیست")
        db.close()
        return
    
    cursor.execute("DELETE FROM tickets WHERE passenger_id IN (SELECT passenger_id FROM passengers WHERE reservation_id=%s)", (reservation_id,))
    cursor.execute("DELETE FROM passengers WHERE reservation_id=%s", (reservation_id,))
    cursor.execute("DELETE FROM payments WHERE reservation_id=%s", (reservation_id,))
    cursor.execute("DELETE FROM reservations WHERE reservation_id=%s", (reservation_id,))
    
    db.commit()
    db.close()
    
    bot.answer_callback_query(call.id, "🗑 فاکتور با موفقیت حذف شد")
    
    bot.edit_message_text(
        f"✅ فاکتور مورد نظر با موفقیت حذف شد",
        chat_id=cid,
        message_id=call.message.message_id
    )
    
    time.sleep(2)
    bot.delete_message(chat_id=cid, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_invoice_"))
def pay_invoice(call):
    cid = call.message.chat.id
    reservation_id = int(call.data.split("_")[2])
    
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
    SELECT r.*, f.flight_id
    FROM reservations r
    JOIN flights f ON r.flight_id = f.flight_id
    WHERE r.reservation_id = %s
    """, (reservation_id,))
    
    reservation = cursor.fetchone()
    db.close()
    
    if not reservation:
        bot.answer_callback_query(call.id, "❌ فاکتور یافت نشد")
        return
    
    flight_search[cid] = {
        "flight_id": reservation["flight_id"]
    }
    reservation_data[cid] = {
        "reservation_code": reservation["reservation_code"],
        "reservation_id": reservation_id
    }
    
    user_steps[cid] = "payment_receipt"
    
    bot.answer_callback_query(call.id, "💰 لطفاً فیش پرداخت را ارسال کنید")
    
    bot.edit_message_text(
        f"💰 *درگاه پرداخت*\n──────────────────\n🎫 کد رزرو: `{reservation['reservation_code']}`\n💰 مبلغ قابل پرداخت: {reservation['total_amount']:,.0f} تومان\n──────────────────\n\nلطفاً فیش پرداخت را ارسال کنید:",
        chat_id=cid,
        message_id=call.message.message_id,
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id not in ADMIN_ID:
        return
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📋 رزروها", "💳 پرداخت ها")
    keyboard.row("🏠 بازگشت به منوی اصلی")
    send_message(message.chat.id, "👑 پنل مدیریت", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "📋 رزروها")
def admin_reservations(message):
    if message.chat.id not in ADMIN_ID:
        return
    
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
    SELECT r.*, u.first_name, u.last_name, u.phone_number, f.flight_number,
           o.city as origin_city, d.city as destination_city
    FROM reservations r
    JOIN users u ON r.user_id = u.user_id
    JOIN flights f ON r.flight_id = f.flight_id
    JOIN airports o ON f.origin_airport_id = o.airport_id
    JOIN airports d ON f.destination_airport_id = d.airport_id
    ORDER BY r.reservation_id DESC LIMIT 30
    """)
    rows = cursor.fetchall()
    db.close()
    
    if not rows:
        send_message(message.chat.id, "❌ هیچ رزروی یافت نشد.")
        return
    
    for row in rows:
        if row['status'] == 'confirmed':
            status_icon = "✅ تایید شده"
        elif row['status'] == 'pending_payment':
            status_icon = "⏳ در انتظار پرداخت"
        elif row['status'] == 'pending_verification':
            status_icon = "🔄 در انتظار تایید"
        elif row['status'] == 'cancelled':
            status_icon = "❌ لغو شده"
        else:
            status_icon = "❓ نامشخص"
        
        text = f"""
📋 *رزرو جدید*

👤 *کاربر:* {row['first_name']} {row['last_name']}
📱 *شماره:* {row['phone_number']}
✈️ *پرواز:* {row['flight_number']}
📍 *مسیر:* {row['origin_city']} ➜ {row['destination_city']}
🎫 *کد رزرو:* `{row['reservation_code']}`
💰 *مبلغ:* {row['total_amount']:,.0f} تومان
📅 *تاریخ:* {row['created_at']}
✅ *وضعیت:* {status_icon}
"""
        send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 پرداخت ها")
def admin_payments(message):
    if message.chat.id not in ADMIN_ID:
        return
    
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
    SELECT p.*, r.reservation_code, u.first_name, u.last_name
    FROM payments p
    JOIN reservations r ON p.reservation_id = r.reservation_id
    JOIN users u ON r.user_id = u.user_id
    WHERE p.status = 'pending'
    """)
    rows = cursor.fetchall()
    db.close()
    
    if not rows:
        send_message(message.chat.id, "✅ هیچ پرداخت در انتظار تاییدی وجود ندارد")
        return
    
    for row in rows:
        bot.send_photo(
            message.chat.id, 
            row["receipt_file_id"],
            caption=f"📋 *فیش پرداخت*\n━━━━━━━━━━━━━━\n🎫 کد رزرو: `{row['reservation_code']}`\n👤 کاربر: {row['first_name']} {row['last_name']}\n💰 مبلغ: {row['amount']:,.0f} تومان\n📅 تاریخ: {row['payment_date']}",
            parse_mode="Markdown"
        )
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton("تایید پرداخت", callback_data=f"verify_{row['payment_id']}"))
        send_message(message.chat.id, f"🆔 شناسه پرداخت: {row['payment_id']}", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def verify_payment(call):
    payment_id = int(call.data.split("_")[1])
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("UPDATE payments SET status='verified' WHERE payment_id=%s", (payment_id,))
    cursor.execute("SELECT reservation_id FROM payments WHERE payment_id=%s", (payment_id,))
    row = cursor.fetchone()
    cursor.execute("UPDATE reservations SET status='confirmed' WHERE reservation_id=%s", (row["reservation_id"],))
    db.commit()
    db.close()
    
    bot.edit_message_text(
        "✅ تایید شده",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )
    
    bot.answer_callback_query(call.id, "پرداخت با موفقیت تایید شد")

@bot.message_handler(func=lambda m: m.chat.id in user_steps)
def register_steps(message):
    cid = message.chat.id
    if message.text == "🏠 بازگشت به منوی اصلی":
        back_main(message)
        return
    
    step = user_steps[cid]
    
    if step == "first_name":
        name = message.text.strip()
        if len(name) < 3:
            send_message(cid, "❌ نام معتبر وارد کنید.")
            return
        if any(ch.isdigit() for ch in name):
            send_message(cid, "❌ نام نباید شامل عدد باشد.")
            return
        user_data[cid] = {"first_name": name}
        user_steps[cid] = "last_name"
        send_message(cid, "نام خانوادگی:")
    
    elif step == "last_name":
        name = message.text.strip()
        if len(name) < 3:
            send_message(cid, "❌ نام خانوادگی معتبر وارد کنید")
            return
        if any(ch.isdigit() for ch in name):
            send_message(cid, "❌ نام خانوادگی نباید شامل عدد باشد")
            return
        user_data[cid]["last_name"] = name
        user_steps[cid] = "national_code"
        send_message(cid, "کد ملی (10 رقم):")
    
    elif step == "national_code":
        code = message.text.strip()
        if not code.isdigit() or len(code) != 10:
            send_message(cid, "❌ کد ملی 10 رقمی معتبر وارد کنید.")
            return
        user_data[cid]["national_code"] = code
        user_steps[cid] = "birth_date"
        send_message(cid, "تاریخ تولد:\nمثال: 1366-05-20")
    
    elif step == "birth_date":
        try:
            datetime.strptime(message.text, "%Y-%m-%d")
        except:
            send_message(cid, "❌ فرمت صحیح: 1385-05-20")
            return
        user_data[cid]["birth_date"] = message.text
        user_steps[cid] = "gender"
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row("مرد", "زن")
        send_message(cid, "جنسیت:", reply_markup=keyboard)
    
    elif step == "gender":
        if message.text not in ["مرد", "زن"]:
            send_message(cid, "❌ یکی از گزینه‌ها را انتخاب کنید.")
            return
        user_data[cid]["gender"] = "male" if message.text == "مرد" else "female"
        user_steps[cid] = "phone"
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(telebot.types.KeyboardButton("📱 ارسال شماره تماس", request_contact=True))
        send_message(cid, "شماره تماس خود را ارسال کنید:", reply_markup=keyboard)
    
    elif step == "flight_date":
        try:
            datetime.strptime(message.text, "%Y-%m-%d")
        except:
            send_message(cid, "❌ فرمت اشتباه.\nمثال: 2026-07-01")
            return
        flight_search[cid]["departure_date"] = message.text
        data = flight_search[cid]
        db = connect_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
        SELECT f.*, a1.city as origin_city, a2.city as destination_city, al.airline_name
        FROM flights f
        JOIN airports a1 ON f.origin_airport_id = a1.airport_id
        JOIN airports a2 ON f.destination_airport_id = a2.airport_id
        JOIN airlines al ON f.airline_id = al.airline_id
        WHERE f.flight_type=%s AND f.origin_airport_id=%s 
        AND f.destination_airport_id=%s AND f.departure_date=%s AND f.status='available'
        """, (data["flight_type"], data["origin_airport_id"], data["destination_airport_id"], data["departure_date"]))
        flights = cursor.fetchall()
        db.close()
        if not flights:
            send_message(cid, "❌ پروازی پیدا نشد.")
            return
        del user_steps[cid]
        for flight in flights:
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(telebot.types.InlineKeyboardButton("✈️ انتخاب پرواز", callback_data=f"flight_{flight['flight_id']}"))
            text = f"""
✈️ *پرواز {flight['flight_number']}*
🏢 {flight['airline_name']}
📍 {flight['origin_city']} ➜ {flight['destination_city']}
🕐 {flight['departure_time']} → {flight['arrival_time']}
💺 اکونومی: {flight['economy_price']:,.0f} تومان
💼 بیزینس: {flight['business_price']:,.0f} تومان
"""
            bot.send_message(cid, text, reply_markup=keyboard, parse_mode="Markdown")
    
    elif step == "select_passenger_type":
        if message.text == "👤 خودم":
            db = connect_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE cid=%s", (cid,))
            user = cursor.fetchone()
            db.close()
            if user:
                reservation_data[cid]["passengers"] = [{
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "national_code": user["national_code"],
                    "birth_date": user["birth_date"].strftime("%Y-%m-%d") if user["birth_date"] else None
                }]
                finalize_reservation(cid)
            else:
                send_message(cid, "❌ اطلاعات شما یافت نشد.")
        elif message.text == "➕ مسافر جدید":
            user_steps[cid] = "passenger_count"
            send_message(cid, "👥 تعداد مسافران (حداکثر 6 نفر):")
        elif message.text != "🏠 بازگشت به منوی اصلی":
            send_message(cid, "❌ لطفاً یکی از گزینه‌ها را انتخاب کنید.")
    
    elif step == "passenger_count":
        try:
            count = int(message.text.strip())
            if count < 1 or count > 6:
                raise ValueError
        except:
            send_message(cid, "❌ تعداد معتبر وارد کنید (1-6).")
            return
        reservation_data[cid]["passenger_count"] = count
        reservation_data[cid]["passengers"] = []
        reservation_data[cid]["current"] = 1
        user_steps[cid] = "new_passenger_name"
        send_message(cid, f"👤 نام و نام خانوادگی مسافر شماره 1:")
    
    elif step == "new_passenger_name":
        full_name = message.text.strip()
        
        if any(ch.isdigit() for ch in full_name):
            send_message(cid, "❌ نام مسافر نباید شامل عدد باشد.\nلطفاً فقط از حروف استفاده کنید.")
            return
        
        for ch in full_name:
            if not (ch.isalpha() or ch == " "):
                send_message(cid, "❌ نام فقط باید شامل حروف باشد.")
                return
        
        if len(full_name) < 3:
            send_message(cid, "❌ نام معتبر وارد کنید (حداقل 3 حرف).")
            return
        
        parts = full_name.split()
        reservation_data[cid]["current_first"] = parts[0]
        reservation_data[cid]["current_last"] = " ".join(parts[1:]) if len(parts) > 1 else ""
        user_steps[cid] = "new_passenger_national_code"
        send_message(cid, "📇 کد ملی (10 رقم):")
    
    elif step == "new_passenger_national_code":
        code = message.text.strip()
        if not code.isdigit() or len(code) != 10:
            send_message(cid, "❌ کد ملی 10 رقمی معتبر وارد کنید.")
            return
        reservation_data[cid]["passengers"].append({
            "first_name": reservation_data[cid]["current_first"],
            "last_name": reservation_data[cid]["current_last"],
            "national_code": code
        })
        current = len(reservation_data[cid]["passengers"])
        total = reservation_data[cid]["passenger_count"]
        if current < total:
            user_steps[cid] = "new_passenger_name"
            send_message(cid, f"👤 نام و نام خانوادگی مسافر شماره {current + 1}:")
        else:
            finalize_reservation(cid)

def finalize_reservation(cid):
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE cid=%s", (cid,))
    user = cursor.fetchone()
    
    flight_id = flight_search[cid]["flight_id"]
    cursor.execute("SELECT * FROM flights WHERE flight_id=%s", (flight_id,))
    flight = cursor.fetchone()
    
    total = len(reservation_data[cid]["passengers"])
    class_type = reservation_data[cid]["class_type"]
    
    if class_type == "economy":
        amount = float(flight["economy_price"]) * total
    else:
        amount = float(flight["business_price"]) * total
    
    reservation_code = "RF" + str(random.randint(100000, 999999))
    
    cursor.execute("""
    INSERT INTO reservations (user_id, flight_id, reservation_code, total_amount, status)
    VALUES (%s, %s, %s, %s, %s)
    """, (user["user_id"], flight_id, reservation_code, amount, "pending_payment"))
    
    reservation_id = cursor.lastrowid
    
    cursor.execute("SELECT seat_number FROM tickets WHERE flight_id=%s AND seat_number IS NOT NULL", (flight_id,))
    used_seats = [row["seat_number"] for row in cursor.fetchall()]
    
    for passenger in reservation_data[cid]["passengers"]:
        cursor.execute("""
        INSERT INTO passengers (reservation_id, passenger_type, first_name_fa, last_name_fa, national_code)
        VALUES (%s, %s, %s, %s, %s)
        """, (reservation_id, flight["flight_type"], passenger["first_name"], passenger["last_name"], passenger["national_code"]))
        
        passenger_id = cursor.lastrowid
        seat_number = generate_unique_seat(class_type, used_seats)
        used_seats.append(seat_number)
        ticket_code = "TK" + str(random.randint(100000, 999999))
        
        cursor.execute("""
        INSERT INTO tickets (passenger_id, flight_id, seat_number, class_type, ticket_code, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (passenger_id, flight_id, seat_number, class_type, ticket_code, "issued"))
    
    db.commit()
    db.close()
    
    show_main_menu(cid)
    
    text = f"""
✅ *رزرو با موفقیت ثبت شد*


🎫 *کد رزرو:* `{reservation_code}`
👥 *تعداد مسافران:* {total}
💰 *مبلغ کل:* {amount:,.0f} تومان


📌 لطفاً تصویر فیش پرداخت را ارسال کنید.

*نحوه ارسال عکس:*
1. روی علامت 📎 کلیک کنید
2. گزینه Gallery یا Camera را انتخاب کنید
3. عکس فیش را ارسال کنید

⚠️ توجه: فقط عکس قبول می‌شود.
"""
    send_message(cid, text, parse_mode="Markdown")
    user_steps[cid] = "payment_receipt"
    reservation_data[cid]["reservation_code"] = reservation_code

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    cid = message.chat.id
    if cid not in user_steps or user_steps[cid] != "phone":
        return
    if message.contact.user_id != cid:
        send_message(cid, "❌ فقط شماره خودتان را ارسال کنید.")
        return
    
    data = user_data[cid]
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
    INSERT INTO users (cid, first_name, last_name, national_code, birth_date, gender, phone_number)
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (cid, data["first_name"], data["last_name"], data["national_code"], data["birth_date"], data["gender"], message.contact.phone_number))
    db.commit()
    logging.info(
    f"New User Registered | {cid}"
)
    db.close()
    
    user_steps.pop(cid, None)
    user_data.pop(cid, None)
    send_message(cid, "✅ ثبت نام با موفقیت انجام شد.")
    show_main_menu(cid)

@bot.message_handler(content_types=['photo'])
def receive_receipt(message):
    cid = message.chat.id
    if cid not in user_steps or user_steps[cid] != "payment_receipt":
        return
    
    file_id = message.photo[-1].file_id
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    
    if "reservation_id" in reservation_data.get(cid, {}):
        reservation_id = reservation_data[cid]["reservation_id"]
        cursor.execute("SELECT total_amount FROM reservations WHERE reservation_id=%s", (reservation_id,))
        row = cursor.fetchone()
        amount = row["total_amount"] if row else 0
    else:
        cursor.execute("""
        SELECT r.reservation_id, r.total_amount
        FROM reservations r
        JOIN users u ON r.user_id = u.user_id
        WHERE u.cid = %s
        ORDER BY r.reservation_id DESC LIMIT 1
        """, (cid,))
        row = cursor.fetchone()
        reservation_id = row["reservation_id"] if row else None
        amount = row["total_amount"] if row else 0
    
    if reservation_id:
        cursor.execute("""
        INSERT INTO payments (reservation_id, receipt_file_id, amount, status)
        VALUES (%s, %s, %s, %s)
        """, (reservation_id, file_id, amount, "pending"))
        db.commit()
        send_message(cid, "✅ فیش شما ثبت شد و در انتظار تایید ادمین است")
    else:
        send_message(cid, "❌ خطا در ثبت فیش. لطفاً دوباره تلاش کنید")
    
    user_steps.pop(cid, None)
    reservation_data.pop(cid, None)
    db.close()
    show_main_menu(cid)

@bot.message_handler(content_types=['text', 'document', 'video', 'audio', 'sticker', 'animation', 'voice', 'video_note', 'location', 'venue'])
def handle_non_photo_payment(message):
    cid = message.chat.id
    
    if cid in user_steps and user_steps[cid] == "payment_receipt":
        send_message(
            cid,
            "❌ *فرمت فایل نامعتبر است!*\n\n"
            "لطفاً فقط یک *عکس* از فیش پرداخت ارسال کنید\n\n"
            "📌 *نحوه ارسال عکس:*\n"
            "1. روی علامت 📎 کلیک کنید\n"
            "2. گزینه *Gallery* یا *Camera* را انتخاب کنید\n"
            "3. عکس فیش را انتخاب کنید و ارسال نمایید",
            parse_mode="Markdown"
        )

print("Bot Started...")
bot.infinity_polling()