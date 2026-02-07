from DrissionPage import ChromiumPage, ChromiumOptions
import pandas as pd
import yagmail
import schedule
import time
import re
import os

def timing():
    print(f"\n--- شروع تسک: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # تنظیمات مرورگر برای اجرا در سرور لینوکس (بدون نیاز به نمایشگر مجازی دستی)
    co = ChromiumOptions()
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--headless')  # اجرا در پس‌زمینه
    
    page = None
    try:
        page = ChromiumPage(co)
        print("🌐 در حال باز کردن DexScreener و عبور از آنتی‌بات...")
        
        page.get('https://dexscreener.com/')
        
        # انتظار هوشمند برای لود شدن جدول (حداکثر 40 ثانیه)
        if page.wait.ele_appearing('.ds-dex-table', timeout=40):
            print("✅ وارد سایت شدیم و جدول لود شد.")
            time.sleep(5) # زمان اضافی برای لود کامل قیمت‌ها
            
            # اسکرول به پایین برای لود شدن ردیف‌های بیشتر
            page.scroll.to_bottom()
            time.sleep(2)

            # ۱. استخراج متن جدول
            table_text = page.ele('.ds-dex-table').text
            data_list = table_text.splitlines()

            # ۲. استخراج آدرس‌های کنتراکت با Regex از سورس صفحه
            html_source = page.html
            links = re.findall(r'href="/([^"]+)"', html_source)
            contracts = [l.split('/')[-1] for l in links if len(l.split('/')[-1]) > 30]

            # ۳. پردازش و تمیزکاری داده‌ها (منطق اختصاصی شما)
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
            
            clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]

            rows = []
            for i in range(0, len(clean_data) - 14, 15):
                rows.append(clean_data[i:i+15])

            if rows:
                df = pd.DataFrame(rows, columns=titles)
                
                # تطبیق آدرس‌های کنتراکت
                if contracts:
                    # تکرار لیست کنتراکت‌ها برای پر کردن تمام ردیف‌ها در صورت لزوم
                    extended_contracts = (contracts * (len(df) // len(contracts) + 1))[:len(df)]
                    df['CONTRACT ADDRESS'] = extended_contracts
                
                # ۴. ذخیره در CSV
                csv_name = 'dex_report.csv'
                df.to_csv(csv_name, index=False, encoding='utf-8-sig')
                print(f"📊 فایل با {len(df)} ردیف آماده شد.")

                # ۵. ارسال ایمیل
                try:
                    yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
                    yag.send(
                        to='amirhosseinzamanifarsi@gmail.com',
                        subject=f'DexScreener Report {time.strftime("%H:%M")}',
                        contents='آخرین اطلاعات استخراج شده از سایت ضمیمه شد.',
                        attachments=csv_name
                    )
                    print("✉️ ایمیل با موفقیت ارسال شد.")
                except Exception as mail_err:
                    print(f"❌ خطا در ارسال ایمیل: {mail_err}")
            else:
                print("⚠️ دیتایی در جدول پیدا نشد.")
        else:
            print("❌ سایت لود نشد (احتمالاً سد کلودفلر یا اینترنت سرور).")
            page.get_screenshot('error.png')

    except Exception as e:
        print(f"❌ خطای بحرانی: {str(e)}")
    
    finally:
        if page:
            page.quit()
        print("--- پایان عملیات و آزادسازی حافظه ---")

# زمان‌بندی (هر ۱۰ دقیقه یکبار)
schedule.every(10).minutes.do(timing)

# اجرای اولین بار بلافاصله پس از شروع اسکریپت
timing()

while True:
    schedule.run_pending()
    time.sleep(1)
