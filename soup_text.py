from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests

def send_notice(title, content, url):
    endpoint_url = 'http://127.0.0.1:8000/sapi/insert_notice'

    data={
        'title': title,
        'content': content,
        'original_link': url
    }
    # Sending a POST request to the backend
    response = requests.post(endpoint_url, json=data)

    if response.status_code == 200:
        print('Data sent successfully to the backend.')
    else:
        print('Failed to send data:', response.content)
        
        
def create_headless_driver():
    options = Options()
    options.headless = True  # Enable headless mode
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Function to get the full content of a notice
def get_notice_content(notice_url):
    # Setting up the WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    driver.get(notice_url)
    time.sleep(3)  # Wait for the page to load

    # Replace with the correct selector
    content_selector = "#bo_v_con"
    
    # Find the element and get its text
    content_element = driver.find_element(By.CSS_SELECTOR, content_selector)
    content_text = content_element.text if content_element else "Content not found"

    driver.quit() 
    return content_text

# Base URL
base_url = "https://cs.yonsei.ac.kr/bbs/board.php?bo_table=sub5_5"

# Setting up the WebDriver for the main page
driver = create_headless_driver()

# Navigate to the base URL
driver.get(base_url)
time.sleep(3)  # Wait for the page to load

# Loop through the specified range of li elements
for i in range(2, 3):
    # Construct the selector for each notice
    title_selector = f"#fboardlist > div > table > tbody > tr:nth-child(1) > td.td_subject > div > a"
    date_selector = f"#fboardlist > div > table > tbody > tr:nth-child(1) > td.td_datetime.hidden-xs"

    try:
        title_element = driver.find_element(By.CSS_SELECTOR, title_selector)
        title = title_element.text.strip()
        date_element = driver.find_element(By.CSS_SELECTOR, date_selector)
        date = date_element.text.strip()
        
        # partial_href = title_element.get_attribute('href')
        # full_notice_url = partial_href
        full_notice_url = title_element.get_attribute('href')

        # Get the content of the notice
        content = get_notice_content(full_notice_url)

        print(f"Notice {i}: {title}")
        print("Content:", content)
        print("Date:",date)
        print("----")
        send_notice(title, content, full_notice_url)


    except Exception as e:
        print(f"Error processing notice {i}: {e}")

driver.quit()  # Close the browser