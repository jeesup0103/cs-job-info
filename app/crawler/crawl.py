from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests

class SkkuCrawler:
    def __init__(self):
        self.base_url = "https://sw.skku.edu/sw/notice.do"

    def create_headless_driver(self):
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def get_notice_content(self, notice_url):
        driver = self.create_headless_driver()
        driver.get(notice_url)
        time.sleep(3)
        
        content_selector = "div.board-view-content-wrap.board-view-txt"
        content_element = driver.find_element(By.CSS_SELECTOR, content_selector)
        content_text = content_element.text if content_element else "Content not found"
        
        driver.quit()
        return content_text

    def send_notice(self, title, content, url, date):
        endpoint_url = 'http://127.0.0.1:8000/api/insert_notice'
        data = {
            'title': title,
            'content': content,
            'original_link': url,
            'date_posted': date,
            'source_school': 'skku',
        }
        response = requests.post(endpoint_url, json=data)
        if response.status_code == 200:
            print('Data sent successfully to the backend.')
        else:
            print('Failed to send data:', response.content)

    def crawl(self):
        driver = self.create_headless_driver()
        driver.get(self.base_url)
        time.sleep(3)

        for i in range(1, 2):
            title_selector = f"div.board-name-list.board-wrap > ul > li:nth-child({i}) > dl > dt > a"
            date_selector = f"div.board-name-list.board-wrap > ul > li:nth-child({i}) > dl > dd > ul > li:nth-child(3)"
            try:
                title_element = driver.find_element(By.CSS_SELECTOR, title_selector)
                title = title_element.text.strip()
                
                date_element = driver.find_element(By.CSS_SELECTOR, date_selector)
                date = date_element.text.strip()

                partial_href = title_element.get_attribute('href')
                full_notice_url = partial_href

                content = self.get_notice_content(full_notice_url)

                print(f"Notice {i}: {title}")
                print("Content:", content)
                print("Date", date)
                print("----")
                self.send_notice(title, content, full_notice_url, date)

            except Exception as e:
                print(f"Error processing notice {i}: {e}")

        driver.quit()
