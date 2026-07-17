async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone = "09127136697"
    
    user_data_temp[user_id]['phone'] = phone
    user_data = user_data_temp[user_id]
    
    # محاسبه قیمت
    price_info = calculate_price(
        user_data['weight'],
        user_data['purity'],
        user_data['profit_percent'],
        user_data['labor_percent'],
        user_data['is_new']
    )
    
    # ساخت آگهی
    ad_id = f"{user_id}_{datetime.now().timestamp()}"
    ad_data = {
        'user_id': user_id,
        **user_data,
        'price_info': price_info,
        'sold': False,
        'created_at': datetime.now().isoformat()
    }
    
    db.add_ad(ad_id, ad_data)
    
    condition = "نو ✨" if user_data['is_new'] else "دست دوم 🔄"
    ad_text = (
        f"🏷 {user_data['name']}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📊 عیار: {user_data['purity']}\n"
        f"⚖ وزن: {user_data['weight']} گرم\n"
        f"📦 وضعیت: {condition}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 قیمت پایه هر گرم (۱۸ عیار): {price_info['base_price_18k']:,.0f} تومان\n"
        f"💎 قیمت هر گرم با عیار {user_data['purity']}: {price_info['gram_price']:,.0f} تومان\n"
        f"📈 قیمت خام: {price_info['raw_price']:,.0f} تومان\n"
        f"💹 سود ({user_data['profit_percent']}%): {price_info['profit']:,.0f} تومان\n"
        f"🔧 اجرت ساخت ({user_data['labor_percent']}%): {price_info['labor']:,.0f} تومان\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💫 قیمت نهایی: {price_info['final_price']:,.0f} تومان\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📞 تماس: {phone}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🆔 کانال: {CHANNEL_ID}"
    )
    
    keyboard = [
        [InlineKeyboardButton("📱 تماس با فروشنده", url=f"tel:{phone}")],
        [InlineKeyboardButton("🔄 بروزرسانی قیمت", callback_data=f"update_{ad_id}")],
        [InlineKeyboardButton("❌ فروخته شد", callback_data=f"sold_{ad_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=user_data['photo_id'],
        caption=ad_text,
        reply_markup=reply_markup
    )
    
    del user_data_temp[user_id]
    return ConversationHandler.END
