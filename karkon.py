import time
import random
import schedule
import subprocess
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import pandas as pd
import yagmail
import re
import signal
import sys
import subprocess

def is_tor_running():
    try:
        result = subprocess.run(["pgrep", "tor"], capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

if not is_tor_running():
    print("❌ Tor روشن نیست. لطفاً اجرا کنید: sudo systemctl start tor")
    exit(1)

# -----------------------------
# تنظیمات سیستمی
# -----------------------------
TOR_SERVICE = "tor"  # نام سرویس Tor در سیستم
GECKODRIVER_PATH = "/usr/local/bin/geckodriver"
LOG_FILE = "dexscreener.log"

# -----------------------------
# تابع لاگ‌گیری
# -----------------------------
def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")

# -----------------------------
# چک کردن فرآیند Tor
# -----------------------------
def is_tor_running():
    try:
        result = subprocess.run(
            ["pgrep", TOR_SERVICE],
            capture_output=True,
            text=True,
            timeout=5
        )
        return len(result.stdout.strip()) > 0
    except Exception:
        return False

# -----------------------------
# چک کردن فرآیند geckodriver قبلی
# -----------------------------
def kill_geckodriver():
    try:
        subprocess.run(
            ["pkill", "-f", "geckodriver"],
            capture_output=True,
            text=True,
            timeout=3
        )
    except Exception:
        pass

# -----------------------------
# راه‌اندازی Tor (اگر نباشد)
# -----------------------------
def ensure_tor():
    if not is_tor_running():
        log("Tor غیرفعال است. روشن می‌شود...")
        try:
            subprocess.run(["systemctl", "start", TOR_SERVICE], check=True)
            time.sleep(5)  # ده ثانیه برای راه‌اندازی
        except subprocess.CalledProcessError:
            log("❌ نتوانستیم Tor را روشن کنیم. لطفا دستی آن را روشن کنید.")
            return False
    return True

# -----------------------------
# راه‌اندازی مرورگر
# -----------------------------
def setup_driver():
    kill_geckodriver()  # اطمینان حاصل کنیم فرآیند قبلی قطع شده
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0"
    )
    
    # تنظیمات Tor
    options.set_preference("network.proxy.type", 1)
    options.set_preference("network.proxy.socks", "127.0.0.1")
    options.set_preference("network.proxy.socks_port", 9050)
    options.set_preference("network.proxy.socks_version", 5)
    options.set_preference("network.proxy.socks_remote_dns", True)
    
    # اضافه کردن تنظیمات امنیتی
    options.set_preference("privacy.trackingprotection.enabled", False)
    options.set_preference("privacy.resistFingerprinting", False)
    
    service = Service(GECKODRIVER_PATH)
    driver = webdriver.Firefox(service=service, options=options)
    return driver

# -----------------------------
# انتظار شبیه انسان
# -----------------------------
def human_like_wait():
    time.sleep(random.uniform(2, 5))

