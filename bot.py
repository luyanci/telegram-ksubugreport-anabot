import logging
import os
import shutil
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.error import BadRequest
from dotenv import load_dotenv
load_dotenv()
import analog

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("bot")

async def send_message(chat_id: int, text: str, context: ContextTypes.DEFAULT_TYPE, update: Update):
    if update.effective_chat.type == "supergroup":
        await context.bot.send_message(chat_id=chat_id, message_thread_id=update.effective_message.message_thread_id, text=text,parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=chat_id, text=text,parse_mode='Markdown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_message(chat_id=update.effective_chat.id, text="Hello! I'm KSU Bugreport Analyzer Bot. Use /checklog to analyze your log files.", context=context, update=update)
    logger.info(f"User {update.effective_user.id} started the bot. lang: {update.effective_user.language_code}")

def process_file(file_path: str, lang_code: str) -> str:
    response = ""
    try:
        analog.unpack_tar_gz(file_path, 'extracted_files')
        basic_lines = analog.read_basic_txt('extracted_files/basic.txt')
        defconfig_lines = analog.read_defconfig_gz('extracted_files/defconfig.gz')
        module_data = analog.read_module_json('extracted_files/modules.json')
        response += "basic.txt:\n"
        response += analog.process_basic_file(basic_lines, lang_code)
        response += "defconfig.gz:\n```\n"
        for line in defconfig_lines:
            if line.split('=')[0].startswith('CONFIG_KSU'):
                response += line + "\n"
            elif line.split('=')[0].startswith('CONFIG_BBG'):
                response += line + "\n"
        
        response += "If none of this part,means no KSU or BBG modules are enabled\n```\n"
        response += "modules.json:\n"
        response += analog.process_module_json(module_data, lang_code)
    except FileNotFoundError as e:
        logger.info(f"Error processing file: {e}")
    finally:
        if os.path.exists('extracted_files'):
            shutil.rmtree('extracted_files')
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.info("Cleaned up extracted files and downloaded file.")
    return response

async def logcheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_message(chat_id=update.effective_chat.id, text="Checking logs", context=context, update=update)
    try:
        # download file
        if not update.message.reply_to_message or not update.message.reply_to_message.document:
            await send_message(chat_id=update.effective_chat.id, text="Please reply to a message containing the log file.", context=context, update=update)
            return
        file = await update.message.reply_to_message.document.get_file()
        file_path = 'downloaded_file.gz'
        await file.download_to_drive(file_path)
    except BadRequest as e:
        logger.error(f"Failed to download file: {e}")
        await send_message(chat_id=update.effective_chat.id, text=f"Failed to download the file. ({e})", context=context, update=update)
        return
    response = "Results:\n" + process_file(file_path, f"{update.effective_user.language_code if update.effective_user.language_code in analog.langs else 'en'}")
    await send_message(chat_id=update.effective_chat.id, text=response, context=context, update=update)
    
if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    logcheck_handler = CommandHandler('checklog', logcheck)
    application.add_handler(start_handler)
    application.add_handler(logcheck_handler)
    application.run_polling()