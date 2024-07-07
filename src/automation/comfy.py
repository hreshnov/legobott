# BUILT-IN
from time import sleep

# [SELENIUM]
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

# [SELENIUM EXCEPTIONS]
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException

from bs4 import BeautifulSoup

# LOCAL
from .base import Base

class Comfy(Base):
    def __init__(self):
        super().__init__()

    def get_the_link(self, url: str, attempts: int = 3) -> str:
        if attempts < 1:
            return ""
        self.driver.get(url)
        sleep(self.sleep_time())
        try:
            self.wait(10).until(ec.presence_of_element_located((
                By.CLASS_NAME, 'category-image-slider'
            )))
        except (TimeoutException, WebDriverException):
            return self.get_the_link(url, attempts - 1)
        return self.driver.page_source

    def open_ad(self, ad_url: str, attempts: int = 3) -> str:
        if attempts < 1:
            return ""
        self.driver.get(ad_url)
        sleep(self.sleep_time())
        try:
            self.wait(10).until(ec.presence_of_element_located((
                By.CLASS_NAME, 'gen-tab__name'
            )))
        except (TimeoutException, WebDriverException):
            return self.open_ad(ad_url, attempts - 1)
        return self.driver.page_source


    def get_next_page_url(self, current_page_source):
        soup = BeautifulSoup(current_page_source, 'html.parser')
        pagination_links = soup.find_all('a', class_='pagination-item p-i p-i--meta', href=True)

        # Find the next page URL
        for link in pagination_links:
            if 'Вперед →' in link.text or 'Next' in link.text:  # Check if the link is for the next page
                return link['href']

    def refresh(self):
        self.driver.refresh()

if __name__ == '__main__':
    pass
