import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
)
import gspread
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
load_dotenv()

# Define states for ConversationHandler
ASK_NAME, ASK_ONLINE_OFFLINE, ASK_CITY, ASK_HELP_TYPE, ASK_ADDITIONAL = range(5)

# Set up Google Sheets access
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

sheet = client.open('psycho').worksheet('Москва и МО')  # or .worksheet('SheetName')

# Start command handler
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я бот, который поможет тебе найти подходящего специалиста! Пожалуйста, уточни, как к тебе можно обращаться?")
    return ASK_NAME

# Ask online/offline
def ask_online_offline(update: Update, context: CallbackContext):
    context.user_data['name'] = update.message.text
    reply_keyboard = [['Онлайн', 'Оффлайн']]
    update.message.reply_text(
        f"Приятно познакомиться, {context.user_data['name']}! Ты хочешь общаться с психологом в онлайн или оффлайн режиме?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ASK_ONLINE_OFFLINE

# Ask for city and metro station if offline, else proceed
def ask_city_or_help_type(update: Update, context: CallbackContext):
    choice = update.message.text.lower()
    context.user_data['online_offline'] = choice
    if choice == 'оффлайн':
        update.message.reply_text("Выбери, пожалуйста, наиболее подходящую станцию метро")
        return ASK_CITY
    else:
        return ask_help_type(update, context)

# Ask for help type
def ask_help_type(update: Update, context: CallbackContext):
    if context.user_data['online_offline'] == 'оффлайн':
        context.user_data['city_and_metro'] = update.message.text
    reply_keyboard = [
        ['Психотерапия'],
        ['Психотерапия и ГВ при АД'],
        ['Психотерапия и АД']
    ]
    update.message.reply_text(
        "Какой вид психотерапии тебе предпочтителен?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ASK_HELP_TYPE

# Ask for additional preferences
def ask_additional(update: Update, context: CallbackContext):
    context.user_data['help_type'] = update.message.text
    update.message.reply_text(
        "Пожалуйста, напиши, есть ли у тебя дополнительный пожелания? Мы постараемся учесть их в будущем"
    )
    return ASK_ADDITIONAL

# Show results based on input
def show_results(update: Update, context: CallbackContext):
    context.user_data['additional'] = update.message.text
    # Now, use context.user_data to filter the specialists
    specialists = get_specialists(context.user_data)
    if specialists:
        reply_text = "Тут ты можешь найти наиболее подходящих тебе специалистов:\n"
        for spec in specialists:
            reply_text += f"\nИмя: {spec['Имя ']}\nКонтакт: {spec['Контакт']}\n"
    else:
        reply_text = "Извините, но мы не нашли подходящих вам специалистов, попробуйте повторить поиск"
    update.message.reply_text(reply_text)
    return ConversationHandler.END

# Function to get specialists based on user data
def get_specialists(user_data):
    # Fetch all records from the sheet
    records = sheet.get_all_records()
    result = []
    print(records)
    for record in records:
        # Apply filters based on user_data
        # Filter by online/offline
        if user_data['online_offline'] == 'онлайн' and record['Принимает онлайн'] != 'да':
            continue
        if user_data['online_offline'] == 'оффлайн' and record['Принимает онлайн'] == 'да' :
            continue
        # TODO: change a logic
        if user_data['online_offline'] == 'оффлайн':
            #if user_data['city_and_metro'].lower() not in record['Где принимает'].lower():# and \
            if user_data['city_and_metro'].lower() not in record['станция Метро'].lower():
                continue
        # Filter by help_type
        help_type = user_data['help_type'].lower()
        if 'Психотерапия и ГВ при АД' in help_type and record['Знает о схемах совмещения АД и ГВ'] != 'да':
            continue
        if 'Психотерапия и АД' in help_type and record['Назначает препараты'] != 'да':
            continue
        if 'психотерапия' in help_type and record['Занимается психотерапией'] != 'да':
            continue
        # Add to result if all conditions met
        result.append(record)
    return result

# Cancel handler
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Что то пошло не так, попробуй еще раз')
    return ConversationHandler.END

def main():
    API_TOKEN = os.environ["API_TOKEN"]
    updater = Updater(API_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Define conversation handler with states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, ask_online_offline)],
            ASK_ONLINE_OFFLINE: [MessageHandler(Filters.regex('^(Онлайн|Оффлайн|онлайн|оффлайн)$'), ask_city_or_help_type)],
            ASK_CITY: [MessageHandler(Filters.text & ~Filters.command, ask_help_type)],
            ASK_HELP_TYPE: [MessageHandler(Filters.text & ~Filters.command, ask_additional)],
            ASK_ADDITIONAL: [MessageHandler(Filters.text & ~Filters.command, show_results)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    print(os.getcwd())
    main()