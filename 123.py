from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import os

# ==================== تنظیمات کاربر ====================
USE_PROXY = True
PROXY_ADDR = "127.0.0.1:8118"  # پورت Privoxy
EMAIL_USER = 'dexscreeneramirzamani@gmail.com'
EMAIL_PASS = 'urcs rehx ttyt hzbv'
RECIPIENT = 'amirhosseinzamanifarsi@gmail.com'
# =====================================================

def scrape_dex():
    print(f"\n🚀 شروع عملیات استخراج: {time.strftime('%H:%M:%S')}")
    
    # ۱. راه‌اندازی نمایشگر مجازی برای لینوکس بدون مانیتور
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        co.set_argument('--incognito') # حالت ناشناس برای کاهش ردپا
        
        if USE_PROXY:
            print(f"🛡️ فعالسازی پروکسی: {PROXY_ADDR}")
            co.set_proxy(PROXY_ADDR)
            
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        
        # ۲. باز کردن سایت با زمان انتظار منعطف
        print("🌐 در حال بارگذاری DexScreener...")
        page.get('https://dexscreener.com/', retry=3, timeout=30)
        
        # ۳. سیستم هوشمند عبور از کپچا و لود جدول
        success = False
        for i in range(20): # حداکثر ۲ دقیقه صبر
            time.sleep(6)
            
            # بررسی لود شدن جدول (نشانه موفقیت)
            if page.ele('.ds-dex-table', timeout=2):
                print("✅ جدول با موفقیت لود شد!")
                success = True
                break
                
            # شناسایی و کلیک روی کپچا (Turnstile/Cloudflare)
            title = page.title.lower()
            if "verify" in title or "moment" in title or "attention" in title:
                print(f"⚠️ کپچا مشاهده شد (تلاش {i+1}). در حال تلاش برای کلیک...")
                
                # پیدا کردن دکمه با چندین متد مختلف
                btn = page.ele('@type=checkbox', timeout=2) or \
                      page.ele('text:Verify you are human', timeout=2) or \
                      page.ele('.ctp-checkbox-label', timeout=2)
                
                if btn:
                    print("👆 کلیک روی دکمه کپچا انجام شد.")
                    btn.click(by_js=False) # کلیک فیزیکی واقعی
            
            if i == 10: # اگر خیلی طول کشید، یکبار رفرش کن
                print("🔄 رفرش صفحه به دلیل تأخیر...")
                page.refresh()

        # ۴. استخراج داده‌ها
        if success:
            print("📊 شروع استخراج ردیف‌ها...")
            time.sleep(10) # زمان اضافی برای لود کامل قیمت‌های متغیر
            
            table = page.ele('.ds-dex-table')
            data_list = table.text.splitlines()

            # استخراج کنتراکت‌ها (Contract Addresses)
            links = page.eles('tag:a')
            contracts = [l.attr('href').split('/')[-1] for l in links if l.attr('href') and len(l.attr('href').split('/')[-1]) > 30]

            # فیلتر و تمیزکاری لیست
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            garbage = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
            clean_data = [x for x in data_list if x not in garbage and len(x) > 0]
            
            rows = []
            for i in range(0, len(clean_data) - 14, 15):
                rows.append(clean_data[i:i+15])

            if rows:
                df = pd.DataFrame(rows, columns=titles)
                # مچ کردن کنتراکت‌ها
                if contracts:
                    unique_c = list(dict.fromkeys(contracts))
                    df['CONTRACT ADDRESS'] = (unique_c * (len(df)//len(unique_c)+1))[:len(df)]
                
                csv_file = f"dex_report_{time.strftime('%H%M')}.csv"
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"💾 فایل با {len(df)} سطر ساخته شد.")

                # ۵. ارسال ایمیل
                try:
                    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)
                    yag.send(
                        to=RECIPIENT, 
                        subject=f"Dex Report {time.strftime('%H:%M')}", 
                        contents="گزارش جدید بازار پیوست شد.",
                        attachments=csv_file
                    )
                    print("📧 ایمیل با موفقیت ارسال شد.")
                    os.remove(csv_file) # حذف فایل بعد از ارسال
                except Exception as e:
                    print(f"❌ خطا در ارسال ایمیل: {e}")
            else:
                print("⚠️ جدول خالی بود یا دیتایی استخراج نشد.")
        else:
            print("❌ شکست در عبور از کپچا/لود صفحه.")
            page.get_screenshot('error_log.png')
            print("📸 اسکرین‌شات خطا ذخیره شد (error_log.png).")

    except Exception as e:
        print(f"❌ خطای بحرانی: {e}")
    finally:
        if page:
            page.quit()
        display.stop()
        print("🏁 پایان چرخه و آزادسازی منابع.")

# زمان‌بندی: هر ۱۰ دقیقه یکبار
schedule.every(10).minutes.do(scrape_dex)

# اجرای بار اول بلافاصله
scrape_dex()

while True:
    schedule.run_pending()
    time.sleep(1)
