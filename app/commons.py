from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os


def get_driver():
    current_dir = os.getcwd()
    driver_path = os.path.join(current_dir, 'chromedriver.exe')
    service = Service(executable_path=driver_path)
    chrome_options = Options()
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(2048, 1536)

    return driver


# EXTRA FEATURES - LATER
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By

# def close_popup(driver, css_selector: str):
#     try:
#         WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
#         close_button = driver.find_element(By.CSS_SELECTOR, css_selector)
#         close_button.click()
#     except Exception as e:
#         print("Exception while closing popup: ", e)
