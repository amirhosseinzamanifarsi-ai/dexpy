from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
import time

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0")

path_geckodriver = '/usr/bin/geckodriver'
service_path = Service(path_geckodriver)
driver = webdriver.Firefox(service=service_path, options=options)

driver.get('https://dexscreener.com/')
time.sleep(30)  # انتظار طولانی‌تر

# ذخیره سورس صفحه
with open('/tmp/debug_page.html', 'w') as f:
    f.write(driver.page_source)

driver.quit()
print("سورس صفحه در /tmp/debug_page.html ذخیره شد")
