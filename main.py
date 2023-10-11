# -*- coding: utf-8 -*-
from config import *
import logging
import requests
import re
import openai
from aiogram import Bot, Dispatcher, executor, types
import asyncio
from telebot.async_telebot import AsyncTeleBot

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# Dictionary to store user history
user_history = {}

openai.api_key = OUR_API_KEY
openai.api_base = 'https://api.openai.com/v1'

async def ai(prompt):
    user_id = prompt.chat.id
    history = user_history.get(user_id, [])
    history.append(prompt.text)
    user_history[user_id] = history

    # Keep only the last 3-4 messages to avoid exceeding the token limit
    if len(history) > 3:
        history = history[-3:]

    messages = [{"role": "system",
                 "content": 'Тебя зовут chatGPT, и ты знаешь все.'}]
    for i in range(len(history)):
        if i % 2 == 0:
            messages.append({"role": "user", "content": history[i]})
        else:
            messages.append({"role": "system", "content": history[i]})

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=messages,
            max_tokens=1200,
            temperature=0.5,
            timeout=15
        )

        response = completion.choices[0].message.content
        history.append(response)
        user_history[user_id] = history
        return response
    except:
        return None


@dp.message_handler()
async def handle_message(message: types.Message):
    await bot.send_chat_action(message.chat.id, 'typing')
    answer = await ai(message)
    if answer is not None:
        username = message.from_user.first_name
        response = f"{username}: {answer}"

        # Convert code and commands to Markdown
        response = re.sub(r'```python(.+?)```', r'```python\n\1\n```', response, flags=re.DOTALL)

        await bot.send_message(message.chat.id, response, parse_mode='Markdown')
    else:
        await bot.send_message(message.chat.id, 'Я не знаю, что ответить на это...')


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я чат-бот, готовый ответить на твои вопросы. Попробуй задать мне что-нибудь!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)