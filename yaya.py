from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
import requests
import schedule
import re
import pandas as pd
import yagmail
import datetime
import time
import os

def timing():
    print("Starting timing function...")
    
    # تنظیمات Firefox برای سرور لینوکس
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0")
    options.add_argument("--window-size=1280,720")
    
    # استفاده از geckodriver به صورت خودکار (اگر نصب نیست، این خط رو حذف کن)
    try:
        from webdriver_manager.firefox import GeckoDriverManager
        service = Service(GeckoDriverManager().install())
    except:
        # اگر webdriver-manager نصب نیست، از مسیر دستی استفاده کن
        service = Service('/usr/bin/geckodriver')
    
    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        driver.get('https://dexscreener.com/')
        print("Page loaded")
        
        # صبر کنید تا صفحه کاملاً لود شود
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)  # زمان اضافی برای لود کامل
        
        # بررسی محتوای صفحه
        page_source = driver.page_source
        print(f"Page source length: {len(page_source)}")
        
        # روش 1: استفاده از المنت‌های قابل اعتماد
        # ابتدا چک کنید که جدول وجود دارد
        try:
            # سعی کنید المنت‌های مختلف را پیدا کنید
            elements = driver.find_elements(By.TAG_NAME, "table")
            if elements:
                print(f"Found {len(elements)} table elements")
                # اولین جدول را انتخاب کنید
                table = elements[0]
                table_html = table.get_attribute('outerHTML')
                soup = BeautifulSoup(table_html, 'html.parser')
                rows = soup.find_all('tr')
                print(f"Found {len(rows)} rows in table")
            else:
                print("No table found, trying div with specific classes")
                # روش جایگزین: یافتن المنت‌های دیگر
                divs = driver.find_elements(By.CSS_SELECTOR, "div.ds-dex-table-row")
                print(f"Found {len(divs)} div rows")
        except Exception as e:
            print(f"Error finding elements: {e}")
        
        # روش 2: استخراج داده‌ها از صفحه با BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # یافتن المنت‌های مختلف
        data_list = []
        
        # روش اول: یافتن المنت‌هایی که شامل اطلاعات توکن هستند
        token_elements = soup.find_all('div', class_=re.compile('ds-dex-table-row'))
        
        if not token_elements:
            # روش دوم: یافتن المنت‌های عمومی
            token_elements = soup.find_all('div', {'data-testid': re.compile('token')})
        
        if not token_elements:
            # روش سوم: یافتن همه div‌هایی که شامل اطلاعات قیمت هستند
            price_elements = soup.find_all(text=re.compile(r'\$'))
            print(f"Found {len(price_elements)} price elements")
            for price in price_elements[:10]:  # فقط 10 مورد اول
                parent = price.parent
                while parent:
                    if parent.name == 'div' and len(parent.get_text()) > 20:
                        data_list.append(parent.get_text().strip())
                        break
                    parent = parent.parent
        
        # اگر روش‌های بالا جواب نداد، از متن صفحه استخراج کن
        if not data_list:
            # یافتن خطوطی که شامل اطلاعات مالی هستند
            lines = page_source.split('\n')
            financial_lines = []
            for line in lines:
                if '$' in line and ('%' in line or 'ETH' in line or 'SOL' in line):
                    financial_lines.append(line.strip())
            
            data_list = financial_lines[:50]  # فقط 50 خط اول
        
        # ساخت DataFrame
        if data_list:
            # تقسیم داده‌ها به ردیف‌ها
            rows_data = []
            for line in data_list:
                # تمیز کردن داده‌ها
                cleaned_line = re.sub(r'\s+', ' ', line)
                rows_data.append([cleaned_line])
            
            df = pd.DataFrame(rows_data, columns=['Raw Data'])
            print(f"Created DataFrame with {len(df)} rows")
        else:
            # اگر هیچ داده‌ای پیدا نشد، یک DataFrame خالی ایجاد کن
            df = pd.DataFrame({'Message': ['No data found']})
            print("No data extracted")
        
        # ذخیره به CSV
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        csvname = f'dexscrrener_{timestamp}.csv'
        df.to_csv(csvname, index=False, encoding='utf-8')
        print(f"CSV saved as {csvname}")
        
        # ارسال ایمیل
        try:
            send_email(csvname)
        except Exception as e:
            print(f"Email sending failed: {e}")
            
    except Exception as e:
        print(f"Error in timing function: {e}")
        # ذخیره page_source برای دیباگ
        try:
            with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Page source saved to debug_page_source.html")
        except:
            pass
    
    finally:
        driver.quit()

def send_email(csv_file):
    """ارسال ایمیل با فایل پیوست"""
    try:
        ersal_konandeh = 'dexscreeneramirzamani@gmail.com'
        password = 'urcs rehx ttyt hzbv'
        daryaft_konandeh = 'amirhosseinzamanifarsi@gmail.com'
        subject = f'DexScreener Data - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        yag = yagmail.SMTP(ersal_konandeh, password)
        yag.send(
            to=daryaft_konandeh,
            subject=subject,
            contents=f'Attached is the DexScreener data file: {csv_file}',
            attachments=csv_file
        )
        print('Email sent successfully')
    except Exception as e:
        print(f'Email sending failed: {e}')

# برنامه‌ریزی اجرا
schedule.every(1).minutes.do(timing)

if __name__ == "__main__":
    print("Starting DexScreener scraper...")
    timing()  # اجرای اولیه برای تست
    while True:
        schedule.run_pending()
        time.sleep(1)
