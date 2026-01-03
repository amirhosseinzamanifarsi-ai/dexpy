from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time

def check_page():
    # تنظیمات Firefox
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
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    
    # User-Agent متفاوت
    options.set_preference("general.useragent.override", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    try:
        driver = webdriver.Firefox(options=options)
        
        print("در حال باز کردن صفحه...")
        
        # تلاش برای باز کردن صفحه
        driver.get("https://www.tgju.org/profile/price_dollar_rl/history")
        
        # انتظار برای لود صفحه
        time.sleep(5)
        
        # چک کردن محتوای صفحه
        page_title = driver.title
        page_source = driver.page_source[:1000]  # فقط 1000 کاراکتر اول
        
        print(f"عنوان صفحه: {page_title}")
        print(f"محتوای صفحه (1000 کاراکتر اول):")
        print(page_source)
        
        # سعی برای پیدا کردن جدول
        try:
            table = driver.find_element(By.TAG_NAME, "table")
            print("✅ جدول پیدا شد!")
            return True
        except:
            print("❌ جدول پیدا نشد")
            return False
            
    except Exception as e:
        print(f"❌ خطا در باز کردن صفحه: {e}")
        return False
    finally:
        if driver:
            driver.quit()

# اجرای تست
check_page()
