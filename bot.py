import logging
import os
import shutil
from telegram import Update,InputMediaDocument
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.error import BadRequest,NetworkError
from dotenv import load_dotenv
load_dotenv()
from api_compat import send_message, send_document_grp, edit_message_text,streamed_download_file
import analog
from locates import langs

MAX_FILE_SIZE= 50*1024*1024  # 50 MB

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("tgbot")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = update.effective_user.language_code if update.effective_user.language_code in langs else 'en'
    await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['start_message'], context=context, update=update)
    logger.debug(f"User {update.effective_user.id} started the bot. lang: {update.effective_user.language_code}")

async def send_need_files(timestamp: int, lang_code: str, context: ContextTypes.DEFAULT_TYPE, update: Update):
    file_grp = []
    content=""
    can_send_files, missing_files, broken_files, too_large_files = analog.process_need_send_file(timestamp)

    try:
        if len(missing_files) != 0:
            content+=langs[lang_code]['missing_files'].format(files=", ".join(missing_files))+"\n"
        if len(broken_files) != 0:
            content+=langs[lang_code]['broken_files'].format(files=", ".join(broken_files))+"\n"
        if len(too_large_files) != 0:
            content+=langs[lang_code]['too_large_files'].format(files=", ".join(too_large_files))+"\n"
        if len(can_send_files) != 0:
            for file in can_send_files:
                if file == can_send_files[-1]:
                    file_grp.append(InputMediaDocument(media=open(f'extracted_files_{timestamp}/{file}', "rb"),caption=f"File: {file}\n\n{content}"))
                else:
                    file_grp.append(InputMediaDocument(media=open(f'extracted_files_{timestamp}/{file}', "rb"),caption=f"File: {file}"))
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_document")
            await send_document_grp(chat_id=update.effective_chat.id,document_grp=file_grp, context=context, update=update)
    except BadRequest as e:
        logger.error(f"Failed to send files: {e}")
        await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['file_processing_error'].format(error=str(e)), context=context, update=update)
        return
    except NetworkError as e:
        logger.error(f"Network error while sending files: {e}")
        return

async def logcheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = ""
    chatid = update.effective_chat.id
    timestamp = int(update.message.date.timestamp())
    lang_code = update.effective_user.language_code if update.effective_user.language_code in langs else 'en'
    msg = await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['logcheck_message'], context=context, update=update)
    try:
        # download file
        if not update.message.reply_to_message or not update.message.reply_to_message.document:
            await edit_message_text(msg, langs[lang_code]['no_file_error'])
            return
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        file = await update.message.reply_to_message.document.get_file()
        file_path = f'downloaded_file_{chatid}_{timestamp}.gz'
        await streamed_download_file(file, file_path, msg, context, update)

        response = "Results:\n" + analog.process_file(file_path, f"{update.effective_user.language_code if update.effective_user.language_code in analog.langs else 'en'}",timestamp)
        await edit_message_text(msg, response)
        await send_need_files(timestamp, lang_code, context, update)
    except BadRequest as e:
        logger.error(f"Failed to download file: {e}")
        await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['download_error'].format(error=str(e)), context=context, update=update)
        await msg.delete()
        return
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return
    finally:
        # clean up
        if os.path.exists('extracted_files_'+str(timestamp)):
            shutil.rmtree('extracted_files_'+str(timestamp))
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.info("{}_{}: Cleaned up extracted files and downloaded file.".format(chatid,timestamp))
    
if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    logcheck_handler = CommandHandler('checklog', logcheck)
    application.add_handler(start_handler)
    application.add_handler(logcheck_handler)
    application.run_polling()