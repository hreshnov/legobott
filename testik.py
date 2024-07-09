# test.py
from bot.parse.rozetkasel import parse_rozetka
from src.automation.rozetka import Rozetka
import asyncio
from pyvirtualdisplay import Display

async def test():
    link = 'https://rozetka.com.ua/ua/building_kits/c97420/producer=lego/'
    rozetka = Rozetka()
    page_source = rozetka.get_the_link(link)
    if not page_source:
        print("Не удалось получить содержимое страницы")
        return
    await parse_rozetka(page_source)

async def scheduled_parsing_rozetka():
    with Display(visible=False, size=(1920, 1080)):
        while True:
            await test()
            print('Ждем 10 мин')
            await asyncio.sleep(600)

if __name__ == '__main__':
    asyncio.run(test())
