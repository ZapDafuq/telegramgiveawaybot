import os
import json
import random
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from functools import wraps

# --- Flask Keep-Alive ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    # Corrected line: Reads the PORT environment variable to work on Replit
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- Bot Config ---
# Your Telegram Bot Token directly in the script
TOKEN = '8378912980:AAFNFS3m02CcSPKcOHfCIgAQiYklD0URF08'
CHANNEL_USERNAME = '@JulianNine'

participants = set()
user_info = {}
giveaway_active = False
giveaway_message_id = None
giveaway_end_time = None

AUTHORIZED_USERS = {6544556777}

def restricted(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in AUTHORIZED_USERS:
            update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        return func(update, context, *args, **kwargs)
    return wrapped

DATA_FILE = 'giveaway_data.json'

def save_state():
    data = {
        'participants': list(participants),
        'user_info': user_info,
        'giveaway_active': giveaway_active,
        'giveaway_message_id': giveaway_message_id,
        'giveaway_end_time': giveaway_end_time.isoformat() if giveaway_end_time else None,
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def load_state():
    global participants, user_info, giveaway_active, giveaway_message_id, giveaway_end_time
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            participants.clear()
            participants.update(data.get('participants', []))
            user_info.clear()
            user_info.update(data.get('user_info', {}))
            giveaway_active = data.get('giveaway_active', False)
            giveaway_message_id = data.get('giveaway_message_id', None)
            end_time_str = data.get('giveaway_end_time', None)
            if end_time_str:
                giveaway_end_time = datetime.fromisoformat(end_time_str)
                if giveaway_end_time.tzinfo is None:
                    giveaway_end_time = pytz.timezone('Asia/Yangon').localize(giveaway_end_time)
            else:
                giveaway_end_time = None
    else:
        participants.clear()
        user_info.clear()
        giveaway_active = False
        giveaway_message_id = None
        giveaway_end_time = None

def get_remaining_time():
    if giveaway_active and giveaway_end_time:
        now = datetime.now(pytz.timezone('Asia/Yangon'))
        delta = giveaway_end_time - now
        if delta.total_seconds() > 0:
            return delta
    return None

@restricted
def start(update: Update, context: CallbackContext):
    update.message.reply_text("🎉 Welcome! Use /giveaway to start a giveaway.")

@restricted
def giveaway(update: Update, context: CallbackContext):
    global giveaway_active, participants, user_info, giveaway_message_id, giveaway_end_time

    if giveaway_active:
        update.message.reply_text("⚠️ A giveaway is already running!")
        return

    giveaway_active = True
    participants.clear()
    user_info.clear()

    keyboard = [[InlineKeyboardButton("🎉 J9 ရဲ့ Giveaway မှာပါဝင်လိုက်ပါ", callback_data='join')]]
    markup = InlineKeyboardMarkup(keyboard)

    giveaway_end_time = None

    sent_msg = context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=(
            "🎁 **J9 ရဲ့ Giveaway လာပါပြီ!🥳🥳**\n\n"
            "အောက်ကခလုတ်လေးကိုနှိပ်ပြီးပါဝင်နိုင်ပါတယ်!👇\n"
            "⏰ Winner များကိုဘယ်အချိန်ရွေးချယ်သွားမလဲဆိုတာထပ်ပြောပေးပါမယ်ဗျ\n"
            "🤑🤑🤑 Winner ၂၀ ယောက်အတွက် Unit 1000 စီ!"
        ),
        reply_markup=markup,
        parse_mode="Markdown"
    )

    giveaway_message_id = sent_msg.message_id
    save_state()

    update.message.reply_text("✅ Giveaway started! Please use /fixendtime to set the end date and time.")

def join_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user

    global giveaway_active
    if not giveaway_active:
        query.answer("❌ Giveaway ended. You can no longer join.")
        return

    if user.id not in participants:
        participants.add(user.id)
        name = user.username if user.username else f"{user.first_name} {user.last_name or ''}".strip()
        user_info[user.id] = name
        save_state()
        query.answer("🎉 J9 ရဲ့ Giveaway မှာသင်ပါဝင်သွားပါပြီ!")
        try:
            context.bot.send_message(chat_id=user.id, text="✅ သင်ကံကောင်းပါစေလို့ J9 မှဆုတောင်းပေးလိုက်ပါတယ်🍀\nငွေသွင်းငွေထုတ်ပြုလုပ်ရန် - @JulianN9ne")
        except Exception as e:
            print(f"Failed to send PM to user {user.id}: {e}")
    else:
        try:
            query.answer("✅ သင်ကံကောင်းပါစေလို့ J9 မှဆုတောင်းပေးလိုက်ပါတယ်🍀")
        except:
            pass

@restricted
def participants_command(update: Update, context: CallbackContext):
    update.message.reply_text(f"👥 Total participants: {len(participants)}")

@restricted
def cancel_giveaway(update: Update, context: CallbackContext):
    global giveaway_active, participants, user_info, giveaway_message_id, giveaway_end_time
    if giveaway_active:
        giveaway_active = False
        participants.clear()
        user_info.clear()
        giveaway_message_id = None
        giveaway_end_time = None
        save_state()
        update.message.reply_text("❌ Giveaway canceled.")
    else:
        update.message.reply_text("⚠️ No active giveaway to cancel.")

@restricted
def status(update: Update, context: CallbackContext):
    if giveaway_active:
        remaining = get_remaining_time()
        if remaining:
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            update.message.reply_text(f"🎉 Giveaway is active!\nTime remaining: {hours}h {minutes}m {seconds}s\nParticipants: {len(participants)}")
        else:
            update.message.reply_text("⚠️ Giveaway end time passed but giveaway still active! Please end it manually.")
    else:
        update.message.reply_text("No active giveaway right now.")

@restricted
def export_participants(update: Update, context: CallbackContext):
    if not participants:
        update.message.reply_text("No participants yet.")
        return

    lines = []
    for user_id in participants:
        name = user_info.get(user_id, "Unknown")
        if name and not name.startswith('@') and ' ' not in name:
            name = '@' + name
        lines.append(f"{user_id} - {name}")

    export_text = "\n".join(lines)
    if len(export_text) > 4000:
        update.message.reply_text("Too many participants to send as message.")
        with open("participants.txt", "w", encoding="utf-8") as f:
            f.write(export_text)
        with open("participants.txt", "rb") as f:
            update.message.reply_document(f)
        os.remove("participants.txt")
    else:
        update.message.reply_text(f"Participants:\n{export_text}")

@restricted
def fixendtime(update: Update, context: CallbackContext):
    global giveaway_end_time, giveaway_active

    if not giveaway_active:
        update.message.reply_text("⚠️ No active giveaway to update end time for.")
        return

    if len(context.args) != 2:
        update.message.reply_text("❗️Usage: /fixendtime YYYY-MM-DD HH:MM (24h)\nExample: /fixendtime 2025-08-02 20:00")
        return

    date_str, time_str = context.args[0], context.args[1]

    try:
        new_end = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        mmt = pytz.timezone('Asia/Yangon')
        new_end = mmt.localize(new_end)
    except Exception as e:
        update.message.reply_text(f"❌ Invalid date/time format.\nError: {e}")
        return

    now = datetime.now(pytz.timezone('Asia/Yangon'))
    if new_end <= now:
        update.message.reply_text("❌ The new end time must be in the future.")
        return

    giveaway_end_time = new_end
    save_state()

    jobs = context.job_queue.get_jobs_by_name('end_giveaway')
    for job in jobs:
        job.schedule_removal()

    delay = (giveaway_end_time - now).total_seconds()
    context.job_queue.run_once(pick_winner, delay, name='end_giveaway')

    update.message.reply_text(f"✅ Giveaway end time updated to {giveaway_end_time.strftime('%Y-%m-%d %H:%M %Z')}")

def pick_winner(context: CallbackContext):
    global giveaway_active, participants, user_info, giveaway_message_id, giveaway_end_time

    if not giveaway_active:
        return

    if not participants:
        context.bot.send_message(chat_id=CHANNEL_USERNAME, text="😢 No one joined the giveaway.")
    else:
        winners = random.sample(list(participants), min(20, len(participants)))
        winners_text = '\n'.join([f"🏆 [{user_info.get(uid, 'User')}](tg://user?id={uid})" for uid in winners])
        context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=f"🎉 **Giveaway Ended!**\n\n{winners_text}\n\nCongratulations!\nWinner များ DM ကိုလာခဲ့ပေးပါဗျ❤️\nငွေသွင်းငွေထုတ်ပြုလုပ်ရန် - @JulianN9ne",
            parse_mode="Markdown"
        )

        if giveaway_message_id:
            try:
                context.bot.edit_message_text(
                    chat_id=CHANNEL_USERNAME,
                    message_id=giveaway_message_id,
                    text="🎉 Giveaway ended! Thanks for participating!\nငွေသွင်းငွေထုတ်ပြုလုပ်ရန် - @JulianN9ne",
                    reply_markup=None
                )
            except Exception as e:
                print(f"Failed to edit giveaway message: {e}")

    giveaway_active = False
    participants.clear()
    user_info.clear()
    giveaway_message_id = None
    giveaway_end_time = None
    save_state()

