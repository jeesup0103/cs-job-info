# import requests
# from bs4 import BeautifulSoup

# # URL to scrape
# url = "https://sw.skku.edu/sw/notice.do"

# # Send a GET request to the URL
# response = requests.get(url)
# response.raise_for_status()  # This will raise an exception for HTTP errors

# # Parse the HTML content
# soup = BeautifulSoup(response.text, 'html.parser')

# # Base part of the CSS selector
# base_selector = "#jwxe_main_content > div > div > div.board-name-list.board-wrap > ul > li:nth-child({}) > dl > dt > a"

# # List to store titles
# notice_titles = []

# # Loop through the first 10 li elements
# for i in range(1, 11):
#     # Create the full selector for each notice
#     selector = base_selector.format(i)

#     # Find the element using the selector
#     title_element = soup.select_one(selector)

#     # Extract the title text and add it to the list
#     if title_element:
#         notice_titles.append(title_element.text.strip())

# # Print the titles
# for idx, title in enumerate(notice_titles, 1):
#     print(f"Notice {idx}: {title}")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

driver = webdriver.Chrome(service= Service(ChromeDriverManager().install()))

url = "https://www.naver.com/"
driver.get(url)
time.sleep(5)