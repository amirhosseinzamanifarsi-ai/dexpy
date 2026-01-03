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
        
        # منتظر لود اولیه صفحه
        print("منتظر لود صفحه...")
        time.sleep(20)  # انتظار بیشتر
        
        # اسکرول برای فعال کردن لود داده‌ها
        print("در حال اسکرول کردن صفحه...")
        for i in range(15):  # اسکرول بیشتر
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        
        # اسکرول به بالا و پایین چند بار
        for i in range(5):
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
        
        # چک کردن وجود داده‌ها در HTML
        print("در حال بررسی وجود داده‌ها...")
        page_source = driver.page_source
        
        # چک کردن وجود کلمات کلیدی
        keywords = ['ds-dex-table', 'ds-table', 'tbody', 'tr', 'td', 'rank', 'token', 'price']
        found_keywords = []
        
        for keyword in keywords:
            if keyword.lower() in page_source.lower():
                found_keywords.append(keyword)
        
        print(f"✅ کلمات کلیدی پیدا شد: {found_keywords}")
        
        if len(found_keywords) < 3:
            raise ValueError("داده‌ها لود نشدن - کلمات کلیدی کافی پیدا نشد")
        
        # استخراج داده‌ها از متن صفحه
        print("در حال استخراج داده‌ها...")
        
        try:
            # پیدا کردن تمام متن صفحه
            body_text = driver.find_element(By.TAG_NAME, "body").text
            lines = body_text.split('\n')
            
            # فیلتر خطوطی که داده هستن
            data_lines = []
            for line in lines:
                line = line.strip()
                if line and len(line) > 3:  # خطوط خالی یا کوتاه رو حذف کن
                    data_lines.append(line)
            
            if len(data_lines) < 30:  # حداقل 30 خط داده
                raise ValueError(f"داده کافی یافت نشد ({len(data_lines)} خط)")
            
            print(f"✅ {len(data_lines)} خط داده پیدا شد")
            
            # نمایش چند خط اول برای بررسی
            print("چند خط اول داده:")
            for i, line in enumerate(data_lines[:10]):
                print(f"  {i+1}: {line}")
            
            # پردازش داده‌ها
            titles = ['RANK','TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            new_data = data_lines
            
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
            print(f"❌ خطا در استخراج داده‌ها: {e}")
            raise
            
    except Exception as e:
        print(f"❌ خطای کلی: {e}")
        
        # ذخیره اسکرین‌شات و HTML برای دیباگ
        if driver:
            try:
                driver.save_screenshot('debug_screenshot.png')
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print("✅ اسکرین‌شات و HTML صفحه برای دیباگ ذخیره شد")
            except:
                pass
        
        raise
    
    finally:
        if driver:
            driver.quit()
