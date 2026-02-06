from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import schedule
import yagmail
import time
from selenium.webdriver.firefox.options import Options
import shutil
import os
import sys

# ░▒▓ تنظیمات مسیر اجرایی برای سرور ▓▒░
os.environ['PATH'] += ":/usr/local/bin:/snap/bin:/usr/bin"

def send_email(subject, body):
    try:
        yag = yagmail.SMTP(
            user='dexscreeneramirzamani@gmail.com',  # ایمیل فرستنده
            password='app_password_here',  # پسورد مخصوص برنامه (از تنظیمات Gmail بسازید)
            host='smtp.gmail.com',
            port=587,
            smtp_starttls=True,
            smtp_ssl=False
        )
        yag.send(
            to=amirhosseinzamanifarsi@gmail.com,  # ایمیل گیرنده
            subject=subject,
            contents=body
        )
        print("📧 ایمیل با موفقیت ارسال شد")
    except Exception as e:
        print(f"🚨 خطا در ارسال ایمیل: {str(e)}")

def scraping_task():
    try:
        # ░▒▓ تشخیص خودکار مسیرهای حیاتی ▓▒░
        firefox_path = shutil.which('firefox') or '/usr/bin/firefox'
        gecko_path = shutil.which('geckodriver') or '/usr/local/bin/geckodriver'
        
        # ░▒▓ تنظیمات پیشرفته فایرفاکس ▓▒░
        options = Options()
        options.binary_location = firefox_path
        options.add_argument("--headless=new")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        service = Service(
            executable_path=gecko_path,
            log_path=os.devnull  # غیرفعال کردن لاگ‌های اضافی
        )

        # ░▒▓ ایجاد درایور با تنظیمات بهینه ▓▒░
        driver = webdriver.Firefox(service=service, options=options)
        driver.set_page_load_timeout(30)
        
        # ▼▼▼ استخراج داده از صفحه ▼▼▼
        driver.get("https://example.com")  # آدرس واقعی خود را جایگزین کنید
        
        # مثال استخراج داده با BeautifulSoup:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # results = soup.find_all('div', class_='target-class')
        # data = [item.text for item in results]
        
        # ▼▼▼ نمونه ذخیره سازی در CSV ▼▼▼
        # import csv
        # with open('data.csv', 'a') as f:
        #     writer = csv.writer(f)
        #     writer.writerow(data)
        
        driver.quit()
        send_email("✅ اجرای موفق", "داده‌ها با موفقیت استخراج شدند")
        return True
        
    except Exception as e:
        error_msg = f"🚨 خطا در اجرا: {str(e)}"
        print(error_msg)
        send_email("❌ خطا در اسکریپت", error_msg)
        return False

# ░▒▓ تنظیمات زمان‌بندی ▓▒░
schedule.every(10).minutes.do(scraping_task)

# ░▒▓ اجرای اصلی اسکریپت ▓▒░
if __name__ == "__main__":
    print("🟢 اسکریپت شروع به کار کرد")
    send_email("🚀 اسکریپت فعال شد", "سیستم اسکرپینگ با موفقیت راه‌اندازی شد")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # کاهش مصرف CPU
    except KeyboardInterrupt:
        send_email("⚠️ اسکریپت متوقف شد", "عملیات توسط کاربر متوقف شد")
        print("⛔ اسکریپت متوقف شد")
        sys.exit(0)
