import os,httpx
import logging
import asyncio
from time import sleep
from telegram import Update,InputMediaDocument,Message
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

API_ID = 21724
API_HASH = "3e0cb5efcd52300aec5994fdfc5bdc16"

from locates import langs
timeout=httpx.Timeout(10.0,read=60.0,write=60.0,connect=10.0,pool=None)

logger = logging.getLogger(__name__)

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

MB = 1024*1024

async def streamed_download_file(file, file_path: str,message: Message, context: ContextTypes.DEFAULT_TYPE, update: Update):
    lang_code = update.effective_user.language_code if update.effective_user.language_code in langs else 'en'
    link = file._get_encoded_url()
    last_update_time = 0
    async with httpx.AsyncClient(timeout=timeout) as client:
        cli = client.build_request("GET", link)
        r = await client.send(cli, stream=True)
        r.raise_for_status()
        size = int(r.headers.get("Content-Length", 0))
        downloaded_size=0
        await edit_message_text(message,f"{langs[lang_code]['logcheck_message']} \n{downloaded_size/MB:.2f} / {size/MB:.2f} MB (0.00%)")
        with open(file_path,'wb') as f:
            async for chunk in r.aiter_bytes(1024*512):
                f.write(chunk)
                downloaded_size += len(chunk)
                now = asyncio.get_event_loop().time()
                if now - last_update_time >= 1:
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
                    await edit_message_text(message,f"{langs[lang_code]['logcheck_message']} \n{downloaded_size/MB:.2f} / {size/MB:.2f} MB ({downloaded_size/size*100:.2f}%)")
                    last_update_time = now
        await edit_message_text(message,f"{langs[lang_code]['logcheck_message']} \n{downloaded_size/MB:.2f} / {size/MB:.2f} MB (100.00%)!")
        sleep(3)
        return
    
async def start_local_bot_api():
    logger.info("Starting Telegram Bot API")
    import subprocess
    global process
    process = subprocess.Popen(["./telegram-bot-api-binary",
                                f"--api-id={API_ID}",
                                f"--api-hash={API_HASH}",
                                "--local",
                                "-p",
                                "18081"])
    

async def wait_for_local_bot_api(BOT_TOKEN: str = os.getenv('BOT_TOKEN')):
    #await start_local_bot_api()
    logger.info("Waiting for Telegram Bot API to start...")
    async with httpx.AsyncClient(timeout=timeout) as client:
        for count in range(30):
            try:
                response = await client.get(f"http://127.0.0.1:18081/bot{BOT_TOKEN}/getMe")
                if response.status_code < 500:
                    logger.info("Telegram Bot API started")
                    break
            except Exception as e:
                logger.error(f"Error while waiting for Telegram Bot API: {str(e)}")
                logger.info("Still wait..." + str(count))
                raise e
                
        else:
            process.kill()
            logger.error("Failed to start Telegram Bot API")
            exit(1)
        return 