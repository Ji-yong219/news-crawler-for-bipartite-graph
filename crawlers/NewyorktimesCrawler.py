# 
# NewyorktimesCrawler.py
# Web crawling program for https://www.nytimes.com/
# Author : Ji-yong219
# Project Start:: 2020.12.18
# Last Modified from Ji-yong 2021.06.22
#


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen, Request
from urllib.request import HTTPError
import calendar, datetime
import time
import json

from Translator import Translator

import grequests
import requests
import asyncio
from functools import partial

import sys
from tqdm import trange

from multiprocessing import Process, Queue, Manager, cpu_count
import numpy as np

# from  googletrans import Translator

class Crawler:
    news_agency = None
    chrome_options = None
    driver = None
    url_num = 0
    url = ''
    news_url_list = []
    news_dic = {}
    viewed_news = []
    news_queue = []
    soup_list = []
    temp_data = {}
    loop = None
    
    start_date = datetime.date(2020, 11, 14)
    end_date = datetime.date(2021, 1, 14) # + 1일 해줘야함

    # 생성자
    def __init__(self, url, driver_url, chrome_options, news_agency):
        self.news_agency = news_agency
        self.url = url
        
        self.chrome_options = chrome_options
        
        self.driver_url = driver_url

    # 기사 링크 수집 메소드
    def crawlLinks(self, search):
        self.news_queue = []
        self.driver = webdriver.Chrome(self.driver_url, chrome_options=self.chrome_options)
        self.url_num = 0
        
        count = 0
        while True:
            if self.news_agency == 'us-wp':
                self.url = f'https://www.washingtonpost.com/newssearch/?query={search}&btn-search=&sort=Date&datefilter=60%%20Days&contenttype=Article&startat={self.url_num}'
                
            elif self.news_agency == 'us-nt':
                news = None
                
                for single_date in self.daterange(self.start_date, self.end_date):
                    this_date = single_date.strftime("%Y%m%d")
                    self.url = f"https://www.nytimes.com/search?dropmab=true&startDate={this_date}&endDate={this_date}&query={search}&sort=oldest&types=article"
                    print(f'{this_date} 하는 중', end='\t→\t')

                    while True:
                        self.driver.get(self.url)
                    
                        try:
                            element = WebDriverWait(self.driver, 60).until(
                                EC.presence_of_element_located((By.XPATH, '//ol[@data-testid="search-results"]')) 
                            )

                        except TimeoutException:
                            print("페이지 못받아온 타임아웃", end='\t')
                            
                        else:
                            break
                        
                    
                    
                    while True:
                        btn = None
                        
                        try:
                            btn = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, '//button[contains(text(), "Show More") and @data-testid="search-show-more-button"]'))
                            ).click()

                        except TimeoutException:
                            print("버튼 못찾은 타임아웃", end='\t')
                        
                        if btn is None:
                            break
                            
                        time.sleep(1)
                        
                    ol = self.driver.find_element_by_xpath('//ol[@data-testid="search-results"]')
                    news = ol.find_elements_by_tag_name('a')
                    
                    news = list(set(news))

                    for i in range(len(news)):
                        link = None

                        if news[i] is not None:
                            link = news[i].get_attribute('href')

                        if link is None:
                            continue
                            
                        elif "/search?" in link:
                            continue

                        link = link.replace('\n', '')
                        
                        if self.news_agency == 'us-nt' and link and link not in self.news_queue:
                            self.news_queue.append(link)
                            
                    print(f'뉴스 {len(self.news_queue)}개 모음')
                        
                break
                                
            elif self.news_agency == 'kr':
                self.url = f'https://search.daum.net/search?nil_suggest=btn&w=news&DA=STC&cluster=y&q={search}&sd=20200901000000&ed=20201220235959&period=u&p={self.url_num}'
                
            self.driver.get(self.url)

            try:
                
                if self.news_agency == 'us-wp':
                    element = WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div/div/div[2]/div')) 
                    )
                
                
                elif self.news_agency == 'kr':
                    element = WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="innerFooter"]/div[2]/address'))
                    )

            except TimeoutException:
                print("타임아웃")

            div, news = None, None

            if self.news_agency == 'kr':
                try:
                    if self.driver.find_element_by_xpath('//*[@id="noResult"]'):
                        break
                except Exception as e:
                    pass
                
                div = self.driver.find_element_by_xpath('//*[@id="mArticle"]/div/div[2]')
                news = bs(div.get_attribute('innerHTML'), 'html.parser').findAll('a', text='다음뉴스', class_='f_nb')
        
            elif self.news_agency == 'us-wp':
                div = self.driver.find_element_by_xpath('//*[@id="main-content"]/div/div/div[2]/div')
                news = div.find_elements_by_tag_name('a')

                if len(news)<20:
                    break
        

            news = list(set(news))

            for i in range(len(news)):
                link = None

                if self.news_agency == 'us-wp':
                    if search in news[i].text.lower():
                        link = news[i].get_attribute('href')

                elif self.news_agency == 'kr':
                    link = news[i]['href']

                if link is None:
                    continue

                link = link.replace('\n', '')
                if self.news_agency == 'us-wp' and link and link[:30] == "https://www.washingtonpost.com" and link not in self.news_queue:
                    self.news_queue.append(link)

                elif self.news_agency == 'kr' and link and link not in self.news_queue:
                    self.news_queue.append(link)
                    # count+=1

            if self.news_agency == 'us-wp':
                self.url_num += 20

            elif self.news_agency == 'kr':
                self.url_num += 1


        with open('./%s_urls_%s.txt'%(self.news_agency, search), 'w', encoding='utf8') as f:
            # for row in self.news_queue:
            #     f.writeline(row+'\n')
            f.writelines('\n'.join(self.news_queue))
        self.news_queue = []
        self.driver.close()

    def crawlNews(self, search):
        with open('./%s_urls_%s.txt'%(self.news_agency, search), 'r', encoding='utf8', newline='\n') as f:
            for row in f.readlines():
                row = row.replace('\n', '').replace('\r', '')
                self.news_queue.append(row)

        fbc = FeedbackCounter( len(self.news_queue) )

        headers = {'User-Agent':'Mozilla/5.0'}
        
        rs = (grequests.get(self.news_queue[i], headers=headers, callback=fbc.feedback) for i in trange(len(self.news_queue), file=sys.stdout, desc='get Grequest'))
        a = grequests.map(rs)
        
        self.soup_list = [ (a[i].url,bs(a[i].content, 'html.parser')) for i in trange(len(a), file=sys.stdout, desc='get html parser from bs4') if a[i] is not None]


        for idx, soup in enumerate(self.soup_list):
            if soup is None or len(soup)<2:
                continue

            url, soup = soup

            if soup is None:
                print("soup 없어서 continue")
                continue

            title = self.getTitle(soup)
            if title and title != "":
                # print("제목 : ", title[0].get_text())
                pass
            
            else:
                print("title 없어서 continue\t->", url)
                continue

            author = self.getAuthor(soup)
            if author and author != "":
                # print("기자 : ", author[0].get_text())
                author = author[0].get_text()
                pass
            
            else:
                author = "No-Author"
                # print("기자 없어서 continue\t->", url)
                # continue
                
                
            if self.news_agency == 'us-wp':# or 'nytimes.com/article' in url:
                date = self.getDate(soup)
                if date and date != "" and date != []:
                    date = date[0].get_text()
                    print(f'date : {date}')
                    
                    if "Updated" in date:
                        date = date.split("Updated")[0].replace("Published ", "").strip()
                        
                    if "a.m." in date or "p.m." in date:
                        date = date.split(" ")
                        date.insert(3, "at")
                        date = " ".join( date )
                        date = self.convert_date( date )
                        
                    else:
                        date = self.convert_date( date + " at 04:00 a.m. GMT+9")
                        
                    check_date = False
                    
                    for single_date in self.daterange(self.start_date, self.end_date):
                        if str(single_date).replace('-', '') == str(date)[:8]:
                            check_date = True
                            break
                            
                    if check_date: continue
                        
                else:
                    continue

            elif self.news_agency == 'us-nt':
                print()
                if url[24:34].replace('/', '').isdigit():
                    date = url[24:34].replace("/", "") + "130000"
                else:
                    print("날짜 이상해서 continue")
                    continue

            elif self.news_agency == 'kr':
                date = url.split('/')[-1]
            
            else:
                print("date 없어서 continue")
                continue
            
            article = self.getArticle(soup)
            if article and article != "":
                # print("내용 : ", article[0].get_text()[:20])
                pass
            
            else:
                print("내용 없어서 continue")
                continue

            if self.news_agency == 'us-wp' or self.news_agency == 'us-nt':
                self.temp_data[url] = {
                    'title':title[0].get_text(),
                    'author':author,
                    'date':date,
                    'article':article[0].get_text()
                }
                
            elif self.news_agency == 'kr':
                print(f'{idx}반복, {url}')
                self.temp_data[url] = {
                    'title':title[0].get_text(),
                    'author':author.get_text(),
                    'date':date,
                    'article':article[0].get_text()
                }
        
        print("다 긁은 개수 : ", len(self.temp_data))
        
        with open('%s_news_%s.json'%(self.news_agency, search), 'w', encoding='utf8') as f:
            json.dump(self.temp_data, f, indent=4, sort_keys=True, ensure_ascii=False)

    def get_num_month(self, str_month):
        for month_idx in range(1, 13):
            if str_month == calendar.month_name[month_idx]:
                if month_idx < 10:
                    return '0'+str(month_idx)
                else:
                    return str(month_idx)

            elif str_month == calendar.month_abbr[month_idx]:
                if month_idx < 10:
                    return '0'+str(month_idx)
                else:
                    return str(month_idx)

    def convert_date(self, original_date):
        data = original_date.split(' ')
        # print(f'data:{data}')
        month = self.get_num_month(data[0].replace('.', ''))
        dates = data[1].replace(',', '')
        year = data[2].replace(',', '')
        hour = data[4].split(':')[0]
        minute = data[4].split(':')[1]
        
        temp = '-'.join([str(i) for i in [year, month, dates, hour, minute, 0, data[5].replace('.', '').upper()]])
        converted_date = datetime.datetime.strptime(temp, '%Y-%m-%d-%I-%M-%S-%p') - datetime.timedelta(hours=-9)
        return converted_date.strftime('%Y%m%d%H%M')
        
        if int(dates) < 10 and len(dates)==1:
            dates = '0'+str(dates)
        
        if data[5][0] == 'p':
            time = str( int(time.split(':')[0])+12 ) + ':' + time.split(':')[1]
        
        if int(time.split(':')[0]) < 10 and len(time.split(':')[0])==1:
            time = '0'+str(time.split(':')[0]) + ':' + time.split(':')[1]
        
        if int(time.split(':')[1]) < 10 and len(time.split(':')[1])==1:
            time = time.split(':')[0]+':0'+str(time.split(':')[1])
        
        time = time.replace(':', '')

        return year+month+dates+time

    async def getSoup(self, url):
        global loop
        try:
            #html = urlopen(url)
            #soup = bs(html.read(), 'html.parser')

            print(f'{self.news_queue.index(url)+1} / {len(self.news_queue)} url 요청 중 ... ')

            request = partial(grequests.get, url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'})
            res = await loop.run_in_executor(None, request)
            
            print(f'{self.news_queue.index(url)+1} / {len(self.news_queue)} url 요청 완료 {url}')
            
            res = grequests.map([res], size=1)[0]
            print(res)

            if res is not None:
                res = res.content
                soup = await loop.run_in_executor(None, bs, res, 'html.parser')
                # soup = bs(res, 'html.parser')
                
            else:
                return None

        except HTTPError as e:
            print('HTTP Error!')
            print(e)
            return None
        '''
        except AttributeError as e:
            print('Attribute Error!')
            return None
        
        except Exception as e:
            return None
        '''
        return {url:soup}

    def getTitle(self, soup):
        title = None
        try:
            
            if self.news_agency == 'us-wp':
                title = soup.select('h1[data-qa="headline"]') # washingtonpost
            
            elif self.news_agency == 'us-nt':
                title = soup.select('h1[data-test-id="headline"]') # newyorktimes

            elif self.news_agency == 'kr':
                title = soup.select('h3[class="tit_view"]') # daum


        except AttributeError as e:
            print(e)
            return None

        return title

    def getAuthor(self, soup):
        author = None
        try:
            if self.news_agency == 'us-wp':
                author = soup.select('span[data-qa="author-name-wrapper"]') # washingtonpost
                
            elif self.news_agency == 'us-nt':
                author = soup.select('article[id="story"]') # newyorktimes
                author = author[0].findAll('span', {'class':'last-byline'})
                
                return author

            elif self.news_agency == 'kr':
                author = soup.select('span[class="info_view"]') # daum
                author = author[0].findAll('span', {'class':'txt_info'})

                if len(author)<2:
                    return None
                else:
                    return author[0]

        except AttributeError as e:
            return None
        
        

    def getDate(self, soup):
        date = None
        try:
            if self.news_agency == 'us-wp':
                date = soup.select('div[data-qa="timestamp"]') # washingtonpost
                
            if self.news_agency == 'us-nt':
                date = soup.select('article[id="story"]') # newyorktimes
                date = date[0].findAll('time')
            
            elif self.news_agency == 'kr':
                date = soup.select('span[class="info_view"]') # daum
                date = date[0].findAll('span', {'class':'num_date'})

        except AttributeError as e:
            return None

        return date

    def getArticle(self, soup):
        try:
            if self.news_agency == 'us-wp':
                article = soup.select('div[class="article-body"]') # washingtonpost
                
            elif self.news_agency == 'us-nt':
                article = soup.select('section[name="articleBody"]') # newyorktimes

            elif self.news_agency == 'kr':
                article = soup.select('div[class="article_view"]') # daum

        except AttributeError as e:
            return None

        return article

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + datetime.timedelta(n)




    # 기사 제목 번역 메소드
    def translateTitle(self, search):
        # trans = Translator(self.driver_url, self.chrome_options)

        num_of_cpu = cpu_count()

        
        manager = Manager()
        # result_dic = manager.dict()
        result_dic = dict()
        dic = {}

        with open(f'{self.news_agency}_news_{search}.json','r', encoding='utf8') as f:
            dic = json.load(f)
        
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
                    self.driver_url,
                    self.chrome_options,
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
            
        # for i in range(len(list(result))):
            # result_dic.add(result.get())
            
        while True:
            if result.empty():
                break
                
            data = result.get()
            
            dic.update(data)
        
        with open(f'{self.news_agency}_news_trans_{search}.json', 'w', encoding='utf8') as f:
            json.dump(result_dic.copy(), f, indent=4, sort_keys=True, ensure_ascii=False)


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


class FeedbackCounter:
    """Object to provide a feedback callback keeping track of total calls."""
    def __init__(self, all):
        self.counter = 1
        self.all = all

    def feedback(self, r, **kwargs):
        self.counter += 1
        print(f'{self.counter} / {self.all+1}, {r.url}')
        return r