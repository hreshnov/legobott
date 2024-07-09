# autoroz.py
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from .base import Base

class Rozetka(Base):
    def __init__(self):
        super().__init__()

    def get_the_link(self, url: str, attempts: int = 3) -> str:
        if attempts < 1:
            return ""
        print(f"Открываем страницу: {url}")
        self.driver.get(url)
        sleep(self.sleep_time())
        try:
            self.wait(20).until(ec.presence_of_element_located((
                By.CLASS_NAME, 'catalog-grid'
            )))
            print(f"Успешно загрузили страницу: {url}")
        except (TimeoutException, WebDriverException) as e:
            print(f"Ошибка при загрузке страницы: {url}. Попытка {3 - attempts + 1}. Ошибка: {str(e)}")
            return self.get_the_link(url, attempts - 1)
        return self.driver.page_source

    def open_ad(self, ad_url: str, attempts: int = 3) -> str:
        if attempts < 1:
            print(f"Не удалось открыть объявление после {3 - attempts} попыток: {ad_url}")
            return ""
        print(f"Открываем объявление: {ad_url}")
        self.driver.get(ad_url)
        sleep(self.sleep_time())
        try:
            self.wait(20).until(ec.presence_of_element_located((
                By.CLASS_NAME, 'h2'
            )))
            print(f"Успешно открыл объявление: {ad_url}")
            return self.driver.page_source
        except (TimeoutException, WebDriverException) as e:
            print(f"Ошибка при открытии объявления: {ad_url}. Попытка {3 - attempts + 1}. Ошибка: {str(e)}")
            return self.open_ad(ad_url, attempts - 1)

    def get_next_page_url(self, current_page_source):
        soup = BeautifulSoup(current_page_source, 'html.parser')
        pagination_links = soup.find_all('a', class_='pagination__direction--forward', href=True)
        for link in pagination_links:
            if 'Вперед →' in link.text or 'Next' in link.text:
                return link['href']
        return None

    def refresh(self):
        self.driver.refresh()

if __name__ == '__main__':
    pass
