# BUILT-IN
from random import randint

# [UNDETECTED CHROMEDRIVER]
import undetected_chromedriver as uc

# [SELENIUM]
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

class Base:
    def __init__(self, driver: uc.Chrome = None):
        self.sleep_time = lambda: float(randint(100, 549)/100)
        self.options = webdriver.ChromeOptions()
        # self.options.add_argument('--headless')
        self.options.binary_location = '/usr/bin/google-chrome-stable'
        self.options.add_argument('--no-sandbox')
        self.options.add_argument(
            '--no-first-run --no-service-autorun --password-store=basic'
        )
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-infobars')
        caps = webdriver.DesiredCapabilities.CHROME
        # caps['acceptSslCerts'] = True
        if driver:
            self.driver = driver
        else:
            self.driver = uc.Chrome(
                port=0,
                options=self.options,
                keep_alive=True,
            )

        self.driver.maximize_window()
        self.wait = lambda seconds: WebDriverWait(self.driver, seconds)

if __name__ == '__main__':
    pass
