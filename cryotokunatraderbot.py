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
bot = Bot('')

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class BTCStatesGroup(StatesGroup):
    number = State()

class USDTStatesGroup(StatesGroup):
    number = State()

def limitprice(name):
    try:
        return client.tickers(name)[0][7]
    except ValueError:
        return limitprice(name)


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

def getusdtbalance():
    try:
        return client.auth_r_wallets()[3][3]
    except ValueError:
        return getbtcbalance()

def makeoffer(name, amount, price):
    try:
        return client.auth_w_order_submit(name, "limit", amount, price)
    except ValueError:
        return makeoffer(name, amount, price)

async def check(name):
    try:
        if len(client.auth_r_orders(name)) == 0:
            return 0
        else:
            await asyncio.sleep(60)
            await check(name)
    except ValueError:
        await check(name)
    except urllib.error.URLError:
        await asyncio.sleep(360)
        await check(name)

async def strategy(name, message, uah):
    try:
        await check(name)
        price = limitprice(name)
        purchase = minusprice(name)
        sell = plusprice(name)
        amount = uah / price
        amount = round(amount, 6)
        makeoffer(name, amount, purchase)
        await bot.send_message(message.chat.id, 'Purchase order ({0}) was placed at the price: {1}'.format(name, str(purchase)))
        await check(name)
        makeoffer(name, -amount, sell)
        await bot.send_message(message.chat.id,'The sale order ({0}) was placed at the price: {1}'.format(name, str(sell)))
        await check(name)
        await strategy(name, message, uah)
    except ValueError:
       await strategy(name, message, uah)

@dp.message_handler(commands="start")
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ['List prices', 'Start strategy(BTC)', 'Start strategy(USDT)', 'Check balance']
    keyboard.add(*buttons)
    await bot.send_message(message.chat.id, "Hello, {0.id}!\nBot is ready to work".format(message.from_user), parse_mode='html',reply_markup=keyboard)


@dp.message_handler(text='List prices')
async def findprice(message):
    await bot.send_message(message.chat.id, "The price of BTC is: {0}\nThe price of USDT is: {1}".format(str(limitprice('btcuah')), str(limitprice('usdtuah'))))

@dp.message_handler(text='Check balance')
async def getbalances(message):
    getusdtbalance()
    await bot.send_message(message.chat.id,"UAH: {0}\nBTC: {1}\nUSDT: {2}".format(str(getuahbalance()), str(round(getbtcbalance(), 5)), str(round(getusdtbalance(), 5))))


@dp.message_handler(text='Start strategy(BTC)')
async def startstrategy(message):
    await message.reply("To start BTC strategy enter an amount of money")
    await BTCStatesGroup.number.set()

@dp.message_handler(state=BTCStatesGroup.number)
async def load_number(message, state: FSMContext):
    async with state.proxy() as data:
        data['number'] = message.text
    await state.finish()
    await strategy('btcuah', message, int(data['number']))

@dp.message_handler(text='Start strategy(USDT)')
async def startstrategy(message):
    await message.reply("To start USDT strategy enter an amount of money")
    await USDTStatesGroup.number.set()

@dp.message_handler(state=USDTStatesGroup.number)
async def load_number(message, state: FSMContext):
    async with state.proxy() as data:
        data['number'] = message.text
    await state.finish()
    await strategy('usdtuah', message, int(data['number']))

if __name__ == "__main__":
    executor.start_polling(dp, timeout=20000000, skip_updates=True)

