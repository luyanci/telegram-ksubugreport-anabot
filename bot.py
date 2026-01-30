import logging
import os
import shutil
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from loguru import logger
from dotenv import load_dotenv
load_dotenv()
import analog

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def logcheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Checking logs...")
    # download file
    file = await update.message.reply_to_message.document.get_file()
    file_path = 'downloaded_file.gz'
    await file.download_to_drive(file_path)
    response = "Results:\n"
    # unpack and read file
    try:
        analog.unpack_tar_gz(file_path, 'extracted_files')
        basic_lines = analog.read_basic_txt('extracted_files/basic.txt')
        defconfig_lines = analog.read_defconfig_gz('extracted_files/defconfig.gz')
        module_data = analog.read_module_json('extracted_files/modules.json')
        response = "BASIC.txt content:\n"
        for line in basic_lines:
            response += line + "\n"
        response += "\n.defconfig.gz content:\n"
        for line in defconfig_lines:
            if line.split('=')[0].startswith('CONFIG_KSU'):
                response += line + "\n"
            elif line.split('=')[0].startswith('CONFIG_BBG'):
                response += line + "\n"
        response += "If none of this part,means no KSU or BBG modules are enabled\n"
        response += "\nmodule.json content:\n"
        for module in module_data:
            if module.get('enabled') == 'true':
                response += f"Module Name: {module.get('name')}, Version: {module.get('version')}, moduleid: {module.get('id')}\n"
                response += f"  Description: {module.get('description')}\n"
            else:
                continue
    except FileNotFoundError as e:
        print(e)
        logger.info(f"Error processing file: {e}")
    finally:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        os.remove(file_path)
        shutil.rmtree('./extracted_files')
        logger.info("Successfully processed all files.")
    
        

if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    logcheck_handler = CommandHandler('checklog', logcheck)
    application.add_handler(start_handler)
    application.add_handler(logcheck_handler)
    application.run_polling()