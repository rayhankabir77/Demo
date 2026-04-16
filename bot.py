import pandas as pd
from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta, timezone
import asyncio

# --- ১. সেটিংস (আপনার তথ্য দিয়ে পরিবর্তন করুন) ---
BOT_TOKEN = "8757377007:AAECcWfmqFws2RYgZAUZwfDj3LV8M4DSJ7w" # এটি দ্রুত Revoke করে নতুন টোকেন নিন
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRXefpWbtvo6CHymAIeEA8ORZkclDUYCVq8HS1h5l4gaSz-lE20Vls63pQyfagt_uMwtxRleXY7eYc5/pub?output=csv"
GROUP_ID = -1003932929002 

# --- ২. ভেরিফিকেশন ফাংশন ---
def check_verification(user_id):
    try:
        # প্রতিবার চেক করার সময় লেটেস্ট গুগল শিট ডাটা রিড করবে
        df = pd.read_csv(SHEET_CSV_URL)
        # শিটের কলামের নাম 'User_ID' এবং ডাটা টাইপ স্ট্রিং হিসেবে চেক করা হচ্ছে
        user_row = df[df['User_ID'].astype(str) == str(user_id)]
        
        if not user_row.empty:
            # Status কলামের ভ্যালু চেক করা (বড় হাত বা ছোট হাত যাই হোক 'verified' হতে হবে)
            status = str(user_row.iloc[0]['Status']).strip().lower()
            return status == "verified"
        return False
    except Exception as e:
        print(f"[Sheet Error]: {e}")
        return False

# --- ৩. নতুন মেম্বার জয়েন হ্যান্ডেলার ---
async def on_user_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # শুধুমাত্র নির্দিষ্ট গ্রুপে কাজ করবে
    if update.effective_chat.id != GROUP_ID:
        return

    for user in update.message.new_chat_members:
        if user.is_bot: continue # বট হলে ইগনোর করবে
        
        user_id = user.id
        first_name = user.first_name

        try:
            # ক) জয়েন করার সাথে সাথে সব পারমিশন বন্ধ (Mute)
            await context.bot.restrict_chat_member(
                chat_id=GROUP_ID,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            
            # খ) ওয়েলকাম মেসেজ
            welcome_msg = await update.message.reply_text(
                f"👋 স্বাগতম {first_name}!\n\nআপনার ভেরিফিকেশন চেক করা হচ্ছে। ১০ সেকেন্ড অপেক্ষা করুন। ভেরিফাইড না হলে আপনাকে ২ ঘণ্টার জন্য ব্যান করা হবে।"
            )

            # গ) ১০ সেকেন্ড অপেক্ষা
            await asyncio.sleep(10)

            # ঘ) ভেরিফিকেশন চেক
            is_verified = check_verification(user_id)
            print(f"User {user_id} ({first_name}) verification: {is_verified}")

            if is_verified:
                # ঙ) ভেরিফাইড হলে পূর্ণ পারমিশন দেওয়া (Unmute)
                await context.bot.restrict_chat_member(
                    chat_id=GROUP_ID,
                    user_id=user_id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_audios=True,
                        can_send_documents=True,
                        can_send_photos=True,
                        can_send_videos=True,
                        can_send_video_notes=True,
                        can_send_voice_notes=True,
                        can_send_polls=True,
                        can_send_other_messages=True, # স্টিকার/জিআইএফ এর জন্য
                        can_add_web_page_previews=True,
                        can_invite_users=True
                    )
                )
                await welcome_msg.edit_text(f"✅ ভেরিফিকেশন সফল! {first_name}, এখন আপনি Raybil World-এ মেসেজ করতে পারবেন।")
            else:
                # চ) ভেরিফাইড না হলে ২ ঘণ্টার জন্য ব্যান
                await welcome_msg.edit_text(f"❌ দুঃখিত {first_name}, আপনি আমাদের ভেরিফাইড মেম্বার নন। আপনাকে ২ ঘণ্টার জন্য ব্যান করা হলো।")
                
                ban_until = datetime.now(timezone.utc) + timedelta(hours=2)
                await context.bot.ban_chat_member(
                    chat_id=GROUP_ID,
                    user_id=user_id,
                    until_date=ban_until
                )
        
        except Exception as e:
            print(f"[Join Handler Error]: {e}")

# --- ৪. মেসেজ সিকিউরিটি (বাইপাস রোধ করতে) ---
async def message_security_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return

    user_id = update.message.from_user.id
    
    # অ্যাডমিনদের জন্য এই চেক কাজ করবে না (নিজেদের সুরক্ষার জন্য)
    try:
        member = await context.bot.get_chat_member(GROUP_ID, user_id)
        if member.status in ['administrator', 'creator']:
            return
    except:
        return

    # যারা অলরেডি আছে কিন্তু ভেরিফাইড না, তাদের মেসেজ দিলেই ব্যান করবে
    if not check_verification(user_id):
        try:
            await update.message.reply_text("⚠️ আপনি ভেরিফাইড নন! আপনাকে গ্রুপ থেকে অপসারন করা হচ্ছে।")
            await context.bot.ban_chat_member(
                chat_id=GROUP_ID, 
                user_id=user_id, 
                until_date=datetime.now(timezone.utc) + timedelta(hours=2)
            )
        except Exception as e:
            print(f"[Security Check Error]: {e}")

# --- ৫. মেইন ফাংশন ---
if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    
    # নতুন মেম্বার জয়েন হ্যান্ডলার
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_user_join))
    
    # টেক্সট মেসেজ ফিল্টার (যারা ভেরিফাইড না তাদের ধরতে)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_security_check))

    print("Raybil Security Bot is Running...")
    app.run_polling()
