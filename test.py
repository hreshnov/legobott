# LOCAL[ PARSING ]
from bot.parse.cmftest import *

# LOCAL[ AUTOMATION ]
from src.automation.comfy import Comfy

import asyncio

from pyvirtualdisplay import Display


async def test():
    link = 'https://comfy.ua/lego/'
    comfy = Comfy()
    page_source = comfy.get_the_link(link)
    if not page_source:
        return
    await parse_comfy(page_source, comfy)

async def scheduled_parsing_comfy():
    with Display(visible=False, size=(1920, 1080)):
        while True:
            await test()
            print('Ждем 10 мин')
            await asyncio.sleep(600)


# if __name__ == '__main__':
#     asyncio.run(test())
