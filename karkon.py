import time
import random
import schedule
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas
import yagmail

# تنظیمات Tor و Firefox
def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0")
    
    # استفاده از Tor (socks5)
    options.set_preference("network.proxy.type", 1)
    options.set_preference("network.proxy.socks", "127.0.0.1")
    options.set_preference("network.proxy.socks_port", 9050)
    options.set_preference("network.proxy.socks_version", 5)
    options.set_preference("network.proxy.socks_remote_dns", True)
    
    service = Service('/usr/bin/geckodriver')
    driver = webdriver.Firefox(service=service, options=options)
    return driver

def human_like_wait():
    time.sleep(random.uniform(2, 5))

def human_like_scroll(driver):
    driver.execute_script("window.scrollTo(0, 0);")
    human_like_wait()
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    human_like_wait()

def extract_data():
    driver = setup_driver()
    url = 'https://dexscreener.com/'
    
    try:
        print("در حال بارگذاری صفحه...")
        driver.get(url)
        human_like_wait()
        
        # اسکرول اولیه
        human_like_scroll(driver)
        
        # انتظار برای ظاهر شدن جدول
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ds-dex-table')))
        human_like_wait()
        
        # استخراج داده
        table = driver.find_element(By.CSS_SELECTOR, '.ds-dex-table')
        raw_text = table.text
        lines = raw_text.splitlines()
        
        # فیلتر ردیف‌ها (مثال)
        titles = ['RANK','TOKEN','EXCHANGE','FULL NAME','PRICE','AGE','TXNS','VOLUME','MAKERS','5M','1H','6H','24H','LIQUIDITY','MCAP']
        data_lines = lines[12:]  # شروع داده‌ها
        
        # حذف ردیف‌های غیرمربوطه
        skip_list = ['750','3','210','880','780','150','WP','720','V4','20','50','70','60','CPMM','180','620','80','100V3','V3','200','V1','30','OOPS','100','550','130','CLMM','DLMM','40','600','300','V2','500','110','DYN','DYN2','/','1000','10','310','850','120','660','510','530']
        filtered = [line for line in data_lines if line not in skip_list]
        
        # تبدیل به DataFrame
        tokens = []
        for i in range(0, len(filtered), 15):
            row = filtered[i:i+15]
            if len(row) == 15:
                tokens.append(row)
        
        df = pandas.DataFrame(tokens, columns=titles)
        
        # --- استخراج CONTRACT ADDRESS ---
        source = driver.page_source
        import re
        contract_pattern = r'" href="([^"/.]*[a-z0-9]{20,})"'
        contracts = re.findall(contract_pattern, source)
        
        # تطبیق تعداد
        if len(df) == len(contracts):
            df['CONTRACT ADDRESS'] = contracts
        else:
            df['CONTRACT ADDRESS'] = contracts[:len(df)]
        
        # ذخیره CSV و ارسال ایمیل
        csv_name = 'dexscrrener_selenium.csv'
        df.to_csv(csv_name, index=False, encoding='utf-8')
        
        yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
        yag.send('amirhosseinzamanifarsi@gmail.com', 'test', csv_name)
        print(f"✅ فایل {csv_name} با موفقیت ایمیل شد.")
        
    except TimeoutException:
        print("❌ Cloudflare یا صفحه بیش از حد طول کشید. دوباره تلاش می‌کنیم.")
        driver.quit()
        return
    except Exception as e:
        print(f"❌ خطای دیگر: {e}")
    finally:
        driver.quit()

# برنامه‌ریزی
schedule.every(1).minute.do(extract_data)

print("شروع برنامه. هر دقیقه یک بار اجرا می‌شود...")
while True:
    schedule.run_pending()
    time.sleep(1)