# -----------------------------
# استخراج داده
# -----------------------------
def extract_data():
    if not ensure_tor():
        log("❌ Tor روشن نیست. اسکریپت متوقف می‌شود.")
        return
    
    driver = None
    try:
        log("در حال راه‌اندازی مرورگر...")
        driver = setup_driver()
        driver.set_page_load_timeout(30)  # زمان بارگذاری صفحه
        driver.set_script_timeout(30)     # زمان اسکریپت

        url = "https://dexscreener.com/"
        log(f"در حال باز کردن: {url}")
        driver.get(url)
        human_like_wait()

        # انتظار برای جدول
        wait = WebDriverWait(driver, 45)  # افزایش زمان انتظار
        table = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ds-dex-table"))
        )
        human_like_wait()

        # رول کردن برای بارگذاری بیشتر
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        human_like_wait()

        # استخراج متن جدول
        raw_text = table.text
        lines = raw_text.splitlines()

        titles = [
            "RANK", "TOKEN", "EXCHANGE", "FULL NAME", "PRICE", "AGE",
            "TXNS", "VOLUME", "MAKERS", "5M", "1H", "6H", "24H",
            "LIQUIDITY", "MCAP"
        ]
        data_lines = lines[12:]

        skip_list = [
            "750", "3", "210", "880", "780", "150", "WP", "720", "V4", "20",
            "50", "70", "60", "CPMM", "180", "620", "80", "100V3", "V3",
            "200", "V1", "30", "OOPS", "100", "550", "130", "CLMM", "DLMM",
            "40", "600", "300", "V2", "500", "110", "DYN", "DYN2", "/", "1000",
            "10", "310", "850", "120", "660", "510", "530"
        ]
        filtered = [line for line in data_lines if line not in skip_list]

        tokens = []
        for i in range(0, len(filtered), 15):
            row = filtered[i:i+15]
            if len(row) == 15:
                tokens.append(row)

        df = pd.DataFrame(tokens, columns=titles)

        # استخراج CONTRACT ADDRESS به صورت دقیق
        source = driver.page_source
        contract_pattern = r'href="[^"]*0x[a-fA-F0-9]{40}[^"]*"'  # لینک‌های اتریوم
        matches = re.findall(contract_pattern, source)
        contracts = [re.search(r'0x[a-fA-F0-9]{40}', m).group() for m in matches if re.search(r'0x[a-fA-F0-9]{40}', m)]

        # حذف تکراری
        contracts = list(dict.fromkeys(contracts))

        log(f"تعداد آدرس قرارداد: {len(contracts)}")
        log(f"تعداد ردیف‌های جدول: {len(df)}")

        # اضافه کردن ستون CONTRACT ADDRESS
        if len(contracts) >= len(df):
            df["CONTRACT ADDRESS"] = contracts[: len(df)]
        else:
            df["CONTRACT ADDRESS"] = contracts + [""] * (len(df) - len(contracts))

        csv_name = "dexscreener_selenium.csv"
        df.to_csv(csv_name, index=False, encoding="utf-8")
        log(f"✅ فایل CSV ذخیره شد: {csv_name}")

        # ارسال ایمیل
        try:
            yag = yagmail.SMTP(
                "dexscreeneramirzamani@gmail.com",
                "urcs rehx ttyt hzbv"
            )
            yag.send(
                to="amirhosseinzamanifarsi@gmail.com",
                subject="DEXScreener - داده‌های به‌روز",
                contents=f"فایل داده‌های جدید DEXScreener\n\nتعداد ردیف: {len(df)}",
                attachments=csv_name
            )
            log("✅ ایمیل با موفقیت ارسال شد.")
        except Exception as e:
            log(f"❌ ارسال ایمیل ناموفق: {e}")

    except TimeoutException:
        log("❌ زمان بارگذاری صفحه بیش از حد طول کشید.")
    except WebDriverException as e:
        if "HTTPConnectionPool" in str(e):
            log("❌ اتصال به مرورگر (geckodriver) قطع شده. احتمالا Tor مشکل دارد.")
        else:
            log(f"❌ خطا در WebDriver: {e}")
    except Exception as e:
        log(f"❌ خطا غیرمنتظره: {e}")
    finally:
        if driver:
            driver.quit()
        kill_geckodriver()  # اطمینان حاصل کنیم فرآیند مرورگر قطع شده

# -----------------------------
# مدیریت سیگنال (Ctrl+C)
# -----------------------------
def signal_handler(sig, frame):
    log("دریافت Ctrl+C. سیستم خاموش می‌شود...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# -----------------------------
# برنامه‌ریزی
# -----------------------------
schedule.every(2).minutes.do(extract_data)  # هر 2 دقیقه یک بار

log("=== شروع برنامه ===")
log("هر 2 دقیقه یک بار اجرا می‌شود...")

while True:
    schedule.run_pending()
    time.sleep(30)  # اینجا مهم: 30 ثانیه صبر کن تا جلوی اجرا دوباره بگیری
