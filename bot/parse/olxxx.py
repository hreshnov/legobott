import aiohttp
import logging
from bs4 import BeautifulSoup
import asyncio
import traceback

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.requests import set_adolx, get_all_adsolx
from config.loader import bot

base_url_olx = "https://www.olx.ua/detskiy-mir/igrushki/"

logging.basicConfig(
    filename='olx.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

async def fetch(session, url, params=None):
    async with session.get(url, params=params) as response:
        return await response.text()

async def parse_olx(base_url_olx):
    search_keywords = ["lego hobbit", "лего hobbit", "лего хоббит", "лего лотр", "lego lotr", "lego lord of the ring"]
    async with aiohttp.ClientSession() as session:
        for keyword in search_keywords:
            params = {
                "search[description]": 1,
                "q": keyword
            }
            logging.info(f"Searching for: {keyword}")
            response_text = await fetch(session, base_url_olx, params)

            if response_text:
                # logging.info(f"Successfully fetched the page for keyword: {keyword}")
                soup = BeautifulSoup(response_text, 'html.parser')
                ads = soup.find_all('a', class_='css-z3gu2d')

                if ads:
                    # logging.info(f"Found {len(ads)} ads for keyword: {keyword}")
                    for ad in ads:
                        ad_url = ad['href']
                        if not ad_url.startswith('https://www.olx.ua'):
                            ad_url = 'https://www.olx.ua' + ad_url

                        ad_response_text = await fetch(session, ad_url)
                        ad_soup = BeautifulSoup(ad_response_text, 'html.parser')

                        try:
                            title_div = ad_soup.find('div', {'data-cy': 'ad_title'})
                            title_da = title_div.find('h4')
                            title = title_da.text.strip()
                            # logging.info(f"Title found: {title}")
                        except AttributeError:
                            title = "No title"
                            logging.warning("Title not found")

                        try:
                            price_div = ad_soup.find('div', {'data-testid': 'ad-price-container'})
                            price_da = price_div.find('h3')
                            price = price_da.text.strip()
                            # logging.info(f"Price found: {price}")
                        except AttributeError:
                            price = "No price"
                            logging.warning("Price not found")

                        try:
                            description_div = ad_soup.find('div', {'data-cy': 'ad_description'})
                            description_da = description_div.find('div')
                            description = description_da.text.strip()
                            # logging.info(f"Description found: {description}")
                        except AttributeError:
                            description = "No description"
                            logging.warning("Description not found")

                        try:
                            images = [img['src'] for img in ad_soup.find_all('img', class_='css-1bmvjcs')]
                            if images:
                                logging.info(f"Images found: {images[0]}")
                            else:
                                logging.warning("No images found")
                        except (AttributeError, TypeError):
                            images = ["No image"]
                            logging.warning("Images not found")

                        if any(kw.lower() in title.lower() for kw in search_keywords):
                            if not await is_ad_in_database(title):
                                await send_ad_to_channel(title, price, description, ad_url, images)
                                await asyncio.sleep(2)
                else:
                    logging.info(f"No ads found for keyword: {keyword}")
            else:
                logging.warning(f"Failed to fetch the page for keyword: {keyword}")

        # logging.info('ПЕРВЫЙ КРУГ ЗАКОНЧЕН!!!!!!!!!')

async def is_ad_in_database(url):
    all_ads = await get_all_adsolx()
    if not all_ads:
        return False
    return any(url == ad.url for ad in all_ads)

async def send_ad_to_channel(title, price, description, url, images):
    try:
        if await is_ad_in_database(url):
            # logging.info(f"Ad already in database: {title}")
            return

        chat_id = '-1002172066040'

        set_adolx(title, price, description, url, images)
        message_ads_in_channel = f"OLX\n\n{title}\n\nОпис: {description}\n\nЦіна: {price}₴"
        card = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='До оголошення', url=url)
            ]
        ])

        # logging.info(f"Sending ad to channel: {title}")

        await bot.send_photo(chat_id=chat_id, photo=images[0], caption=message_ads_in_channel, parse_mode='Markdown',
                             reply_markup=card)
    except Exception:
        traceback.print_exc()

async def scheduled_parsing():
    while True:
        await parse_olx(base_url_olx)
        logging.info('Ждем 10 мин')
        await asyncio.sleep(300)

