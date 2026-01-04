import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

def test_tor_connection():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # تنظیمات Tor
    options.set_preference("network.proxy.type", 1)
    options.set_preference("network.proxy.socks", "127.0.0.1")
    options.set_preference("network.proxy.socks_port", 9050)
    options.set_preference("network.proxy.socks_version", 5)
    options.set_preference("network.proxy.socks_remote_dns", True)
    
    service = Service("/usr/bin/geckodriver")
    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        print("در حال تست بارگذاری...")
        driver.get("https://check.torproject.org/")
        time.sleep(10)
        print(driver.page_source[:500])
        print("✅ Tor فعال است.")
    except Exception as e:
        print(f"❌ خطای اتصال: {e}")
    finally:
        driver.quit()

test_tor_connection()
