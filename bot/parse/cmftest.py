import re
from bs4 import BeautifulSoup
import cloudscraper
import asyncio
import logging
import traceback

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.loader import bot
from bot.database.requests import set_ad, get_all_ads

scraper = cloudscraper.create_scraper(
    delay=10,
    browser={'browser': 'firefox'},
    disableCloudflareV1=True,
)

logging.basicConfig(
    filename='comfy.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/58.0.3029.110",
    'Accept': "text/html",
    'Accept-Language': 'en-US,en;q=0.5'
}

base_url = "https://comfy.ua/lego/"



async def fetch_page(url):
    response = scraper.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.text
    return None

async def parse_comfy(page_source: str, comfy):
    visited_urls = set()
    while page_source:
        soup = BeautifulSoup(page_source, 'html.parser')
        ads_divs = soup.find_all('div', class_='products-list-item')
        # logging.info(f"Найдено {len(ads_divs)} карточек товаров.")

        if not ads_divs:
            logging.error("Не удалось найти элементы с заданным классом.")
            break

        for ads_div in ads_divs:
            ad = ads_div.find('a', href=True)
            if not ad:
                logging.error("Не удалось найти ссылку внутри карточки товара.")
                continue

            ad_url = ad['href']
            ad_page_source = comfy.open_ad(ad_url)
            if ad_page_source:
                await parse_ad(ad_page_source, ad_url)

        next_page_url = comfy.get_next_page_url(page_source)
        if next_page_url and next_page_url not in visited_urls:
            visited_urls.add(next_page_url)
            page_source = await fetch_page(next_page_url)
        else:
            break

async def parse_ad(ad_page_source, ad_url):
    # logging.info("Парсинг объявления")
    try:
        ad_soup = BeautifulSoup(ad_page_source, 'html.parser')

        title_element = ad_soup.find('h1', class_='gen-tab__name')
        price_element = ad_soup.find('div', class_='price__current')
        dis_element = ad_soup.find('span', class_='price__percent-discount')
        images = [img['src'] for img in ad_soup.find_all('img', class_='fit contain')]

        if title_element:
            title = title_element.text.strip()
        else:
            title = "Нет заголовка"

        if price_element:
            price = price_element.text.replace('\n', '').replace(' ', '')
        else:
            price = "Нет цены"

        if dis_element:
            discount_str = dis_element.text.strip()
            discount = int(discount_str.replace('%', ''))
        else:
            discount = "Нет скидки"

        if images:
            images = images
        else:
            images = "Нет фото"

        if discount == -53:
            logging.info(f"Объявление пропущено из-за скидки -53%: {title}")
            return

        if discount <= -29.5:
            if not await is_ad_in_database(title):
                await send_ad_to_channel(title, price, discount, ad_url, images)
                await asyncio.sleep(2)

        # logging.info(f"Комфи: {title}, {price} {discount} {images}")

    except Exception as e:
        logging.error(f"Произошла ошибка при анализе объявления: {str(e)}")
        traceback.print_exc()

async def is_ad_in_database(title):
    all_ads = await get_all_ads()
    if not all_ads:
        return False
    return any(title == ad.title for ad in all_ads)

async def send_ad_to_channel(title, price, discount, url, images):
    try:
        if await is_ad_in_database(title):
            # logging.info("Объявление уже в базе данных")
            return

        chat_id = '-1002217851779'
        thread_id = '106'

        set_ad(title, price, discount, url, images)
        message_ads_in_channel = f"{title}\n\nЗнижка: {discount}%\n\nАкційна ціна: {price}\n\n#comfy"
        card = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='До оголошення', url=url)
            ]
        ])

        # logging.info(f"Sending ad to channel: {title}")

        await bot.send_photo(chat_id=chat_id, photo=images[0], caption=message_ads_in_channel, parse_mode='Markdown',
                             reply_markup=card, message_thread_id=thread_id)
    except aiogram.exceptions.TelegramRetryAfter as e:
        logging.error(f"Telegram rate limit exceeded, retrying in {e.retry_after} seconds...")
        await asyncio.sleep(e.retry_after)
        await send_ad_to_channel(title, price, discount, url, images)
    except Exception:
        traceback.print_exc()

