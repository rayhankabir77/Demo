import os
import asyncio
from datetime import datetime, timedelta
from supabase import create_client, Client
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes

# তোমার সুপাবেস ডিটেইলস
SUPABASE_URL = "https://jjevliuuyrlhhasxcdmc.supabase.co"
SUPABASE_KEY = "sb_publishable_9F4tebwyaM0mCz1RwSvIfw_cpQJqB-f" # এটা তোমার ANON KEY হওয়া উচিত
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    user_id = str(request.from_user.id)
    chat_id = request.chat.id

    # ১. সুপাবেস থেকে ইউজার চেক করা
    # ধরে নিচ্ছি তোমার টেবিলের নাম 'users' এবং কলাম 'uid' ও 'is_verified'
    response = supabase.table("users").select("is_verified").eq("uid", user_id).execute()
    user_data = response.data

    if user_data and user_data[0].get('is_verified') == True:
        # ভেরিফাইড হলে জয়েন অ্যাপ্রুভ এবং ওয়েলকাম
        await request.approve()
        await context.bot.send_message(
            chat_id=user_id, 
            text=f"অভিনন্দন {request.from_user.first_name}! আপনি ভেরিফাইড ইউজার হিসেবে গ্রুপে যুক্ত হয়েছেন।"
        )
    else:
        # ভেরিফাইড না হলে ডিক্লাইন এবং ২ ঘণ্টার জন্য ব্লক
        await request.decline()
        until_date = datetime.now() + timedelta(hours=2)
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=int(user_id), until_date=until_date)
        
        await context.bot.send_message(
            chat_id=user_id, 
            text="দুঃখিত! আপনি ভেরিফাইড নন। আপনাকে ২ ঘণ্টার জন্য ব্লক করা হয়েছে।"
        )

# মেইন ফাংশন এবং হ্যান্ডলার সেটআপ...
