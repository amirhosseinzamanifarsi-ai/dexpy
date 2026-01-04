import time
import random
import schedule
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import pandas
import yagmail
import re

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0")
    
    # تنظیمات پروکسی Tor
    options.set_preference("network.proxy.type", 1)
    options.set_preference("network.proxy.socks", "127.0.0.1")
    options.set_preference("network.proxy.socks_port", 9050)
    options.set_preference("network.proxy.socks_version", 5)
    options.set_preference("network.proxy.socks_remote_dns", True)
    
    # راه‌اندازی مجدد سرویس با زمان‌بندی
    service = Service('/usr/bin/geckodriver', service_args=["--marionette-port", "51017"])
    driver = webdriver.Firefox(service=service, options=options)
    return driver

def human_like_wait():
    time.sleep(random.uniform(2, 5))

def extract_data():
    driver = None
    try:
        print("در حال راه‌اندازی Firefoxx...")
        driver = setup_driver()
        
        url = 'https://dexscreener.com/'
        
        print("در حال بارگذاری صفحه...")
        driver.get(url)
        human_like_wait()
        
        # رول کردن صفحه
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        human_like_wait()
        
        # انتظار برای جدول
        wait = WebDriverWait(driver, 60)  # زمان انتظار کمتر
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ds-dex-table')))
        human_like_wait()
        
        # استخراج متن جدول
        table = driver.find_element(By.CSS_SELECTOR, '.ds-dex-table')
        raw_text = table.text
        lines = raw_text.splitlines()
        
        titles = ['RANK','TOKEN','EXCHANGE','FULL NAME','PRICE','AGE','TXNS','VOLUME','MAKERS','5M','1H','6H','24H','LIQUIDITY','MCAP']
        data_lines = lines[12:]
        
        skip_list = ['750','3','210','880','780','150','WP','720','V4','20','50','70','60','CPMM','180','620','80','100V3','V3','200','V1','30','OOPS','100','550','130','CLMM','DLMM','40','600','300','V2','500','110','DYN','DYN2','/','1000','10','310','850','120','660','510','530']
        filtered = [line for line in data_lines if line not in skip_list]
        
        tokens = []
        for i in range(0, len(filtered), 15):
            row = filtered[i:i+15]
            if len(row) == 15:
                tokens.append(row)
        
        df = pandas.DataFrame(tokens, columns=titles)
        
        # استخراج CONTRACT ADDRESS
        source = driver.page_source
        
        # regex بهتر
        contract_pattern = r'href="([^"]*0x[a-fA-F0-9]{40}[^"]*)"'
        contracts = re.findall(contract_pattern, source)
        if not contracts:
            contract_pattern_2 = r'0x[a-fA-F0-9]{40}'
            contracts = re.findall(contract_pattern_2, source)
        
        contracts = list(dict.fromkeys(contracts))
        
        print(f"تعداد آدرس‌های پیدا شده: {len(contracts)}")
        print(f"تعداد ردیف‌ها: {len(df)}")
        
        # رفع خطا: ستون خالی یا مقداردهی
        if len(contracts) == len(df):
            df['CONTRACT ADDRESS'] = contracts
        else:
            df['CONTRACT ADDRESS'] = ''
            # df['CONTRACT ADDRESS'] = contracts[:len(df)] + [''] * (len(df) - len(contracts))
        
        csv_name = 'dexscrrener_selenium.csv'
        df.to_csv(csv_name, index=False, encoding='utf-8')
        
        # ایمیل
        yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
        yag.send('amirhosseinzamanifarsi@gmail.com', 'test', csv_name)
        print(f"✅ فایل {csv_name} با موفقیت ایمیل شد.")
        
    except TimeoutException:
        print("❌ صفحه بیش از حد طول کشید.")
    except WebDriverException as e:
        if "HTTPConnectionPool" in str(e):
            print("❌ اتصال به localhost:51017 یا Tor مشکل دارد. دوباره تلاش می‌کنیم...")
        else:
            print(f"❌ خطای دیگر در WebDriver: {e}")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
    finally:
        if driver:
            driver.quit()

# برنامه‌ریزی
schedule.every(2).minutes.do(extract_data)  # از 1 دقیقه به 2 دقیقه تغییر دادم

print("شروع برنامه. هر 2 دقیقه یک بار اجرا می‌شود...")
while True:
    schedule.run_pending()
    time.sleep(1)
