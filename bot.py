import pandas as pd
from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
import asyncio

# সেটিংস
BOT_TOKEN = "8711531840:AAFYTlYEt0ji7R2LqKfp89DWagJ2mJlr0Bg"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRXefpWbtvo6CHymAIeEA8ORZkclDUYCVq8HS1h5l4gaSz-lE20Vls63pQyfagt_uMwtxRleXY7eYc5/pub?output=csv"
GROUP_ID = -1003934746677

def check_verification(user_id):
    try:
        # প্রতিবার লেটেস্ট ডাটা রিড করা
        df = pd.read_csv(SHEET_CSV_URL)
        df.columns = df.columns.str.strip()
        user_row = df[df['User_ID'].astype(str).str.strip() == str(user_id).strip()]
        
        if not user_row.empty:
            status = str(user_row.iloc[0]['Status']).strip().lower()
            return status == "verified"
        return False
    except Exception as e:
        print(f"Sheet Error: {e}")
        return False

async def on_user_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GROUP_ID:
        return

    for user in update.message.new_chat_members:
        if user.is_bot: continue
        
        user_id = user.id
        first_name = user.first_name

        # ১. প্রথমেই মিউট করা
        try:
            await context.bot.restrict_chat_member(
                chat_id=GROUP_ID,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False)
            )
        except Exception as e:
            print(f"Mute Error: {e}")

        welcome_msg = await update.message.reply_text(f"👋 {first_name}, ভেরিফিকেশন চেক চলছে... ১০ সেকেন্ড অপেক্ষা করুন।")

        # ২. ১০ সেকেন্ড ওয়েট
        await asyncio.sleep(10)

        # ৩. ভেরিফিকেশন রেজাল্ট অনুযায়ী একশন
        if check_verification(user_id):
            try:
                # সব পারমিশন একদম ক্লিয়ার করে দেওয়া
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
                        can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )
                await welcome_msg.edit_text(f"✅ ভেরিফিকেশন সফল! {first_name}, এখন আপনি Raybil World-এ মেসেজ করতে পারবেন।")
                print(f"Verified & Unmuted: {first_name} ({user_id})")
            except Exception as e:
                print(f"Unmute Error: {e}")
                await welcome_msg.edit_text("⚠️ ভেরিফিকেশন সফল হলেও পারমিশন দিতে সমস্যা হচ্ছে। অ্যাডমিনকে জানান।")
        else:
            await welcome_msg.edit_text(f"❌ দুঃখিত {first_name}, আপনি ভেরিফাইড নন। ২ ঘণ্টা পর চেষ্টা করুন।")
            try:
                await context.bot.ban_chat_member(
                    chat_id=GROUP_ID,
                    user_id=user_id,
                    until_date=datetime.now() + timedelta(hours=2)
                )
                print(f"Banned: {first_name} ({user_id})")
            except Exception as e:
                print(f"Ban Error: {e}")

if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_user_join))
    print("Raybil Security Bot is running with Fixes...")
    app.run_polling()
