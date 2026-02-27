import os,httpx
import asyncio
from time import sleep
from telegram import Update,InputMediaDocument,Message
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from locates import langs
timeout=httpx.Timeout(10.0)

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
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT)
                    await edit_message_text(message,f"{langs[lang_code]['logcheck_message']} \n{downloaded_size/MB:.2f} / {size/MB:.2f} MB ({downloaded_size/size*100:.2f}%)")
                    last_update_time = now
            sleep(1)
            return