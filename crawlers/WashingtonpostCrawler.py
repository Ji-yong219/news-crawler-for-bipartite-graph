# 
# WashingtonpostCrawler.py
# Web crawling program for https://washingtonpost.com
# Author : Ji-yong219
# Project Start:: 2020.12.18
# Last Modified from Ji-yong 2021.06.22
#

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup as bs
import datetime
import json

import grequests

import sys
from tqdm import trange

from utils.util import *
from utils.FeedbackCounter import FeedbackCounter
from crawlers.BaseCrawler import Crawler

class WPCrawler(Crawler):
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
    start_date = None
    end_date = None

    # 생성자
    def __init__(self, driver_url, chrome_options):
        self.chrome_options = chrome_options
        
        self.driver_url = driver_url

    # 기사 링크 수집 메소드
    def crawlLinks(self, search, start_date, end_date):
        self.news_queue = []
        self.driver = webdriver.Chrome(self.driver_url, chrome_options=self.chrome_options)
        self.url_num = 0
        is_end = False
        
        while True:
            if is_end:
                break

            self.url = f'https://www.washingtonpost.com/newssearch/?query={search}&btn-search=&sort=Date&datefilter=All%20Since%202005&contenttype=Article&startat={self.url_num}'
                
            print(f"크롤링시작 URL:{self.url}")
            self.driver.get(self.url)

            try:
                element = WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div/div/div[2]/div')) 
                )

            except TimeoutException:
                print("타임아웃")

            div, news = None, None

            div = self.driver.find_element_by_xpath('//*[@id="main-content"]/div/div/div[2]/div')
            news = div.find_elements_by_tag_name('a')

            if len(news)<20:
                break
        

            news = list(set(news))

            for i in range(len(news)):
                link = None

                if search in news[i].text.lower():
                    link = news[i].get_attribute('href')

                if link is None:
                    continue

                link = link.replace('\n', '')
                if link and link[:30] == "https://www.washingtonpost.com" and link not in self.news_queue:
                    print(f'link : {link}')
                    try:
                        index_ = link.index(f"/20")+1
                        date_ = link[index_:index_+10].replace('/', '')
                        date_ = datetime.date(int(date_[:4]), int(date_[4:6]), int(date_[6:]))
                        start_date_ = datetime.date(int(start_date[:4]), int(start_date[4:6]), int(start_date[6:]))
                        end_date_ = datetime.date(int(end_date[:4]), int(end_date[4:6]), int(end_date[6:]))
                        print(f'date_:{date_}\t\tstart_date_:{start_date_}\t\tend_date_:{end_date_}')

                    except ValueError:
                        print("value Error", link)
                        pass

                    else:
                        if start_date_ <= date_ and date_ <= end_date_:
                            self.news_queue.append(link)

                        elif date_ < start_date_:
                            is_end = True

                        else:
                            self.url_num += (date_ - end_date_).days*10

            self.url_num += 20

        with open('result/washingtonpost/urls_%s.txt'%(search), 'w', encoding='utf8') as f:
            f.writelines('\n'.join(self.news_queue))

        self.news_queue = []
        self.driver.close()

    def crawlNews(self, search, start_date, end_date):
        with open('result/washingtonpost/urls_%s.txt'%(search), 'r', encoding='utf8', newline='\n') as f:
            for row in f.readlines():
                row = row.replace('\n', '').replace('\r', '')
                self.news_queue.append(row)

        fbc = FeedbackCounter( len(self.news_queue) )

        headers = {'User-Agent':'Mozilla/5.0'}
        
        rs = (grequests.get(self.news_queue[i], headers=headers, callback=fbc.feedback) for i in trange(len(self.news_queue), file=sys.stdout, desc='get Grequest'))
        a = grequests.map(rs)
        
        self.soup_list = [ (a[i].url,bs(a[i].content, 'html.parser')) for i in trange(len(a), file=sys.stdout, desc='get html parser from bs4') if a[i] is not None]

        print(f'self.soup_list : {len(self.soup_list)}')

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
                pass
            
            else:
                author = "No-Author"
                print("기자 없어서 continue\t->", url)
                # continue
                
                
            date = self.getDate(soup)
            if date and date != "" and date != []:
                date = date[0].get_text()
                # print(f'date : {date}')
                
                if "Updated" in date:
                    date = date.split("Updated")[0].replace("Published ", "").strip()
                    
                else:
                    date = convert_date( date + " at 04:00 a.m. GMT+9")
                    
                check_date = False
                
                start_date_ = datetime.date(int(start_date[:4]), int(start_date[4:6]), int(start_date[6:]))
                end_date_ = datetime.date(int(end_date[:4]), int(end_date[4:6]), int(end_date[6:]))
                for single_date in daterange(start_date_, end_date_):
                    if str(single_date).replace('-', '') == str(date)[:8]:
                        check_date = True
                        break
                        
                if check_date: continue
                    
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

            self.temp_data[url] = {
                'title':title[0].get_text(),
                'author':author[0].get_text(),
                'date':date,
                'article':article[0].get_text()
            }
        
        print("다 긁은 개수 : ", len(self.temp_data))
        
        with open('result/washingtonpost/news_%s.json'%(search), 'w', encoding='utf8') as f:
            json.dump(self.temp_data, f, indent=4, sort_keys=True, ensure_ascii=False)

    def getTitle(self, soup):
        title = None
        try:
            title = soup.select('h1[data-qa="headline"]') # washingtonpost


        except AttributeError as e:
            print(e)
            return None

        return title

    def getAuthor(self, soup):
        author = None
        try:
            author = soup.select('span[data-qa="author-name"]') # washingtonpost
            author = soup.select('a[data-qa="author-name"]') if (author is None) or author == [] or author == "" else author

        except AttributeError as e:
            return None

        return author
     
    def getDate(self, soup):
        date = None
        try:
            date = soup.select('div[data-qa="timestamp"]') # washingtonpost

        except AttributeError as e:
            return None

        return date

    def getArticle(self, soup):
        try:
            article = soup.select('div[class="article-body"]') # washingtonpost

        except AttributeError as e:
            return None

        return article
