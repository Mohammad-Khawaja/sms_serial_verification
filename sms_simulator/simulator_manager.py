from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram import Update

import aiohttp
from multiprocessing import Process

from config import TOKEN, BASE_URL

async def launch_announcement(*args):
	print("SMS emulator launched.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
	print("پیام دریافت شد.")
	text = update.message.text
	user_id = update.message.chat.id
	data = {"message": text, "from": user_id}
	url = "http://127.0.0.1:5000/v1/process"
	async with aiohttp.ClientSession() as session:
		async with session.post(url, data=data) as response:
			result = await response.json()

def start():
	print("process created")
	app = Application.builder().token(TOKEN).base_url(BASE_URL).post_init(launch_announcement).build()
	app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, message_handler))
	app.run_polling()

def run_sms_simulator():
	pr = Process(target=start, daemon=True)
	pr.start()