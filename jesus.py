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
        time.sleep(10)  # انتظار بیشتر برای لود اولیه
        
        # اسکرول برای فعال کردن لود داده‌ها
        print("در حال اسکرول کردن صفحه...")
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        
        # منتظر لود داده‌ها باشه (تا زمانی که ردیف‌های جدول ظاهر بشن)
        print("منتظر لود داده‌ها...")
        wait = WebDriverWait(driver, 60)
        
        try:
            # منتظر وجود حداقل یک ردیف جدول باشه
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'table tbody tr'))
            )
            print("✅ داده‌ها لود شدن!")
        except:
            print("❌ داده‌ها لود نشدن - امتحان روش‌های دیگه...")
            
            # امتحان روش‌های دیگه برای پیدا کردن جدول
            selectors_to_try = [
                'table.ds-dex-table',
                'table.ds-table',
                'table',
                '.ds-dex-table',
                '.ds-table',
                'div table',
                'table.dataTable',
            ]
            
            table_found = False
            for selector in selectors_to_try:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✅ با سلکتور '{selector}' {len(elements)} عنصر پیدا شد")
                        table_found = True
                        break
                except:
                    pass
            
            if not table_found:
                raise ValueError("هیچ جدولی پیدا نشد")
        
        # استخراج داده‌ها
        print("در حال استخراج داده‌ها...")
        
        # پیدا کردن جدول
        try:
            table = driver.find_element(By.TAG_NAME, "table")
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            
            if len(rows) < 5:  # حداقل 5 ردیف داده
                raise ValueError(f"داده کافی یافت نشد ({len(rows)} ردیف)")
            
            print(f"✅ {len(rows)} ردیف داده پیدا شد")
            
            # نمایش چند ردیف اول برای بررسی
            for i, row in enumerate(rows[:3]):
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells:
                    row_data = [cell.text for cell in cells]
                    print(f"ردیف {i+1}: {row_data}")
            
            # استخراج داده‌ها
            data_list = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_data = [cell.text for cell in cells]
                if row_data:  # فقط ردیف‌هایی که داده دارن
                    data_list.extend(row_data)
            
            # ادامه کد مثل قبل...
            titles = ['RANK','TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            new_data = data_list
            
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