def main():
    load_state()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    commands = [
        BotCommand("start", "Welcome message"),
        BotCommand("giveaway", "Start a new giveaway"),
        BotCommand("participants", "Check the number of participants"),
        BotCommand("status", "Show current giveaway status"),
        BotCommand("fixendtime", "Set/update the giveaway end time"),
        BotCommand("exportparticipants", "Export list of participants"),
        BotCommand("cancelgiveaway", "Cancel the current giveaway"),
    ]
    updater.bot.set_my_commands(commands)

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('giveaway', giveaway))
    dp.add_handler(CommandHandler('participants', participants_command))
    dp.add_handler(CommandHandler('cancelgiveaway', cancel_giveaway))
    dp.add_handler(CommandHandler('status', status))
    dp.add_handler(CommandHandler('exportparticipants', export_participants))
    dp.add_handler(CommandHandler('fixendtime', fixendtime))
    dp.add_handler(CallbackQueryHandler(join_callback))

    if giveaway_active and giveaway_end_time:
        now = datetime.now(pytz.timezone('Asia/Yangon'))
        delay = (giveaway_end_time - now).total_seconds()
        if delay <= 0:
            pick_winner(context=type('DummyContext', (), {'bot': updater.bot})())
        else:
            updater.job_queue.run_once(pick_winner, delay, name='end_giveaway')

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    keep_alive()
    main()