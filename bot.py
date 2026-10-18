import logging
import os
import shutil
import asyncio
import html
from html.parser import HTMLParser
from telegram import Update,InputMediaDocument
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.error import BadRequest,NetworkError
from dotenv import load_dotenv
load_dotenv()
from botapi import send_message, send_document_grp, edit_message_text,kill_local_bot_api, wait_for_local_bot_api
import analog
from locates import langs


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("tgbot")


class _TelegramMessageSplitter(HTMLParser):
    _void_tags = {"br", "hr", "img"}

    def __init__(self, limit: int):
        super().__init__(convert_charrefs=False)
        self.limit = limit
        self.chunks = []
        self.current = []
        self.open_tags = []
        self.visible_length = 0

    def _flush(self):
        self.chunks.append(
            "".join(self.current + [closing for _, _, closing in reversed(self.open_tags)])
        )
        self.current = [opening for _, opening, _ in self.open_tags]
        self.visible_length = 0

    def _append_text(self, source: str, visible_text: str):
        visible_length = sum(2 if ord(char) > 0xFFFF else 1 for char in visible_text)
        if self.visible_length and self.visible_length + visible_length > self.limit:
            self._flush()
        self.current.append(source)
        self.visible_length += visible_length

    def handle_starttag(self, tag, attrs):
        opening = self.get_starttag_text()
        self.current.append(opening)
        if tag not in self._void_tags:
            self.open_tags.append((tag, opening, f"</{tag}>"))

    def handle_startendtag(self, tag, attrs):
        self.current.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.current.append(f"</{tag}>")
        if self.open_tags and self.open_tags[-1][0] == tag:
            self.open_tags.pop()

    def handle_data(self, data):
        for char in data:
            self._append_text(char, char)

    def handle_entityref(self, name):
        source = f"&{name};"
        self._append_text(source, html.unescape(source))

    def handle_charref(self, name):
        source = f"&#{name};"
        self._append_text(source, html.unescape(source))


def split_telegram_message(text: str, limit: int = 4096) -> list[str]:
    splitter = _TelegramMessageSplitter(limit)
    splitter.feed(text)
    splitter.close()
    if splitter.visible_length or not splitter.chunks:
        splitter.chunks.append(
            "".join(splitter.current + [closing for _, _, closing in reversed(splitter.open_tags)])
        )
    return splitter.chunks


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
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT)
            await send_document_grp(chat_id=update.effective_chat.id,document_grp=file_grp, context=context, update=update)
    except BadRequest as e:
        logger.error(f"Failed to send files: {e}")
        await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['file_processing_error'].format(error=str(e)), context=context, update=update)
        return
    except NetworkError as e:
        # This error often occurs when api take too long time to send files, so ignore it...
        logger.warning(f"Network error while sending files: {e}")
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
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        file = await update.message.reply_to_message.document.get_file(read_timeout=100, write_timeout=100,connect_timeout=100)
        file_path = f'downloaded_file_{chatid}_{timestamp}.gz'
        file_url = file._get_encoded_url().replace("%3A",":")
        logger.debug(f"Downloading file from {file_url}")
        await file.download_to_drive(file_path)
        response = "Results:\n" + analog.process_file(file_path, f"{update.effective_user.language_code if update.effective_user.language_code in analog.langs else 'en'}",timestamp)
        response_chunks = split_telegram_message(response)
        if len(response_chunks) > 1:
            await edit_message_text(msg, response_chunks[0])
            for chunk in response_chunks[1:]:
                await send_message(chat_id=update.effective_chat.id, text=chunk, context=context, update=update)
        else:
            await edit_message_text(msg, response)
        await send_need_files(timestamp, lang_code, context, update)
    except BadRequest as e:
        logger.error(f"Failed to download file: {e}")
        await send_message(chat_id=update.effective_chat.id, text=langs[lang_code]['download_error'].format(error=str(e)), context=context, update=update)
        await msg.delete()
        return
    except UnboundLocalError as e:
        await edit_message_text(msg, langs[lang_code]['noroot_error'])
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
        if os.path.exists(file_url):
            # delete file which is api downloaded
            os.remove(file_url)
        logger.info("{}_{}: Cleaned up extracted files and downloaded file.".format(chatid,timestamp))
    
if __name__ == '__main__':
    asyncio.run(wait_for_local_bot_api())
    
    application = ApplicationBuilder() \
        .base_url('http://127.0.0.1:18081/bot') \
        .base_file_url('http://127.0.0.1:18081/file/bot') \
        .token(os.getenv('BOT_TOKEN')) \
        .build()
    start_handler = CommandHandler('start', start)
    logcheck_handler = CommandHandler('checklog', logcheck)
    application.add_handler(start_handler)
    application.add_handler(logcheck_handler)
    try:
        application.run_polling()
    finally:
        kill_local_bot_api()
        logger.info("Bot stopped.")
        