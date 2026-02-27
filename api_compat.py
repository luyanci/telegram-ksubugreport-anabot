from telegram import Update,InputMediaDocument,Message
from telegram.ext import ContextTypes

MB = 1024*1024

async def send_message(chat_id: int, text: str, context: ContextTypes.DEFAULT_TYPE, update: Update):
    if update.effective_chat.type == "supergroup":
        ret = await context.bot.send_message(chat_id=chat_id, message_thread_id=update.effective_message.message_thread_id, text=text,parse_mode='html')
    else:
        ret = await context.bot.send_message(chat_id=chat_id, text=text,parse_mode='html')
    return ret

async def send_document_grp(chat_id: int, document_grp: list[InputMediaDocument], context: ContextTypes.DEFAULT_TYPE, update: Update):
    if update.effective_chat.type == "supergroup":
        ret = await context.bot.send_media_group(chat_id=chat_id, message_thread_id=update.effective_message.message_thread_id, media=document_grp)
    else:
        ret = await context.bot.send_media_group(chat_id=chat_id, media=document_grp)
    return ret
        
async def edit_message_text(message, text: str):
    return await message.edit_text(text=text,parse_mode='html')

