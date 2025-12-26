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
def timing() :
  path_geckodriver = '/snap/bin/geckodriver'
  service_path = Service(path_geckodriver)
  bot_ertebati = webdriver.Firefox(service=service_path)


  ertebat = bot_ertebati.get('https://dexscreener.com/')
  wait = WebDriverWait(bot_ertebati , 10)
  data1 = bot_ertebati.find_element(By.CSS_SELECTOR , '.ds-dex-table')

    
  data_text = data1.text
  data_list = data_text.splitlines()
  titles = ['RANK','TOKEN',  'EXCHANGE' ,' FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']

  new_data = data_list[12:]

  dl_list = ['750','3','210','880','780','150','WP','720','V4','20','50','70','60' ,'CPMM', '180', '620', '80','100V3', 'V3', '200', 'V1' , '30' ,'OOPS', '100', '550','130' ,'CLMM','DLMM', '40', '600', '300', 'V2', '500',  '110', 'DYN' , 'DYN2', '/', '1000' , '10','310', '850', '120', '660', '510', '530']

  nd = []

  def ah (list2) :
    for asl in new_data :
      if asl not in list2 :
        nd.append(asl)
          
  list2 = dl_list
  result = ah(list2)    
  arzha = []
  for ia in range (0, len(nd), 15) :
    arz = nd[ia : ia +15]
    arzha.append(arz)
  pd= pandas.DataFrame(arzha , columns= titles)

  ls_con=[]
  def token_add() :
      path_geckodriver = '/snap/bin/geckodriver'
      service_path = Service(path_geckodriver)
      bot_ertebati = webdriver.Firefox(service=service_path)
      bot_ertebati.get('https://dexscreener.com/')
      bot_ertebati.implicitly_wait(20)
    
      source_site = bot_ertebati.page_source
    
    
      z=requests.get('https://dexscreener.com/')
      soup = BeautifulSoup(z.text , 'html.parser')
      y = soup.find_all('a' , class_= 'ds-dex-table-row ds-dex-table-row-top')
      t = r'" href="([^".]*[a-z0-9])"'
      v = re.findall(t, source_site)
    

      for i in v :
          if len(i) >= 20 :
              ls_con.append(i)

    
  token_add()
  if len(pd) == len(ls_con) :
      pd['CONTRACT ADDRESS']= ls_con 
  else:
      pd['CONTRACT ADDRESS'] = ls_con + ls_con[1]


  csvname = f'dexscrrener.csv'
  csvfile = pd.to_csv(csvname , index=False , encoding= 'utf-8')

  bot_ertebati.quit()

  #...send email

  ersal_konandeh = 'dexscreeneramirzamani@gmail.com'
  password = 'urcs rehx ttyt hzbv'
  file_ersali = csvname
  con = 'test'
  daryaft_konandeh = 'amirhosseinzamanifarsi@gmail.com'
  yag = yagmail.SMTP(ersal_konandeh , password)
  yagyag = yag.send(daryaft_konandeh ,con,file_ersali)
  print ('file ba movafaghiat ersal shod.')
schedule.every(1).minute.do(timing)
while True :
  schedule.run_pending()
  time.sleep(1)
  






