import asyncio
import logging
import aiohttp
from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
import traceback
from bot.database.requests import set_ad, get_all_ads
from config.loader import bot
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
file_handler = RotatingFileHandler('rozetka.log', maxBytes=5*1024*1024, backupCount=2)
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

HEADERS = {
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/58.0.3029.110",
}

BASE_URL_ROZETKA = 'https://rozetka.com.ua/ua/building_kits/c97420/producer=lego/'

async def get_html(session, url):
    async with session.get(url, headers=HEADERS) as response:
        return await response.text()

async def parse_ad(session, ad_url):
    try:
        logging.info(f"Parsing ad: {ad_url}")
        ad_html = await get_html(session, ad_url)
        ad_soup = bs(ad_html, 'html.parser')

        title_element = ad_soup.find('h1', class_='h2 bold ng-star-inserted')
        price_element = ad_soup.find('p', class_='product-price__big product-price__big-color-red')
        befdisc_element = ad_soup.find('p', class_='product-price__small ng-star-inserted')

        if not title_element or not price_element or not befdisc_element:
            logging.warning(f"Skipping ad due to missing title, price, or discount: {ad_url}")
            return

        title = title_element.text.strip()
        price = price_element.text.strip()
        befdisc = befdisc_element.text.strip()

        images = [img['src'] for img in ad_soup.find_all('img', class_='picture-container__picture')]

        price = int(re.sub(r'[^\d]', '', price))
        befdisc = int(re.sub(r'[^\d]', '', befdisc))

        pricea = (price * 100) / befdisc
        discount = round(100 - pricea)

        # logging.info(f"Parsed ad: {title}, {ad_url}, {price}, {discount}")

        if discount >= 29.5:
            if not await is_ad_in_database(title):
                await send_ad_to_channel(title, price, discount, ad_url, images)
                await asyncio.sleep(2)

    except Exception as e:
        logging.error(f"Error parsing {ad_url}: {e}")
        traceback.print_exc()

async def fetch_all_ads(session, base_url_rozetka):
    try:
        while base_url_rozetka:
            logging.info(f"Fetching ads from: {base_url_rozetka}")
            html = await get_html(session, base_url_rozetka)
            soup = bs(html, 'html.parser')
            ads = soup.find_all('a', class_='goods-tile__picture')
            tasks = [parse_ad(session, ad['href']) for ad in ads]
            await asyncio.gather(*tasks)

            next_page_element = soup.find('a', class_='pagination__direction--forward')
            if next_page_element:
                base_url_rozetka = 'https://rozetka.com.ua' + next_page_element['href']
            else:
                base_url_rozetka = None
    except Exception as e:
        logging.error(f"Error fetching base URL: {e}")
        traceback.print_exc()

async def rozetka(base_url_rozetka):
    async with aiohttp.ClientSession() as session:
        while True:
            await fetch_all_ads(session, base_url_rozetka)
            await asyncio.sleep(24*60*60)

async def is_ad_in_database(title):
    all_ads = await get_all_ads()
    if not all_ads:
        return False
    return any(title == ad.title for ad in all_ads)

async def send_ad_to_channel(title, price, discount, url, images):
    try:
        if await is_ad_in_database(title):
            # logging.info(f"Ad already in database: {title}")
            return

        chat_id = '-1002217851779'
        thread_id = '106'

        # logging.info(f"set_ad({title}, {price}, {discount}, {url}, {images})")

        set_ad(title, price, discount, url, images)
        message_ads_in_channel = f"{title}\n\nЗнижка: -{discount}%\n\nАкційна ціна: {price}₴\n\n#rozetka"
        card = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='До оголошення', url=url)
            ]
        ])

        await bot.send_photo(chat_id=chat_id, photo=images[0], caption=message_ads_in_channel, parse_mode='Markdown',
                             reply_markup=card, message_thread_id=thread_id)

    except aiogram.exceptions.TelegramRetryAfter as e:
        logging.error(f"Telegram rate limit exceeded, retrying in {e.retry_after} seconds...")
        await asyncio.sleep(e.retry_after)
        await send_ad_to_channel(title, price, discount, url, images)
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(rozetka(BASE_URL_ROZETKA))
