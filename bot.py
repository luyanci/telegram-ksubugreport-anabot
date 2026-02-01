import logging
import os
import shutil
from telegram import Update,InputMediaDocument
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.error import BadRequest,NetworkError
from dotenv import load_dotenv
load_dotenv()
import analog
import locates

langs=locates.langs
MAX_FILE_SIZE= 50*1024*1024  # 50 MB

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("tgbot")

async def send_message(chat_id: int, text: str, context: ContextTypes.DEFAULT_TYPE, update: Update):
    if update.effective_chat.type == "supergroup":
        await context.bot.send_message(chat_id=chat_id, message_thread_id=update.effective_message.message_thread_id, text=text,parse_mode='html')
    else:
        await context.bot.send_message(chat_id=chat_id, text=text,parse_mode='html')

async def send_document_grp(chat_id: int, document_grp: list[InputMediaDocument], context: ContextTypes.DEFAULT_TYPE, update: Update):
    if update.effective_chat.type == "supergroup":
        await context.bot.send_media_group(chat_id=chat_id, message_thread_id=update.effective_message.message_thread_id, media=document_grp)
    else:
        await context.bot.send_media_group(chat_id=chat_id, media=document_grp)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = update.effective_user.language_code if update.effective_user.language_code in analog.langs else 'en'
    await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['start_message'], context=context, update=update)
    logger.debug(f"User {update.effective_user.id} started the bot. lang: {update.effective_user.language_code}")

def process_file(file_path: str, lang_code: str,timestamp) -> str:
    response = ""
    try:
        analog.unpack_tar_gz(file_path, f'extracted_files_{timestamp}')
        basic_lines = analog.read_basic_txt(f'extracted_files_{timestamp}/basic.txt')
        defconfig_lines = analog.read_defconfig_gz(f'extracted_files_{timestamp}/defconfig.gz')
        module_data = analog.read_module_json(f'extracted_files_{timestamp}/modules.json')
        response += "basic.txt:\n"
        response += analog.process_basic_file(basic_lines, lang_code)
        response += "defconfig.gz:\n"
        response += analog.process_defconfig_file(defconfig_lines, lang_code)
        response += f"{langs[lang_code]['modules_info']}\n"
        response += analog.process_module_json(module_data, lang_code)
    except FileNotFoundError as e:
        logger.info(f"Error processing file: {e}")
    return response

async def send_need_files(timestamp: int, lang_code: str, context: ContextTypes.DEFAULT_TYPE, update: Update):
    need_files = ["adb_tree.txt","adb_details.txt","pstore.tar.gz","dmesg.txt","logcat.txt","oplus.tar.gz","bootlog.tar.gz"]
    can_send_files = []
    missing_files = []
    broken_files = []
    too_large_files = []
    file_grp = []
    content=""
    for file in need_files:
        if not os.path.exists(f'extracted_files_{timestamp}/{file}'):
            missing_files.append(file)
            continue
        elif os.path.getsize(f'extracted_files_{timestamp}/{file}') <= 1000:
            broken_files.append(file)
            continue
        elif os.path.getsize(f'extracted_files_{timestamp}/{file}') > MAX_FILE_SIZE:
            too_large_files.append(file)
            continue
        else:
            can_send_files.append(file)
            continue
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
                    file_grp.append(InputMediaDocument(media=open(f'extracted_files_{timestamp}/{file}', "rb"),caption=f"File: {file}\n{content}"))
                else:
                    file_grp.append(InputMediaDocument(media=open(f'extracted_files_{timestamp}/{file}', "rb"),caption=f"File: {file}"))
            await send_document_grp(chat_id=update.effective_chat.id,document_grp=file_grp, context=context, update=update)
    except NetworkError as e:
        await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['network_error'].format(error=e), context=context, update=update)
        return

async def logcheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatid = update.effective_chat.id
    timestamp = int(update.message.date.timestamp())
    lang_code = update.effective_user.language_code if update.effective_user.language_code in analog.langs else 'en'
    await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['logcheck_message'], context=context, update=update)
    try:
        # download file
        if not update.message.reply_to_message or not update.message.reply_to_message.document:
            await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['no_file_error'], context=context, update=update)
            return
        file = await update.message.reply_to_message.document.get_file()
        file_path = f'downloaded_file_{chatid}_{timestamp}.gz'
        await file.download_to_drive(file_path)
    except BadRequest as e:
        logger.error(f"Failed to download file: {e}")
        await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['download_error'].format(error=f"TG API Returned:{e}"), context=context, update=update)
        return
    response = "Results:\n" + process_file(file_path, f"{update.effective_user.language_code if update.effective_user.language_code in analog.langs else 'en'}",timestamp)
    await send_message(chat_id=update.effective_chat.id, text=response, context=context, update=update)
    await send_need_files(timestamp, lang_code, context, update)
    # clean up
    if os.path.exists('extracted_files_'+str(timestamp)):
        shutil.rmtree('extracted_files_'+str(timestamp))
    if os.path.exists(file_path):
        os.remove(file_path)
    logger.info("Cleaned up extracted files and downloaded file.")
    
if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    logcheck_handler = CommandHandler('checklog', logcheck)
    application.add_handler(start_handler)
    application.add_handler(logcheck_handler)
    application.run_polling()