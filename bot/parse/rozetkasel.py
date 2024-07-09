# rozetka.py
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import cloudscraper
import asyncio
import traceback

import aiogram
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config.loader import bot
from bot.database.requests import set_ad, get_all_ads
from src.automation.rozetka import Rozetka

scraper = cloudscraper.create_scraper(
    delay=10,
    browser={'browser': 'firefox'},
    disableCloudflareV1=True,
)

HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/58.0.3029.110",
    'Accept': "text/html",
    'Accept-Language': 'en-US,en;q=0.5'
}

base_url = "https://rozetka.com.ua/ua/building_kits/c97420/producer=lego/"


async def fetch_page(url):
    response = scraper.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.text
    return None


async def parse_rozetka(page_source: str):
    rozetka = Rozetka()
    visited_urls = set()
    while page_source:
        soup = BeautifulSoup(page_source, 'html.parser')
        ads_divs = soup.find_all('a', class_='goods-tile__picture')
        print(f"Найдено {len(ads_divs)} карточек товаров.")

        if not ads_divs:
            print("Не удалось найти элементы с заданным классом.")
            break

        for ads_div in ads_divs:
            ad_url = ads_div['href']
            print(f"Открываем объявление: {ad_url}")
            ad_page_source = rozetka.open_ad(ad_url)
            if ad_page_source:
                await parse_ad(ad_page_source, ad_url)
            else:
                print(f"Не удалось открыть объявление: {ad_url}")

        next_page_url = rozetka.get_next_page_url(page_source)
        if next_page_url and next_page_url not in visited_urls:
            visited_urls.add(next_page_url)
            page_source = await fetch_page(next_page_url)
        else:
            break

async def parse_ad(ad_page_source, ad_url):
    print("Парсинг объявления")
    try:
        ad_soup = BeautifulSoup(ad_page_source, 'html.parser')

        title_element = ad_soup.find('h1', class_='h2 bold ng-star-inserted')
        price_element = ad_soup.find('p', class_='product-price__big product-price__big-color-red')
        # dis_element = ad_soup.find('p', class_='product-price__small ng-star-inserted')
        images = [img['src'] for img in ad_soup.find_all('img', class_='picture-container__picture')]
        befdisc_element = ad_soup.find('p', class_='product-price__small ng-star-inserted')

        if title_element:
            title = title_element.text.strip()
        else:
            title = "Нет заголовка"

        if price_element:
            price = price_element.text.replace('\n', '').replace(' ', '')
        else:
            price = "Нет цены"

        # if dis_element:
        #     discount_str = dis_element.text.strip()
        #     discount = int(discount_str.replace('%', ''))
        # else:
        #     discount = "Нет скидки"

        if images:
            images = images
        else:
            images = "Нет фото"

        if befdisc_element:
            befdisc = befdisc_element.text.strip()
        else:
            befdisc = "Нет скидки"


        price = int(re.sub(r'[^\d]', '', price))
        befdisc = int(re.sub(r'[^\d]', '', befdisc))

        pricea = (price * 100) / befdisc
        discount = round(100 - pricea)

        if discount == -53:
            print(f"Объявление пропущено из-за скидки -53%: {title}")
            return

        if discount <= -29.5:
            if not await is_ad_in_database(title):
                await send_ad_to_channel(title, price, discount, ad_url, images)
                await asyncio.sleep(2)

        print(f"Roz: {title}, {price} {discount} {images}")

    except Exception as e:
        print(f"Произошла ошибка при анализе объявления: {str(e)}")
        traceback.print_exc()

async def is_ad_in_database(title):
    all_ads = await get_all_ads()
    if not all_ads:
        return False
    return any(title == ad.title for ad in all_ads)

async def send_ad_to_channel(title, price, discount, url, images):
    try:
        if await is_ad_in_database(title):
            print("Объявление уже в базе данных")
            return

        chat_id = '-1002217851779/2'
        thread_id = '2'

        print(f"set_ad({title}, {price}, {discount}, {url}, {images})")

        set_ad(title, price, discount, url, images)
        message_ads_in_channel = f"Comfy\n\n{title}\n\nЗнижка: {discount}%\n\nАкційна ціна: {price}"
        card = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='До оголошення', url=url)
            ]
        ])

        await bot.send_photo(chat_id=chat_id, photo=images[0], caption=message_ads_in_channel, parse_mode='Markdown',
                             reply_markup=card, message_thread_id=thread_id)

    except aiogram.exceptions.TelegramRetryAfter as e:
        print(f"Telegram rate limit exceeded, retrying in {e.retry_after} seconds...")
        await asyncio.sleep(e.retry_after)
        await send_ad_to_channel(title, price, discount, url, images)
    except Exception:
        traceback.print_exc()
