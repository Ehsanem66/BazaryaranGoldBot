import os
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from config import BOT_TOKEN, CHANNEL_ID, INSTAGRAM_ID
from gold_price import calculate_price
from database import AdDatabase

# ادمین‌ها (آیدی عددی)
ADMIN_IDS = [106546961]  # آیدی عددی ادمین رو بذار

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running!')

def run_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()

def fa_to_en(text):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    for p, e in zip(persian_digits, english_digits):
        text = text.replace(p, e)
    return text

PHOTO, NAME, PURITY, WEIGHT, PROFIT_PERCENT, LABOR_PERCENT, CONDITION, PHONE = range(8)

db = AdDatabase()
user_data_temp = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_temp[user_id] = {}
    
    welcome_text = (
        "🌟 *به ربات طلافروشی بازاریاران خوش آمدید!*\n\n"
        "📸 لطفاً عکس طلای خود را ارسال کنید:\n\n"
        "📌 _برای راهنما /help را بزنید_"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    return PHOTO

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *راهنمای ربات بازاریاران*\n\n"
        "🏷 این ربات برای ثبت آگهی طلا در کانال @bazaryaranby طراحی شده است.\n\n"
        "📋 *مراحل ثبت آگهی:*\n"
        "1️⃣ ارسال عکس طلا\n"
        "2️⃣ وارد کردن نام (مثلاً: گردنبند قلب)\n"
        "3️⃣ انتخاب عیار (۱۴ تا ۲۴)\n"
        "4️⃣ وارد کردن وزن به گرم (مثلاً: 5.2)\n"
        "5️⃣ وارد کردن درصد سود فروشنده (مثلاً: 15)\n"
        "6️⃣ وارد کردن درصد اجرت ساخت (مثلاً: 10)\n"
        "7️⃣ انتخاب وضعیت (نو یا دست دوم)\n\n"
        "💰 *مشاهده قیمت لحظه‌ای:*\n"
        "بعد از ثبت آگهی، مشتری با دکمه «مشاهده قیمت لحظه‌ای» قیمت را می‌بیند.\n\n"
        "📞 *شماره تماس:* 09127136697\n\n"
        "🆔 کانال: @bazaryaranby\n"
        "🤖 ربات: @BazaryaranBot\n\n"
        "📌 *دستورات:*\n"
        "/start - ثبت آگهی جدید\n"
        "/help - راهنما\n"
        "/cancel - لغو عملیات\n"
        "/about - درباره ما\n"
        "/support - پشتیبانی"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "🏢 *بازاریاران*\n\n"
        "✨ اولین ربات تخصصی طلافروشی\n"
        "📱 ثبت آگهی رایگان در کانال\n"
        "💰 محاسبه قیمت لحظه‌ای طلا\n"
        "🔗 ارتباط مستقیم خریدار و فروشنده\n\n"
        "📞 تماس: 09127136697\n"
        "🆔 کانال: @bazaryaranby\n"
        "📱 اینستاگرام: @bazaryaran\n\n"
        "🤖 ربات: @BazaryaranBot"
    )
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *پشتیبانی بازاریاران*\n\n"
        "📱 تماس: 09127136697\n"
        "🆔 کانال: @bazaryaranby\n"
        "🤖 ربات: @BazaryaranBot\n\n"
        "💬 جهت ارتباط با پشتیبانی به آیدی زیر پیام دهید:",
        parse_mode='Markdown'
    )

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_temp[user_id]['photo_id'] = update.message.photo[-1].file_id
    await update.message.reply_text("📝 نام طلا را وارد کنید (مثلاً: گردنبند قلب):")
    return NAME

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_temp[user_id]['name'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("۱۴ عیار", callback_data="purity_14"),
         InlineKeyboardButton("۱۸ عیار", callback_data="purity_18")],
        [InlineKeyboardButton("۲۱ عیار", callback_data="purity_21"),
         InlineKeyboardButton("۲۲ عیار", callback_data="purity_22")],
        [InlineKeyboardButton("۲۴ عیار", callback_data="purity_24")]
    ]
    await update.message.reply_text("📊 عیار طلا را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return PURITY

async def purity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    purity = int(query.data.split('_')[1])
    user_data_temp[user_id]['purity'] = purity
    await query.edit_message_text(f"✅ عیار انتخابی: {purity}\n\n⚖ وزن طلا را به گرم وارد کنید (مثلاً: 5.2):")
    return WEIGHT

async def weight_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        text = fa_to_en(update.message.text)
        weight = float(text)
        if weight <= 0:
            raise ValueError
        user_data_temp[user_id]['weight'] = weight
        await update.message.reply_text("📈 درصد سود فروشنده را وارد کنید (فقط عدد، مثلاً: 15):")
        return PROFIT_PERCENT
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید:\nمثال: 5.2 یا ۵.۲")
        return WEIGHT

async def profit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        text = fa_to_en(update.message.text)
        profit = float(text)
        if profit < 0:
            raise ValueError
        user_data_temp[user_id]['profit_percent'] = profit
        await update.message.reply_text("🔧 درصد اجرت ساخت را وارد کنید (فقط عدد، مثلاً: 10):")
        return LABOR_PERCENT
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید:\nمثال: 15 یا ۱۵")
        return PROFIT_PERCENT

async def labor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        text = fa_to_en(update.message.text)
        labor = float(text)
        if labor < 0:
            raise ValueError
        user_data_temp[user_id]['labor_percent'] = labor
        keyboard = [
            [InlineKeyboardButton("نو ✨", callback_data="condition_new"),
             InlineKeyboardButton("دست دوم 🔄", callback_data="condition_used")]
        ]
        await update.message.reply_text("📦 وضعیت طلا:", reply_markup=InlineKeyboardMarkup(keyboard))
        return CONDITION
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید:\nمثال: 10 یا ۱۰")
        return LABOR_PERCENT

async def condition_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    is_new = query.data == "condition_new"
    user_data_temp[user_id]['is_new'] = is_new
    condition_text = "نو ✨" if is_new else "دست دوم 🔄"
    
    phone = "09127136697"
    user_data_temp[user_id]['phone'] = phone
    user_data = user_data_temp[user_id]
    
    ad_id = f"{user_id}_{datetime.now().timestamp()}"
    ad_data = {
        'user_id': user_id,
        **user_data,
        'price_info': None,
        'sold': False,
        'created_at': datetime.now().isoformat()
    }
    
    db.add_ad(ad_id, ad_data)
    
    ad_text = (
        f"🏷 {user_data['name']}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📊 عیار: {user_data['purity']}\n"
        f"⚖ وزن: {user_data['weight']} گرم\n"
        f"📦 وضعیت: {condition_text}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📞 تماس: {phone}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🆔 کانال: {CHANNEL_ID}\n"
        f"\n💰 برای مشاهده قیمت لحظه‌ای، دکمه زیر را بزنید:"
    )
    
    # دکمه فروخته شد فقط برای کاربر ثبت‌کننده (و ادمین)
    keyboard = [
        [InlineKeyboardButton("💰 مشاهده قیمت لحظه‌ای", callback_data=f"price_{ad_id}")],
        [InlineKeyboardButton("❌ فروخته شد", callback_data=f"sold_{ad_id}")]
    ]
    
    await query.message.reply_photo(
        photo=user_data['photo_id'],
        caption=ad_text + "\n\n✅ آگهی شما با موفقیت ثبت شد!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # ارسال به کانال (بدون دکمه فروخته شد)
    try:
        channel_keyboard = [
            [InlineKeyboardButton("💰 مشاهده قیمت لحظه‌ای", callback_data=f"price_{ad_id}")],
            [InlineKeyboardButton("❌ فروخته شد", callback_data=f"sold_{ad_id}")]
        ]
        channel_text = ad_text + "\n\n📱 جهت ثبت آگهی رایگان: @BazaryaranBot"
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=user_data['photo_id'],
            caption=channel_text,
            reply_markup=InlineKeyboardMarkup(channel_keyboard)
        )
    except Exception as e:
        print(f"Channel error: {e}")
        await query.message.reply_text("⚠️ آگهی ثبت شد اما در کانال قرار نگرفت.")
    
    del user_data_temp[user_id]
    return ConversationHandler.END

async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

async def ad_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    
    if not (data.startswith("price_") or data.startswith("sold_")):
        return
    
    parts = data.split('_', 1)
    action = parts[0]
    ad_id = parts[1] if len(parts) > 1 else ""
    
    if action == "price":
        await query.answer()
        ad_data = db.get_ad(ad_id)
        if ad_data and not ad_data.get('sold'):
            price_info = calculate_price(
                ad_data['weight'],
                ad_data['purity'],
                ad_data['profit_percent'],
                ad_data['labor_percent'],
                ad_data['is_new']
            )
            
            condition = "نو ✨" if ad_data['is_new'] else "دست دوم 🔄"
            price_text = (
                f"💎 قیمت لحظه‌ای {ad_data['name']}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📊 عیار: {ad_data['purity']}\n"
                f"⚖ وزن: {ad_data['weight']} گرم\n"
                f"📦 وضعیت: {condition}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"💰 قیمت پایه هر گرم: {price_info['base_price_18k']:,.0f} تومان\n"
                f"💎 قیمت هر گرم: {price_info['gram_price']:,.0f} تومان\n"
                f"📈 قیمت خام: {price_info['raw_price']:,.0f} تومان\n"
                f"💹 سود ({ad_data['profit_percent']}%): {price_info['profit']:,.0f} تومان\n"
                f"🔧 اجرت ({ad_data['labor_percent']}%): {price_info['labor']:,.0f} تومان\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"💫 قیمت نهایی: {price_info['final_price']:,.0f} تومان\n\n"
                f"📞 جهت خرید: {ad_data['phone']}"
            )
            
            await query.answer(price_text, show_alert=True)
    
    elif action == "sold":
        ad_data = db.get_ad(ad_id)
        if ad_data:
            # فقط صاحب آگهی یا ادمین می‌تونه بزنه
            if user_id == ad_data['user_id'] or user_id in ADMIN_IDS:
                await query.answer()
                db.mark_as_sold(ad_id)
                original_caption = query.message.caption or ""
                sold_caption = f"❌ فروخته شد ❌\n\n{original_caption}"
                await query.edit_message_caption(caption=sold_caption)
            else:
                await query.answer("❌ فقط فروشنده یا ادمین میتواند این دکمه را بزند.", show_alert=True)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data_temp:
        del user_data_temp[user_id]
    await update.message.reply_text("❌ عملیات لغو شد.\n/start - ثبت آگهی جدید\n/help - راهنما")
    return ConversationHandler.END

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # دستورات
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('about', about_command))
    application.add_handler(CommandHandler('support', support_command))
    
    # دکمه‌ها
    application.add_handler(CallbackQueryHandler(ad_button_handler, pattern='^(price_|sold_)'))
    
    # مکالمه
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, photo_handler)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            PURITY: [CallbackQueryHandler(purity_handler, pattern='^purity_')],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_handler)],
            PROFIT_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, profit_handler)],
            LABOR_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, labor_handler)],
            CONDITION: [CallbackQueryHandler(condition_handler, pattern='^condition_')],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    print("🌟 Bazaryaran GoldBot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    time.sleep(2)
    main()
