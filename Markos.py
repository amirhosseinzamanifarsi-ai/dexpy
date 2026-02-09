from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import os

# --- تنظیمات ---
USE_PROXY = True 
# پورت 8118 مربوط به Privoxy است که تور را به HTTP تبدیل کرده
PROXY_ADDRESS = "127.0.0.1:8118" 
EMAIL_USER = 'dexscreeneramirzamani@gmail.com'
EMAIL_PASS = 'urcs rehx ttyt hzbv'
RECIPIENT = 'amirhosseinzamanifarsi@gmail.com'

def timing():
    print(f"\n--- شروع چرخه استخراج (نسخه HTTP Proxy): {time.strftime('%H:%M:%S')} ---")
    
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        
        if USE_PROXY:
            print(f"🛡️ اتصال از طریق Privoxy (تور تبدیل شده): {PROXY_ADDRESS}")
            co.set_proxy(PROXY_ADDRESS) # حالا چون HTTP است، DrissionPage ارور نمی‌دهد
        
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        page.get('https://dexscreener.com/', retry=3, interval=15)
        
        success = False
        for i in range(15):
            time.sleep(7)
            
            # چک کردن جدول
            if page.ele('.ds-dex-table', timeout=2):
                print("✅ جدول لود شد!")
                success = True
                break
            
            # کلیک روی کپچا
            if "verify" in page.title.lower() or "moment" in page.title.lower():
                print(f"⚠️ شناسایی کپچا (تلاش {i+1})...")
                btn = page.ele('@type=checkbox', timeout=2) or page.ele('text:Verify you are human', timeout=2)
                if btn:
                    btn.click(by_js=False)
                    print("👆 کلیک انجام شد.")
        
        if success:
            print("📊 استخراج داده‌ها...")
            time.sleep(10)
            table_raw = page.ele('.ds-dex-table')
            data_text = table_raw.text
            data_list = data_text.splitlines()

            # استخراج لینک‌ها
            links = page.eles('tag:a')
            contracts = [l.attr('href').split('/')[-1] for l in links if l.attr('href') and len(l.attr('href').split('/')[-1]) > 30]

            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
            clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]
            
            rows = [clean_data[i:i+15] for i in range(0, len(clean_data) - 14, 15)]

            if rows:
                df = pd.DataFrame(rows, columns=titles)
                if contracts:
                    unique_contracts = list(dict.fromkeys(contracts))
                    df['CONTRACT ADDRESS'] = (unique_contracts * (len(df)//len(unique_contracts)+1))[:len(df)]
                
                filename = f"dex_report_{time.strftime('%H%M')}.csv"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                try:
                    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)
                    yag.send(to=RECIPIENT, subject=f"Dex Report {time.strftime('%H:%M')}", attachments=filename)
                    print("📧 ایمیل ارسال شد.")
                    os.remove(filename)
                except Exception as e:
                    print(f"❌ خطا در ایمیل: {e}")
        else:
            print("❌ شکست در عبور از لایه‌های امنیتی.")
            page.get_screenshot('final_failed.png')

    except Exception as e:
        print(f"❌ خطای سیستم: {e}")
    finally:
        if page: page.quit()
        display.stop()

schedule.every(10).minutes.do(timing)
timing()
while True:
    schedule.run_pending()
    time.sleep(1)
