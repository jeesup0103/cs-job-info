from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import time
import requests
from datetime import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, Notice
from app.db.schemas import NoticeRequest
from urllib.parse import urljoin
import logging
import platform
import subprocess
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:1234@localhost:3306/notice_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create database tables
Base.metadata.create_all(bind=engine)
logging.info("Database tables created successfully")

def check_chromedriver():
    try:
        # Check common Homebrew installation paths
        possible_paths = [
            '/opt/homebrew/bin/chromedriver',  # M1/M2 Mac Homebrew path
            '/usr/local/bin/chromedriver',     # Intel Mac Homebrew path
            'chromedriver'                     # System PATH
        ]

        for path in possible_paths:
            try:
                subprocess.run([path, '--version'], capture_output=True, check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        return False
    except Exception:
        return False

def get_chromedriver_path():
    # Check common Homebrew installation paths
    possible_paths = [
        '/opt/homebrew/bin/chromedriver',  # M1/M2 Mac Homebrew path
        '/usr/local/bin/chromedriver',     # Intel Mac Homebrew path
        'chromedriver'                     # System PATH
    ]

    for path in possible_paths:
        try:
            subprocess.run([path, '--version'], capture_output=True, check=True)
            return path
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return None

def check_chrome():
    try:
        if platform.system() == 'Linux':
            # Check for Chrome or Chromium
            chrome_installed = subprocess.run(['which', 'google-chrome'], capture_output=True).returncode == 0
            chromium_installed = subprocess.run(['which', 'chromium-browser'], capture_output=True).returncode == 0
            return chrome_installed or chromium_installed
        else:
            return os.path.exists('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    except Exception:
        return False

class ChromeDriverManager:
    def __init__(self):
        self.driver = None

    def create_driver(self):
        if self.driver is not None:
            return self.driver

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        # Handle different platforms
        if platform.system() == 'Darwin':  # macOS
            if platform.machine() == 'arm64':  # M1/M2 Mac
                if not check_chrome():
                    raise WebDriverException("Chrome not found. Please install Google Chrome")
                options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

                chromedriver_path = get_chromedriver_path()
                if chromedriver_path:
                    service = Service(executable_path=chromedriver_path)
                    logging.info(f"Using ChromeDriver at: {chromedriver_path}")
                else:
                    logging.error("ChromeDriver not found. Please install it using: brew install chromedriver")
                    raise WebDriverException("ChromeDriver not found")
            else:  # Intel Mac
                service = Service(ChromeDriverManager().install())
        elif platform.system() == 'Linux':  # Linux (including Docker)
            chrome_bin = os.getenv('CHROME_BIN', '/usr/bin/chromium')
            chromedriver_path = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')

            options.binary_location = chrome_bin
            service = Service(executable_path=chromedriver_path)
            logging.info(f"Using Chrome at: {chrome_bin}")
            logging.info(f"Using ChromeDriver at: {chromedriver_path}")
        else:  # Windows or others
            service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=service, options=options)
        logging.info(f"Created headless Chrome driver for {platform.system()} {platform.machine()}")
        return self.driver

    def quit(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            logging.info("Chrome driver closed")

class BaseCrawler:
    def __init__(self, base_url, school_name, driver):
        self.base_url = base_url
        self.school_name = school_name
        self.db = SessionLocal()
        self.driver = driver  # Use the provided driver instance
        logging.info(f"Initialized crawler for {self.school_name} with base URL: {base_url}")

    def send_notice(self, title, content, url, date, school):
        try:
            logging.info(f"Attempting to save notice: {title}")
            notice_data = NoticeRequest(
                title=title,
                content=content,
                original_link=url,
                date_posted=date,
                source_school=school
            )

            # Check if notice already exists
            existing_notice = self.db.query(Notice).filter(Notice.original_link == url).first()
            if existing_notice:
                logging.info(f"Notice already exists: {title}")
                return

            # Create new notice
            new_notice = Notice(
                title=notice_data.title,
                content=notice_data.content,
                original_link=notice_data.original_link,
                date_posted=notice_data.date_posted,
                source_school=notice_data.source_school
            )

            self.db.add(new_notice)
            self.db.commit()
            logging.info(f"Successfully added notice: {title}")

        except Exception as e:
            logging.error(f"Error saving notice: {e}")
            self.db.rollback()
        finally:
            self.db.close()

    def get_notice_content(self, notice_url):
        try:
            logging.info(f"Fetching content from: {notice_url}")
            self.driver.get(notice_url)
            time.sleep(3)

            content_element = self.driver.find_element(By.CSS_SELECTOR, self.content_selector)
            content_text = content_element.text if content_element else "Content not found"
            logging.info(f"Successfully retrieved content from {notice_url}")
            return content_text

        except Exception as e:
            logging.error(f"Error getting notice content: {e}")
            return "Content not found"

    def crawl(self):
        try:
            logging.info(f"Starting crawl for {self.school_name}")
            self.driver.get(self.base_url)
            time.sleep(10)

            try:
                logging.info("Processing notice")
                title_element = self.driver.find_element(By.CSS_SELECTOR, self.title_selector)
                title = title_element.text.strip()
                logging.info(f"Found title: {title}")

                date_element = self.driver.find_element(By.CSS_SELECTOR, self.date_selector)
                date = date_element.text.strip()
                logging.info(f"Found date: {date}")

                href = title_element.get_attribute('href')
                if not href:
                    logging.warning("No URL found")
                    return

                # Handle relative URLs
                full_notice_url = urljoin(self.base_url, href)
                logging.info(f"Processing URL: {full_notice_url}")

                content = self.get_notice_content(full_notice_url)
                self.send_notice(title, content, full_notice_url, date, school=self.school_name)

            except NoSuchElementException as e:
                logging.error(f"Element not found: {e}")
            except Exception as e:
                logging.error(f"Error processing notice: {e}")

        except Exception as e:
            logging.error(f"Error during crawling: {e}")


class SkkuCrawler(BaseCrawler):
    def __init__(self, driver):
        super().__init__(
            base_url="https://sw.skku.edu/sw/notice.do?mode=list&srCategoryId1=1585&srSearchKey=&srSearchVal=",
            school_name="성균관대학교",
            driver=driver
        )
        self.content_selector = "div.board-view-content-wrap.board-view-txt"
        self.title_selector = "#jwxe_main_content > div > div > div.board-name-list.board-wrap > ul > li:nth-child(1) > dl > dt > a"
        self.date_selector = "#jwxe_main_content > div > div > div.board-name-list.board-wrap > ul > li:nth-child(1) > dl > dd > ul > li:nth-child(3)"

class SkkuCrawler2(BaseCrawler):
    def __init__(self, driver):
        super().__init__(
            base_url="https://cse.skku.edu/cse/notice.do?mode=list&srCategoryId1=1585&srSearchKey=&srSearchVal=",
            school_name="성균관대학교",
            driver=driver
        )
        self.content_selector = "div.board-view-content-wrap.board-view-txt"
        self.title_selector = "#jwxe_main_content > div > div > div.board-name-list.board-wrap > ul > li:nth-child(8) > dl > dt > a"
        self.date_selector = "#jwxe_main_content > div > div > div.board-name-list.board-wrap > ul > li:nth-child(8) > dl > dd > ul > li:nth-child(3)"

def run_all_skku_crawlers(driver):
    skku_crawler_1 = SkkuCrawler(driver)
    skku_crawler_2 = SkkuCrawler2(driver)

    results_1 = skku_crawler_1.crawl()
    results_2 = skku_crawler_2.crawl()

    # Combine results from both crawlers
    combined_results = results_1 + results_2
    return combined_results

class SnuCrawler(BaseCrawler):
    def __init__(self, driver):
        super().__init__(
            base_url="https://cse.snu.ac.kr/community/notice?tag=%EC%B1%84%EC%9A%A9%EC%A0%95%EB%B3%B4",
            school_name="서울대학교",
            driver=driver
        )
        self.content_selector = (
            "body > main > div > div > div.bg-neutral-50.px-5.pt-9.sm\\:pl-\\[100px\\].sm\\:pr-\\[340px\\].pb-\\[150px\\] > "
            "div.flow-root.mb-10 > div > p"
        )
        self.title_selector = "html > body > main > div > div:nth-child(2) > div:nth-child(2) > ul > li:nth-child(1) > span:nth-child(2) > a"
        self.date_selector = (
            "body > main > div > div.relative.grow.bg-white.p-\\[1.75rem_1.25rem_4rem_1.25rem\\].sm\\:p-\\[2.75rem_360px_150px_100px\\] > "
            "div.mb-10.mt-9.border-y.border-neutral-200.sm\\:mx-2\\.5 > ul > li:nth-child(1) > "
            "span.sm\\:w-auto.sm\\:min-w-\\[7.125rem\\].tracking-wide.sm\\:pl-8.sm\\:pr-10"
        )

class KaistCrawler(BaseCrawler):
    def __init__(self, driver):
        super().__init__(
            base_url="https://cs.kaist.ac.kr/bbs/recruit",
            school_name="카이스트",
            driver=driver
        )
        self.content_selector = "#container > div.inner > div > div.viewDetail"
        self.title_selector = "#container > div.inner > div.eval_tb > table > tbody > tr:nth-child(3) > td.line2_2_txt > a"
        self.date_selector = "#container > div.inner > div.eval_tb > table > tbody > tr:nth-child(3) > td:nth-child(4)"

    def get_full_notice_url(self, href):
        # Regular expression to capture the parameters from the JavaScript call
        pattern = r"javascript:readArticle\('([^']+)', '([^']+)', '([^']+)', '([^']+)', '([^']*)', '([^']+)'\)"
        match = re.search(pattern, href)

        if match:
            bbs_id, bbs_sn, page, skey, svalue, menu = match.groups()
            # Build the URL using the extracted parameters
            return f"https://cs.kaist.ac.kr/board/view?bbs_id={bbs_id}&bbs_sn={bbs_sn}&page={page}&skey={skey}&svalue={svalue}&menu={menu}"
        else:
            logging.error("No match found for href: {href}")
            return None

    def crawl(self):
        try:
            logging.info(f"Starting crawl for {self.school_name}")
            self.driver.get(self.base_url)
            time.sleep(10)

            try:
                logging.info("Processing notice")
                title_element = self.driver.find_element(By.CSS_SELECTOR, self.title_selector)
                title = title_element.text.strip()
                logging.info(f"Found title: {title}")

                date_element = self.driver.find_element(By.CSS_SELECTOR, self.date_selector)
                date = date_element.text.strip()
                logging.info(f"Found date: {date}")

                href = title_element.get_attribute('href')
                full_notice_url = self.get_full_notice_url(href)
                if not full_notice_url:
                    logging.warning("No valid URL found")
                    return

                logging.info(f"Processing URL: {full_notice_url}")

                content = self.get_notice_content(full_notice_url)
                self.send_notice(title, content, full_notice_url, date, school=self.school_name)

            except NoSuchElementException as e:
                logging.error(f"Element not found: {e}")
            except Exception as e:
                logging.error(f"Error processing notice: {e}")

        except Exception as e:
            logging.error(f"Error during crawling: {e}")

class YonseiCrawler(BaseCrawler):
    def __init__(self, driver):
        super().__init__(
            base_url="https://cs.yonsei.ac.kr/csai/board/jobInfo.do",
            school_name="연세대학교",
            driver=driver
        )
        self.content_selector = "#jwxe_main_content > div > div.board-wrap > div > dl.board-write-box.board-write-box-v03 > dd > div"
        self.title_selector = "#jwxe_main_content > div > div > div > table > tbody > tr:nth-child(1) > td.text-left > div.c-board-title-wrap > a"
        self.date_selector = "#jwxe_main_content > div > div > div > table > tbody > tr:nth-child(1) > td:nth-child(5)"


class HanyangCrawler(BaseCrawler):
    def __init__(self, driver):
        super().__init__(
            base_url="https://cs.hanyang.ac.kr/board/job_board.php",
            school_name="한양대학교",
            driver=driver
        )
        self.content_selector="#content_box > div > table.bbs_view > tbody > tr:nth-child(3) > td > table:nth-child(2) > tbody > tr > td",
        self.title_selector="#content_box > div > table > tbody > tr:nth-child(1) > td.left > a",
        self.date_selector="#content_box > div > table > tbody > tr:nth-child(1) > td:nth-child(5)",
