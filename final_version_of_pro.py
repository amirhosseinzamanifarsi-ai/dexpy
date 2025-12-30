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
import pandas
import yagmail
import datetime
import time
import os

def timing():
    # تنظیمات Firefox برای لینوکس
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    
    # User-Agent مخصوص Firefox روی لینوکس
    user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0"
    options.add_argument(f"--user-agent={user_agent}")
    
    service_path = Service('/usr/bin/geckodriver')
    driver = None
    
    try:
        driver = webdriver.Firefox(service=service_path, options=options)
        print("در حال باز کردن صفحه...")
        
        driver.get('https://dexscreener.com/')
        
        # انتظار برای لود صفحه
        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(8)
        
        # اسکرول برای لود محتوا
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3)
        
        # اسکرول به انتها
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # چک کردن وجود المنت با روش‌های مختلف
        try:
            # روش 1: انتظار برای المنت
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ds-dex-table')))
        except:
            try:
                # روش 2: اسکرول مجدد
                driver.execute_script("window.scrollTo(0, 2000);")
                time.sleep(3)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ds-dex-table')))
            except:
                try:
                    # روش 3: چک کردن وجود المنت بدون انتظار طولانی
                    elements = driver.find_elements(By.CSS_SELECTOR, '.ds-dex-table')
                    if not elements:
                        # روش 4: چک کردن المنت‌های مشابه
                        alt_elements = driver.find_elements(By.CLASS_NAME, 'ds-table')
                        if alt_elements:
                            print("منت ds-table پیدا شد")
                        else:
                            print("هیچ جدولی پیدا نشد")
                            raise ValueError("جدول داده‌ها پیدا نشد")
                except:
                    raise
        
        # استخراج داده‌ها
        print("در حال استخراج داده‌ها...")
        data1 = driver.find_element(By.CSS_SELECTOR, '.ds-dex-table')
        data_text = data1.text
        data_list = data_text.splitlines()
        
        # بررسی اینکه داده‌ها وجود دارن
        if len(data_list) < 15:
            raise ValueError("داده کافی یافت نشد")
        
        titles = ['RANK','TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
        new_data = data_list[12:]
        
        # حذف آیتم‌های ناخواسته
        dl_list = ['750','3','210','880','780','150','WP','720','V4','20','50','70','60','CPMM','180','620','80','100V3','V3','200','V1','30','OOPS','100','550','130','CLMM','DLMM','40','600','300','V2','500','110','DYN','DYN2','/','1000','10','310','850','120','660','510','530']
        
        nd = []
        for item in new_data:
            if item not in dl_list:
                nd.append(item)
        
        # ایجاد دیتافریم
        arzha = []
        for i in range(0, len(nd), 15):
            arz = nd[i:i+15]
            if len(arz) == 15:  # مطمئن شو که 15 ستون داره
                arzha.append(arz)
        
        if len(arzha) == 0:
            raise ValueError("هیچ ردیف داده‌ای پیدا نشد")
            
        pd = pandas.DataFrame(arzha, columns=titles)
        
        # استخراج آدرس قراردادها
        ls_con = token_add(driver)
        
        # اضافه کردن آدرس قرارداد
        if len(pd) == len(ls_con):
            pd['CONTRACT ADDRESS'] = ls_con
        else:
            print(f"هشدار: تعداد ردیف‌ها ({len(pd)}) با تعداد آدرس‌ها ({len(ls_con)}) متفاوت است")
            pd['CONTRACT ADDRESS'] = ls_con[:len(pd)]  # فقط به اندازه تعداد ردیف‌ها
        
        # ذخیره CSV
        csvname = f'dexscrrener.csv'
        pd.to_csv(csvname, index=False, encoding='utf-8')
        print(f"فایل {csvname} ذخیره شد")
        
        # ارسال ایمیل
        send_email(csvname)
        print('فایل با موفقیت ارسال شد.')
        
    except Exception as e:
        print(f"خطا رخ داد: {e}")
        if driver:
            # ذخیره اسکرین‌شات و HTML برای دیباگ
            try:
                driver.save_screenshot('debug_screenshot.png')
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print("اسکرین‌شات و HTML صفحه برای دیباگ ذخیره شد")
            except:
                pass
        raise
    
    finally:
        if driver:
            driver.quit()

def token_add(driver):
    """استخراج آدرس قراردادها از صفحه"""
    try:
        source_site = driver.page_source
        t = r'" href="([^".]*[a-z0-9])"'
        v = re.findall(t, source_site)
        
        ls_con = []
        for item in v:
            if len(item) >= 20 and item.startswith('/'):  # فقط لینک‌های معتبر
                ls_con.append(item)
        
        return ls_con
    
    except Exception as e:
        print(f"خطا در استخراج آدرس قراردادها: {e}")
        return []

def send_email(csvname):
    """ارسال ایمیل با yagmail"""
    try:
        ersal_konandeh = 'dexscreeneramirzamani@gmail.com'
        password = 'urcs rehx ttyt hzbv'
        daryaft_konandeh = 'amirhosseinzamanifarsi@gmail.com'
        subject = 'داده‌های DexScreener'
        
        yag = yagmail.SMTP(ersal_konandeh, password)
        yag.send(daryaft_konandeh, subject, csvname)
        
    except Exception as e:
        print(f"خطا در ارسال ایمیل: {e}")
        raise

# برنامه‌ریزی و اجرا
if __name__ == "__main__":
    schedule.every(1).minute.do(timing)
    
    print("شروع برنامه...")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("برنامه توسط کاربر متوقف شد")
            break
        except Exception as e:
            print(f"خطای کلی: {e}")
            time.sleep(5)
            