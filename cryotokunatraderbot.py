import kuna
import pandas as pd
import time
import random
import asyncio
import logging
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher, executor
from aiogram import types


client = kuna.KunaAPI(public_key='', private_key='')

logging.basicConfig(level=logging.INFO)
bot = Bot('put your telegram token')

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class OrderFood(StatesGroup):
    money = State()


def limitprice(name):
    try:
        return client.tickers(name)[0][7]
    except ValueError:
        return limitprice(name)

def getuahbalance():
    try:
        return client.auth_r_wallets()[0][2]
    except ValueError:
        return getuahbalance()

def getbtcbalance():
    try:
        return client.auth_r_wallets()[1][2]
    except ValueError:
        return getbtcbalance()

async def check():
    try:
        if len(client.auth_r_orders("btcuah")) == 0:
            return 0
        else:
            await asyncio.sleep(5)
            await check()
    except ValueError:
        await check()

async def strategy(message):
    try:
        uah = 50
        await check()
        price = limitprice("btcuah")
        minuspercpice = price - price * 0.01
        plusprice = price + price * 0.01
        amount = uah / price
        amount = round(amount, 6)
        client.auth_w_order_submit("btcuah", "limit", amount, minuspercpice)
        await bot.send_message(message.chat.id, 'Purchase order was placed at the price: ' + str(minuspercpice))
        await check()
        client.auth_w_order_submit("btcuah", "limit", -amount, plusprice)
        await bot.send_message(message.chat.id,'The sale order was placed at the price: ' + str(plusprice))
    except ValueError:
       await strategy(message)

@dp.message_handler(commands="start")
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ['Price of btc', 'Start strategy', 'Check balance']
    keyboard.add(*buttons)
    await bot.send_message(message.chat.id, "Вітаємо, {0.id}!\nБот готовий до роботи".format(message.from_user), parse_mode='html',reply_markup=keyboard)


@dp.message_handler(text='Price of btc')
async def binabot(message):
    await bot.send_message(message.chat.id, "The price is: " + str(limitprice('btcuah')))

@dp.message_handler(text='Check balance')
async def binabot(message):
    await bot.send_message(message.chat.id,"UAH: " + str(getuahbalance()) +'\n'+ "BTC: " + str(getbtcbalance()))

@dp.message_handler(text='Start strategy')
async def binabot(message):

    await strategy(message)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

