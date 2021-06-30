# 
# NewyorktimesCrawler.py
# Web crawling program for https://www.nytimes.com/
# Author : Ji-yong219
# Project Start:: 2020.12.18
# Last Modified from Ji-yong 2021.06.23
#


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import datetime
import time
import json

import grequests

import sys
from tqdm import trange

from multiprocessing import  Manager, cpu_count

from utils.util import *
from utils.FeedbackCounter import FeedbackCounter
from crawlers.BaseCrawler import Crawler

class NTCrawler(Crawler):
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

    # 생성자
    def __init__(self, driver_url, chrome_options):
        self.chrome_options = chrome_options
        
        self.driver_url = driver_url

    # 기사 링크 수집 메소드
    def crawlLinks(self, search, start_date, end_date):
        self.news_queue = []
        self.driver = webdriver.Chrome(self.driver_url, chrome_options=self.chrome_options)
        self.url_num = 0
        start_date_ = datetime.date(int(start_date[:4]), int(start_date[4:6]), int(start_date[6:])) + datetime.timedelta(days=1)
        end_date_ = datetime.date(int(end_date[:4]), int(end_date[4:6]), int(end_date[6:]))# + datetime.timedelta(days=1)
        
        while True:
            news = None
            
            for single_date in daterange(start_date_, end_date_):
                this_date = single_date.strftime("%Y%m%d")
                self.url = f"https://www.nytimes.com/search?dropmab=true&startDate={this_date}&endDate={this_date}&query={search}&sort=oldest&types=article"
                print(f'{this_date} 하는 중 {self.url}', end='\t→\t')

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
                    
                    if link and link not in self.news_queue:
                        self.news_queue.append(link)
                        
                print(f'뉴스 {len(self.news_queue)}개 모음')
                    
            break


        with open('result/newyorktimes/urls_%s.txt'%(search), 'w', encoding='utf8') as f:
            f.writelines('\n'.join(self.news_queue))
        self.news_queue = []
        self.driver.close()

    def crawlNews(self, search, start_date, end_date):
        with open('result/newyorktimes/urls_%s.txt'%(search), 'r', encoding='utf8', newline='\n') as f:
            for row in f.readlines():
                row = row.replace('\n', '').replace('\r', '')
                self.news_queue.append(row)

        fbc = FeedbackCounter( len(self.news_queue) )

        headers = {'User-Agent':'Mozilla/5.0'}
        
        rs = (grequests.get(self.news_queue[i], headers=headers, callback=fbc.feedback) for i in trange(len(self.news_queue), file=sys.stdout, desc='get Grequest'))
        a = grequests.map(rs)
        
        # self.soup_list = [ (a[i].url,bs(a[i].content, 'html.parser')) for i in trange(len(a), file=sys.stdout, desc='get html parser from bs4') if a[i] is not None]


        for i in trange(len(a), file=sys.stdout, desc='get html parser from bs4'):
        # for idx, soup in enumerate(self.soup_list):
            soup = None

            if a[i] is not None:
                soup = (a[i].url,bs(a[i].content, 'html.parser'))

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
                print("기자 없어서 continue\t->", url)
                # continue
                
            if url[24:34].replace('/', '').isdigit():
                date = url[24:34].replace("/", "") + "130000"
            else:
                print("날짜 이상해서 continue")
                continue
            
            article = self.getArticle(soup)
            if article and article != "":
                # print("내용 : ", article[0].get_text()[:20])
                pass
            
            else:
                print("내용 없어서 continue")
                continue

            self.temp_data[url] = {
                'title':title[0].get_text(),
                'author':author,
                'date':date,
                'article':article[0].get_text()
            }
        
        print("다 긁은 개수 : ", len(self.temp_data))
        
        with open('result/newyorktimes/news_%s.json'%(search), 'w', encoding='utf8') as f:
            json.dump(self.temp_data, f, indent=4, sort_keys=True, ensure_ascii=False)

    def getTitle(self, soup):
        title = None
        try:
            title = soup.select('h1[data-test-id="headline"]') # newyorktimes


        except AttributeError as e:
            print(e)
            return None

        return title

    def getAuthor(self, soup):
        author = None
        try:
            author = soup.select('article[id="story"]') # newyorktimes
            author = author[0].findAll('span', {'class':'last-byline'})
            
            return author

        except AttributeError as e:
            return None
        
        

    def getDate(self, soup):
        date = None
        try:
            date = soup.select('article[id="story"]') # newyorktimes
            date = date[0].findAll('time')

        except AttributeError as e:
            return None

        return date

    def getArticle(self, soup):
        try:
            article = soup.select('section[name="articleBody"]') # newyorktimes

        except AttributeError as e:
            return None

        return article