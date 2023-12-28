from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
from datetime import datetime

def convert_date_format(date_str):
    # Parse the date string into a datetime object
    try:
        date_obj = datetime.strptime(date_str, "%Y/%m/%d")
    except ValueError as e:
        # Handle the error if the date format is incorrect
        print(f"Error converting date: {e}")
        return None

    # Format the datetime object back to a string
    formatted_date_str = date_obj.strftime("%Y-%m-%d")
    return formatted_date_str

class BaseCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        
    def create_headless_driver(self):
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver
    
    def send_notice(self, title, content, url, date, school):
        endpoint_url = 'http://127.0.0.1:8000/api/insert_notice'
        data = {
            'title': title,
            'content': content,
            'original_link': url,
            'date_posted': date,
            'source_school': school,
        }
        response = requests.post(endpoint_url, json=data)
        if response.status_code == 200:
            print('Data sent successfully to the backend.')
        else:
            print('Failed to send data:', response.content)
     

class SkkuCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("https://sw.skku.edu/sw/notice.do")

    def get_notice_content(self, notice_url, content_selector):
        driver = self.create_headless_driver()
        driver.get(notice_url)
        time.sleep(3)
        
        content_selector = "div.board-view-content-wrap.board-view-txt"
        content_element = driver.find_element(By.CSS_SELECTOR, content_selector)
        content_text = content_element.text if content_element else "Content not found"
        
        driver.quit()
        return content_text

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

                self.send_notice(title, content, full_notice_url, date, school="성균관대학교")

            except Exception as e:
                print(f"Error processing notice {i}: {e}")

        driver.quit()


class SnuCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("https://cse.snu.ac.kr/department-notices?c%5B%5D=40&c%5B%5D=107&keys=")

    def get_notice_content(self, notice_url):
        driver = self.create_headless_driver()
        driver.get(notice_url)
        time.sleep(3)
        
        content_selector = "#node-69774 > div.content"
        content_element = driver.find_element(By.CSS_SELECTOR, content_selector)
        content_text = content_element.text if content_element else "Content not found"
        
        driver.quit()
        return content_text
    
    def crawl(self):
        driver = self.create_headless_driver()
        driver.get(self.base_url)
        time.sleep(3)

        for i in range(2, 3):
            title_selector = f"#block-system-main > div > div > div.view-content > table > tbody > tr:nth-child({i}) > td.views-field.views-field-title > a"
            date_selector = f"#block-system-main > div > div > div.view-content > table > tbody > tr:nth-child({i}) > td.views-field.views-field-created"
            try:
                title_element = driver.find_element(By.CSS_SELECTOR, title_selector)
                title = title_element.text.strip()
                
                date_element = driver.find_element(By.CSS_SELECTOR, date_selector)
                date = convert_date_format(date_element.text.strip())

                partial_href = title_element.get_attribute('href')
                full_notice_url = partial_href

                content = self.get_notice_content(full_notice_url)

                self.send_notice(title, content, full_notice_url, date, school="서울대학교")

            except Exception as e:
                print(f"Error processing notice {i}: {e}")

        driver.quit()


class YonseiCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("https://cs.yonsei.ac.kr/bbs/board.php?bo_table=sub5_5")

    def get_notice_content(self, notice_url):
        driver = self.create_headless_driver()
        driver.get(notice_url)
        time.sleep(3)
        
        content_selector = "#bo_v_con"
        content_element = driver.find_element(By.CSS_SELECTOR, content_selector)
        content_text = content_element.text if content_element else "Content not found"
        
        driver.quit()
        return content_text
    
    def crawl(self):
        driver = self.create_headless_driver()
        driver.get(self.base_url)
        time.sleep(3)

        for i in range(2, 3):
            title_selector = f"#fboardlist > div > table > tbody > tr:nth-child(1) > td.td_subject > div > a"
            date_selector = f"#fboardlist > div > table > tbody > tr:nth-child(1) > td.td_datetime.hidden-xs"
            try:
                title_element = driver.find_element(By.CSS_SELECTOR, title_selector)
                title = title_element.text.strip()
                
                date_element = driver.find_element(By.CSS_SELECTOR, date_selector)
                date = date_element.text.strip()

                full_notice_url = title_element.get_attribute('href')

                content = self.get_notice_content(full_notice_url)

                self.send_notice(title, content, full_notice_url, date, school="연세대학교")

            except Exception as e:
                print(f"Error processing notice {i}: {e}")

        driver.quit()
