from telegram import Update
import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, CallbackContext


psycho, drugs, ad_gv = range(3)

df = pd.read_csv("src/data/data.csv", delimiter=",")

tokenizer = {"Yes": "Yes", "No": "No"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[
        InlineKeyboardButton("Да", callback_data="да"),
        InlineKeyboardButton("Нет", callback_data="нет"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Давай подберем тебе подходящего специалиста! Скажи, пожалуйста, тебе важно что человек занимается психотерапией? ", reply_markup=reply_markup)
    return psycho

async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt same text & keyboard as `start` does but not as new message"""
    keyboard = [[
        InlineKeyboardButton("Да", callback_data="да"),
        InlineKeyboardButton("Нет", callback_data="нет"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Давай подберем тебе подходящего специалиста! Скажи, пожалуйста, тебе важно что человек занимается психотерапией? ", reply_markup=reply_markup)
    return psycho


async def first_response(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['psycho'] = query.data

    keyboard = [[
        InlineKeyboardButton("Да", callback_data="да"),
        InlineKeyboardButton("Нет", callback_data="нет"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text='Нужен ли тебе врач с возможностью назначать препараты?', reply_markup=reply_markup)

    return drugs

async def second_response(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['drugs'] = query.data

    keyboard = [[
        InlineKeyboardButton("Да", callback_data="да"),
        InlineKeyboardButton("Нет", callback_data="нет"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text='Важно ли тебе осведомленность врача про комбинацию АД и ГВ?', reply_markup=reply_markup)

    return ad_gv

async def third_response(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['ad_gv'] = query.data
    filtered_df = df[(df['Занимается психотерапией'] == context.user_data['psycho']) & (df['Назначает препараты'] == context.user_data['drugs']) &  (df['Знает о схемах совмещения АД и ГВ'] == context.user_data['ad_gv'])]
    
    if len(filtered_df) > 0:
        dict_filtered_df = filtered_df[['Специалист', 'Контакт']].to_dict('records') # Converts filtered DataFrame to list of dictionaries
        formatted_text = '\n'.join(str(item) for item in dict_filtered_df)
        await query.edit_message_text(text="Here's the filtered data:\n\n" + formatted_text)
    else:
        await query.edit_message_text(text='К сожалению мы не смогли найти подходящих врачей')
    
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token("6729317928:AAFh9_RCX6B-QK2KH3DeRJKQZGwnoQAxUjo").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            psycho: [CallbackQueryHandler(first_response)],
            drugs: [CallbackQueryHandler(second_response)],
            ad_gv: [CallbackQueryHandler(third_response)]
        },
        fallbacks=[CommandHandler("start", start)],
    )
    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == '__main__':
    main()