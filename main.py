import asyncio
import logging
import multiprocessing


from config.loader import dp, bot
from logging import basicConfig

from bot.parse.rozetka import rozetka, BASE_URL_ROZETKA
from bot.parse.olxxx import scheduled_parsing
# from bot.parse.cmftest import scheduled_parsing_comfy

from test import *

from bot.handlers.user import welcome


logging.basicConfig(level=logging.INFO)

async def async_worker(func, *args):
    try:
        await func(*args)
    except asyncio.CancelledError:
        pass

def run_async_worker(func, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_worker(func, *args))


async def run_bot():
    dp.include_routers(welcome.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def main():
    processes = [
        multiprocessing.Process(target=run_async_worker, args=(rozetka, BASE_URL_ROZETKA)),
        multiprocessing.Process(target=run_async_worker, args=(scheduled_parsing,)),
        multiprocessing.Process(target=run_async_worker, args=(scheduled_parsing_comfy,)),
        multiprocessing.Process(target=run_async_worker, args=(run_bot,))
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join()

if __name__ == '__main__':
    print('Bot started')
    main()
    logging.info('Bot started')
