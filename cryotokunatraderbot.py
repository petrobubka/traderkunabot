import kuna
import urllib.error
import asyncio
import logging
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher, executor
from aiogram import types


client = kuna.KunaAPI(public_key='', private_key='')

logging.basicConfig(level=logging.INFO)
bot = Bot('put your telegram token')

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class NumberStatesGroup(StatesGroup):
    number = State()
def limitprice(name):
    try:
        return client.tickers(name)[0][7]
    except ValueError:
        return limitprice(name)

def meanprice(name):
    try:
        return round((client.tickers(name)[0][9] + client.tickers(name)[0][10])/2)
    except ValueError:
        return meanprice(name)

def minusprice(name):
    try:
        return client.tickers(name)[0][1]
    except ValueError:
        return minusprice(name)

def plusprice(name):
    try:
        return client.tickers(name)[0][3]
    except ValueError:
        return plusprice(name)

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
            await asyncio.sleep(60)
            await check()
    except ValueError:
        await check()
    except urllib.error.URLError:
        await asyncio.sleep(360)
        await check()

async def strategy(message, uah):
    try:
        await check()
        price = limitprice("btcuah")
        purchase = minusprice("btcuah")
        sell = plusprice("btcuah")
        amount = uah / price
        amount = round(amount, 6)
        client.auth_w_order_submit("btcuah", "limit", amount, purchase)
        await bot.send_message(message.chat.id, 'Purchase order was placed at the price: ' + str(purchase))
        await bot.send_message(message.chat.id, '1')
        await check()
        client.auth_w_order_submit("btcuah", "limit", -amount, sell)
        await bot.send_message(message.chat.id, '2')
        await bot.send_message(message.chat.id,'The sale order was placed at the price: ' + str(sell))
        await check()
        await strategy(message, uah)
    except ValueError:
       await strategy(message, uah)

@dp.message_handler(commands="start")
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ['Price of btc', 'Start strategy', 'Check balance']
    keyboard.add(*buttons)
    await bot.send_message(message.chat.id, "Hello, {0.id}!\nBot is ready to work".format(message.from_user), parse_mode='html',reply_markup=keyboard)


@dp.message_handler(text='Price of btc')
async def findprice(message):
    await bot.send_message(message.chat.id, "The price is: " + str(limitprice('btcuah')))

@dp.message_handler(text='Check balance')
async def getbalances(message):
    await bot.send_message(message.chat.id,"UAH: " + str(getuahbalance()) +'\n'+ "BTC: " + str(getbtcbalance()))


@dp.message_handler(text='Start strategy')
async def startstrategy(message):
    await message.reply("To begin enter an amount of money")
    await NumberStatesGroup.number.set()

@dp.message_handler(state=NumberStatesGroup.number)
async def load_number(message, state: FSMContext):
    async with state.proxy() as data:
        data['number'] = message.text
    await state.finish()
    await strategy(message, int(data['number']))

if __name__ == "__main__":
    executor.start_polling(dp, timeout=20000, skip_updates=True)

