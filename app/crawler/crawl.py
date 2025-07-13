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
            base_url="https://cse.snu.ac.kr/en/community/notice?tag=%EC%B1%84%EC%9A%A9%EC%A0%95%EB%B3%B4",
            school_name="서울대학교",
            driver=driver
        )
        # Multiple selectors for SNU-specific elements
        self.content_selectors = [
            ".flow-root",
            ".mb-10",
            "div[class*='flow-root']",
            "main div div div div",
            "article",
            ".content"
        ]
        self.title_selectors = [
            "ul li:first-child span a",
            "li:first-child a",
            "ul li a",
            ".grow a",
            "[href*='notice']",
            "a[href*='view']"
        ]
        self.date_selectors = [
            "ul li:first-child span:last-child",
            "li:first-child span:not(:has(a))",
            ".tracking-wide",
            "span:contains('2024')",
            "span:contains('2025')"
        ]

        # Set default selectors for BaseCrawler compatibility
        self.content_selector = self.content_selectors[0]
        self.title_selector = self.title_selectors[0]
        self.date_selector = self.date_selectors[0]

    def find_element_with_multiple_selectors(self, selectors, element_type="element"):
        """Try multiple selectors until one works"""
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if element_type == "title" and text and len(text) > 5:
                        logging.info(f"Found title with selector '{selector}': {text}")
                        return element
                    elif element_type == "date" and text and ('2024' in text or '2025' in text):
                        logging.info(f"Found date with selector '{selector}': {text}")
                        return element
                    elif element_type == "content" and text and len(text) > 100:
                        logging.info(f"Found content with selector '{selector}': {text[:100]}...")
                        return element
                    elif element_type == "element" and text:
                        return element
            except Exception as e:
                logging.warning(f"Selector '{selector}' failed: {e}")
                continue
        return None

    def get_notice_content(self, notice_url):
        """Override to use multiple content selectors"""
        try:
            logging.info(f"Fetching content from: {notice_url}")
            self.driver.get(notice_url)
            time.sleep(3)

            content_element = self.find_element_with_multiple_selectors(
                self.content_selectors,
                "content"
            )

            if content_element:
                content_text = content_element.text.strip()
                logging.info(f"Successfully retrieved content from {notice_url}")
                return content_text
            else:
                logging.warning("Content not found with any selector")
                return "Content not found"

        except Exception as e:
            logging.error(f"Error getting notice content: {e}")
            return "Content not found"

    def crawl(self):
        """Override crawl method to use multiple selectors"""
        try:
            logging.info(f"Starting crawl for {self.school_name}")
            self.driver.get(self.base_url)
            time.sleep(10)

            try:
                logging.info("Processing notice")

                # Find title element using multiple selectors
                title_element = self.find_element_with_multiple_selectors(
                    self.title_selectors,
                    "title"
                )

                if not title_element:
                    logging.error("Could not find title element with any selector")
                    # Debug: show available links
                    try:
                        all_links = self.driver.find_elements(By.TAG_NAME, "a")
                        logging.info(f"Total links found: {len(all_links)}")
                        for i, link in enumerate(all_links[:10]):
                            href = link.get_attribute('href')
                            text = link.text.strip()[:50]
                            if href and 'notice' in href:
                                logging.info(f"Notice link {i+1}: {text} -> {href}")
                    except Exception as debug_e:
                        logging.error(f"Debug failed: {debug_e}")
                    return

                title = title_element.text.strip()
                logging.info(f"Found title: {title}")

                # Find date element using multiple selectors
                date_element = self.find_element_with_multiple_selectors(
                    self.date_selectors,
                    "date"
                )

                if date_element:
                    date = date_element.text.strip()
                    logging.info(f"Found date: {date}")
                else:
                    date = "Date not found"
                    logging.warning("Could not find date with any selector")

                # Get URL
                href = title_element.get_attribute('href')
                if not href:
                    logging.warning("No URL found")
                    return

                # Handle relative URLs
                from urllib.parse import urljoin
                full_notice_url = urljoin(self.base_url, href)
                logging.info(f"Processing URL: {full_notice_url}")

                # Get content
                content = self.get_notice_content(full_notice_url)

                # Save notice
                self.send_notice(title, content, full_notice_url, date, school=self.school_name)

            except NoSuchElementException as e:
                logging.error(f"Element not found: {e}")
            except Exception as e:
                logging.error(f"Error processing notice: {e}")

        except Exception as e:
            logging.error(f"Error during crawling: {e}")

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
