# 
# Translater.py
# Translate program with google translator
# it is unlimit because using selenium
# Author : Ji-yong219
# Project Start:: 2020.12.18
# Last Modified from Ji-yong 2021.06.22
#

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from multiprocessing import Process, Manager, cpu_count
import time
import numpy as np

# 기사 제목 번역 메소드
def translateTitle(search, driver_url, chrome_options, dic):
    num_of_cpu = cpu_count()

    manager = Manager()
    result_dic = dict()
    
    title_list = [(k, v.get('title')) for k, v in dic.items()]
    total_length = len(title_list)
    title_list = np.array_split(np.array(title_list), num_of_cpu)
    
    for url,dic_ in dic.items():
        result_dic[url] = dic_
    
    processes = []
    result = manager.Queue()
    
    for idx in range(num_of_cpu):
        process = Process(target=translate_title_process,
            args=(
                idx,
                total_length,
                driver_url,
                chrome_options,
                title_list[idx],
                result_dic,
                search,
                result
            )
        )
        
        processes.append(process)
        process.start()
        
    
    for process in processes:
        process.join()
        
    while True:
        if result.empty():
            break
            
        data = result.get()
        
        dic.update(data)
    
    return result_dic.copy()


def translate_title_process(idx, total_length, driver_url, chrome_options, title_list, result_dic, search, result):
    driver = webdriver.Chrome(driver_url, chrome_options=chrome_options)
    
    url = 'https://translate.google.com/?sl=auto&tl=ko&op=translate'
    driver.get(url)

    try:
        element = WebDriverWait(driver, 7).until(
            # 로딩 될 때까지 대기
            EC.presence_of_element_located((By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div[2]/c-wiz/nav/a[2]/div[1]'))
        )
    except TimeoutException:
        print("타임아웃")

    left_field = driver.find_element_by_xpath('//*[@id="yDmH0d"]/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[2]/c-wiz[1]/span/span/div/textarea')
    right_field = None
    
    right_field = None

    length = len(title_list)
    count = 1

    for url, title in title_list:
        print(f'{count*(idx+1)} / {total_length}   {search}')
        count+=1
        
        before_trans = title
        
        print(before_trans)
        print('↓번역')
        
        left_field.send_keys(before_trans)
        time.sleep(1.5)
        right_field = driver.find_element_by_xpath('//*[@id="yDmH0d"]/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[2]/c-wiz[2]/div[5]/div/div[1]/span[1]/span')
        after_trans = right_field.text
        
        print(after_trans)
        result_dic[url]['title'] = after_trans
        temp = {}
        temp[url] = {}
        temp[url]['title'] = after_trans
        result.put(temp)
        left_field.clear()
        print('\n')
        
    driver.close()
    return

