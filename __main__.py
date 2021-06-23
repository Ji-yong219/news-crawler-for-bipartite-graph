from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)

import time
from selenium import webdriver

from konlpy.tag import Hannanum
from eunjeon import Mecab

han = Hannanum()#han.nouns(text)
mcb = Mecab()
morphology_analyzer = mcb

from crawlers.WashingtonpostCrawler import WPCrawler
from crawlers.NewyorktimesCrawler import NTCrawler
from crawlers import BigKindsCrawler

from utils.Translator import translateTitle
# import KrCrawler
# import KrCrawler2
# from Translator import Translator
import json
from datetime import datetime
from collections import Counter

import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from pandas import DataFrame as df
import numpy as np

import numba
from tqdm import trange

import sys
sys.setrecursionlimit(5000)

import nltk, re
nltk.download('punkt')

import matplotlib.font_manager as fm 
font_path = 'C:/Users/JY/AppData/Local/Microsoft/Windows/Fonts/BMJUA_ttf.ttf' 
fontprop = fm.FontProperties(fname=font_path, size=24) 
plt.rcParams['font.family'] = 'NanumGothic'




# @numba.jit(forceobj=True)
def make_bipartite_graph(news_us, news_kr, day, noun):
    us_title = []
    kr_title = []
    result = {}
    
    #---------------------------- title 
    temp_us = list(news_us.keys())
    for url in temp_us:
        us_title.append([url, news_us.get(url).get('title'), news_us.get(url).get('date')])

    temp_kr = list(news_kr.keys())
    for url in temp_kr:
        kr_title.append([url, news_kr.get(url).get('title'), news_kr.get(url).get('date')])
    #----------------------------

    #---------------------------- 형태소 분석
    for i in range(len(us_title)):
        us_title[i][1] = morphology_analyzer.nouns(us_title[i][1])
    
    for i in range(len(kr_title)):
        kr_title[i][1] = morphology_analyzer.nouns(kr_title[i][1])
    #----------------------------

    #----------------------------
    temp = []

    c = 0


    for idx in trange(len(us_title), file=sys.stdout, desc='make bipartite graph'):
    # for idx in range(len(us_title)):
        i = us_title[idx]
        
        for j in kr_title:
            count = 0

            # 년도+월+일+시+분
            time_us = datetime(int(i[2][0:4]), int(i[2][4:6]), int(i[2][6:8]), int(i[2][8:10]), int(i[2][10:12]))
            time_kr = datetime(int(j[2][0:4]), int(j[2][4:6]), int(j[2][6:8]), int(j[2][8:10]), int(j[2][10:12]))
            
            # 국내기사 제목 명사 수만큼 반복
            for k in range(len(j[1])):
                # 해외기사가 나오고 국내기사 나오기까지 기간 밖일 경우 예외
                if abs((time_kr - time_us).days) > day:
                    break
                
                # 같은 명사가 있을 경우 count 증가
                if j[1][k] in j[1]:
                    count += 1


            # 명사 수가 기준 이상일 경우 연관 지음
            if count >= noun:
                temp.append([i[0], j[0]])
                kr_title.remove(j) # 중복 제거를 위해 해당 국내기사 제거
                
        c+=1
        # print(f'이분그래프 노드 생성 {c}개 / {len(us_title)} 완료   kr: {len(kr_title)}')

    temp2 = []
    #----------------------------
    
    for i in temp:
        if len(temp2) == 0 or i[0] != temp2[-1][0]:
            temp2.append(i)
        else:
            temp2[-1].append(i[1])
            
            
    for i in temp2:
        result[i[0]] = i[1:]

    G = nx.Graph() # Create a graph

    date_list = []
    for k1, v1 in result.items():
        for i in v1:
            G.add_edge(k1, i)
            
    return result, G
    
def info_time(dic, us_news, kr_news):
    dic_key = dic.keys()
    info_term_time = []

    date_dic = {}

    for i in dic_key:
        temp_time = [x.split('.')[1] for x in dic[i]]

        if len(temp_time) > 1:
            temp_time.sort()
            sum_time = 0

            for j in temp_time:
                '''
                j = kr_news[j]['date']
                year_ = int(j[:4])
                mon_ = int(j[4:6])
                day_ = int(j[6:8])
                '''
                hour_ = int(j[8:10])
                min_ = int(j[10:12])
                sec_ = int(j[12:14])
                sum_time += hour_*60*60 + min_*60 + sec_
            avg_time = sum_time / len(temp_time)

            end_year = temp_time[-1][:4]
            end_mon = temp_time[-1][4:6]
            end_day = temp_time[-1][6:8]
            end_hour = temp_time[-1][8:10]
            end_min = temp_time[-1][10:12]
            # end_sec = temp_time[-1][12:14]
            end_ = ''.join([str(i) for i in [end_year, end_mon, end_day, end_hour, end_min]])

            start_year = temp_time[0][:4]
            start_mon = temp_time[0][4:6]
            start_day = temp_time[0][6:8]
            start_hour = temp_time[0][8:10]
            start_min = temp_time[0][10:12]
            # start_sec = temp_time[0][12:14]
            start_ = ''.join([str(i) for i in [start_year, start_mon, start_day, start_hour, start_min]])

            diff = (datetime(int(end_year), int(end_mon), int(end_day), int(end_hour), int(end_min))  -  datetime(int(start_year), int(start_mon), int(start_day), int(start_hour), int(start_min))).total_seconds()
            info_term_time.append([i, us_news[i]['title'], us_news[i]['date'], start_, end_, diff, avg_time])

            this_date = us_news[i]['date'][:8]

            if this_date in date_dic.keys():
                date_dic[this_date].append(avg_time)
            else:
                date_dic[this_date] = [avg_time]

    for k, v in date_dic.items():
        date_dic[k] = round(np.mean(v)/3600, 1)

    return date_dic

    # dataframe = df(info_term_time, columns=['URL', 'Title', '미국기사 시간', '처음 한국기사 시간', '마지막 한국기사 시간', 'diff', '평균'])
    # dataframe.to_csv('Task2.csv', encoding='cp949')

def csv(hubs, authorities, us_news, kr_news):
    #url, title, us/kr, authorities, hubs
    info = []
    for i in hubs.keys():
        if i in us_news.keys():
            info.append([i, us_news[i]['title'], 0, hubs[i], authorities[i]])

        elif i in kr_news.keys():
            info.append([i, kr_news[i]['title'], 1, hubs[i], authorities[i]])
        
    dataframe = df(info, columns = ['url', 'title', 'us : 0 / kr : 1', 'hub score', 'authorities score'])



    dataframe.to_csv('Task1-2.csv')


def get_top_nouns(nouns, top):
    count = Counter(nouns)

    noun_list = count.most_common(top)

    return noun_list

def get_clean_words(text, stopwords):
    clean_words = [] 
    for word in nltk.tokenize.word_tokenize(text): 
        if word not in stopwords: #불용어 제거
            clean_words.append(word)

    return clean_words


if __name__ == "__main__":
    wp_crawl_run = True
    nt_crawl_run = False
    kr_crawl_run = False
    make_bipartite_img = False

    task1_1_run = False # 연관 빈도수 그래프
    task1_2_run = False # 히트 알고리즘
    task2_run = False # 외국기사 나오고 한국기사 날짜
    task3_run = False
    task4_run = False

    word_bipartite_run = False # 내가 따로 한거, 아직 ㄴ



    # 크롬 드라이버 링크
    driver_url = 'D:\\chromedriver.exe'

    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--privileged')
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # selenium으로 크롤링하여 저장된 링크를 가지고 requests로 다시 크롤링하여 json으로 저장
    # kr은 requests로 동기식, us는 grequests와 async로 비동기식 (kr은 비동기가 안먹힘(다음뉴스 500 오류))

    search1 = "trump"
    search2 = "biden"
    search1_kr = "트럼프"
    search2_kr = "바이든"
    start_date = "20201114"
    end_date = "20210113"

    if wp_crawl_run:
        # 크롤러 객체 생성
        wp_crawler = WPCrawler(driver_url, chrome_options)

        # wp_crawler.crawlLinks(search1, start_date, end_date) # 링크 크롤링(selenium)
        wp_crawler.crawlNews(search1, start_date, end_date) # 뉴스 크롤링(async+grequest+bs4)

        dic = {}

        with open(f'result/washingtonpost/news_{search1}.json','r', encoding='utf8') as f:
            dic = json.load(f)
            
        result_dic = translateTitle(search1, driver_url, chrome_options, dic) # 구글 번역(selenium)

        with open(f'result/washingtonpost/news_trans_{search1}.json', 'w', encoding='utf8') as f:
            json.dump(result_dic, f, indent=4, sort_keys=True, ensure_ascii=False)
            

            
        wp_crawler.crawlLinks(search2, start_date, end_date) # 링크 크롤링(selenium)
        wp_crawler.crawlNews(search2, start_date, end_date) # 뉴스 크롤링(async+grequest+bs4)

        dic = {}

        with open(f'result/washingtonpost/news_{search2}.json','r', encoding='utf8') as f:
            dic = json.load(f)
            
        result_dic = translateTitle(search2, driver_url, chrome_options, dic) # 구글 번역(selenium)

        with open(f'result/washingtonpost/news_trans_{search2}.json', 'w', encoding='utf8') as f:
            json.dump(result_dic, f, indent=4, sort_keys=True, ensure_ascii=False)




    if nt_crawl_run:
        # 크롤러 객체 생성
        nt_crawler = NTCrawler(driver_url, chrome_options)

        nt_crawler.crawlLinks(search1, start_date, end_date) # 링크 크롤링(selenium)
        nt_crawler.crawlNews(search1, start_date, end_date) # 뉴스 크롤링(async+grequest+bs4)

        dic = {}

        with open(f'result/newyorktimes/news_{search1}.json','r', encoding='utf8') as f:
            dic = json.load(f)
            
        result_dic = translateTitle(search1, driver_url, chrome_options, dic) # 구글 번역(selenium)

        with open(f'result/newyorktimes/news_trans_{search1}.json', 'w', encoding='utf8') as f:
            json.dump(result_dic, f, indent=4, sort_keys=True, ensure_ascii=False)
            
            
        nt_crawler.crawlLinks(search2, start_date, end_date) # 링크 크롤링(selenium)
        nt_crawler.crawlNews(search2, start_date, end_date) # 뉴스 크롤링(async+grequest+bs4)

        dic = {}

        with open(f'result/newyorktimes/news_{search2}.json','r', encoding='utf8') as f:
            dic = json.load(f)
            
        result_dic = translateTitle(search2, driver_url, chrome_options, dic) # 구글 번역(selenium)

        with open(f'result/newyorktimes/news_trans_{search2}.json', 'w', encoding='utf8') as f:
            json.dump(result_dic, f, indent=4, sort_keys=True, ensure_ascii=False)



    if kr_crawl_run:
        # # 최신 빅카인즈 + 동적 크롤러 (국내 언론)

        BigKindsCrawler.crawl(search1_kr, start_date, end_date)
        BigKindsCrawler.crawl(search2_kr, start_date, end_date)

    # 크롤링하여 저장된 json을 불러와서 이분그래프 생성

    trump_kr = {}
    biden_kr = {}
    trump_us = {}
    biden_us = {}

    with open('result/bigkinds/news_트럼프.json', 'r', encoding='utf8') as f:
        trump_kr = json.load(f)
        
    with open('result/bigkinds/news_바이든.json', 'r', encoding='utf8') as f:
        biden_kr = json.load(f)
        
    with open(f'result/washingtonpost/news_trans_trump.json', 'r', encoding='utf8') as f:
        trump_us = json.load(f)
        
    with open(f'result/washingtonpost/news_trans_biden.json', 'r', encoding='utf8') as f:
        biden_us = json.load(f)
        
    # with open(f'result/newyorktimes/news_trans_trump.json', 'r', encoding='utf8') as f:
    #     trump_us = json.load(f)
        
    # with open(f'result/newyorktimes/news_trans_biden.json', 'r', encoding='utf8') as f:
    #     biden_us = json.load(f)

    print(f'trump: {len(trump_us)}')
    print(f'biden: {len(biden_us)}')
    print(f'트럼프: {len(trump_kr)}')
    print(f'바이든: {len(biden_kr)}')

    us_news = {}
    kr_news = {}
    dic_t, cbg_t, dic_b, cbg_b = None, None, None, None


    if task1_1_run:
        # 이분그래프 생성 (networkx)
        dic_t, cbg_t = make_bipartite_graph(trump_us, trump_kr, 2, 3)
        dic_b, cbg_b = make_bipartite_graph(biden_us, biden_kr, 2, 3)

    dic, cbg, first_partition_nodes = None, None, None

    if task1_2_run or task2_run or task3_run or task4_run or word_bipartite_run :
        us_news.update(trump_us)
        us_news.update(biden_us)
        kr_news.update(trump_kr)
        kr_news.update(biden_kr)
        
        dic, cbg = make_bipartite_graph(us_news, kr_news, 2, 3)

        first_partition_nodes = list(dic.keys())

    # 전체 이분그래프
    if make_bipartite_img:
        mode = 2

        if mode == 1:
            first_partition_nodes = list(dic.keys())
            # larger figure size
            plt.figure(1, figsize=(50,50)) 

            nx.draw_networkx(
                cbg,
                with_labels=True,
                node_size=20,
                font_size=10,
                pos = nx.drawing.layout.bipartite_layout(cbg, first_partition_nodes), 
                width = 1) # Or whatever other display options you like

            plt.show()
            plt.savefig(f"{us_platform}_graph.png") # Save to a PNG file

        elif mode == 2:
            first_partition_nodes = list(dic_t.keys())
            # larger figure size
            plt.figure(1, figsize=(50,50)) 

            nx.draw_networkx(
                cbg_t,
                with_labels=True,
                node_size=20,
                font_size=10,
                pos = nx.drawing.layout.bipartite_layout(cbg_t, first_partition_nodes), 
                width = 1) # Or whatever other display options you like

            # plt.show()
            plt.savefig("graph_t.png") # Save to a PNG file

            first_partition_nodes = list(dic_b.keys())
            # larger figure size
            plt.figure(1, figsize=(50,50)) 

            nx.draw_networkx(
                cbg_b,
                with_labels=True,
                node_size=20,
                font_size=10,
                pos = nx.drawing.layout.bipartite_layout(cbg_b, first_partition_nodes), 
                width = 1) # Or whatever other display options you like

            plt.show()
            # plt.savefig("graph_b.png") # Save to a PNG file
            plt.savefig(f"{us_platform}_bipartite_graph.png") # Save to a PNG file



    # Task 1-1

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            plt.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')

    def min_max_normalize(lst, max_, min_):
        normalized = []
        
        for value in lst:
            # normalized_num = (value - min(lst)) / (max(lst) - min(lst))
            normalized_num = ((value - min_) / (max_ - min_))
            normalized_num = round(normalized_num, 2)
            normalized.append(normalized_num)
        
        return normalized

    from pandas.plotting import table

    if task1_1_run:
        plt.clf()
        print('Task1-1 시작')
        bar_mode = False
        normalize_mode = True


        task1_1_trump = {}
        temp = sorted( dic_t.items(), reverse=False, key=( lambda i : int(trump_us[i[0]]['date']) ) )

        for k, v in temp:
            date = trump_us[k]['date'][:8]
            if date in task1_1_trump.keys():
                task1_1_trump[date] = {'val':( round(task1_1_trump.get(date).get('val')+len(v) / 2, 1))}

            else:
                task1_1_trump[date] = {'val':len(v)}


        task1_1_biden = {}
        temp = sorted( dic_b.items(), reverse=False, key=( lambda i : int(biden_us[i[0]]['date']) ) )

        for k, v in temp:
            date = biden_us[k]['date'][:8]
            if date in task1_1_biden.keys():
                task1_1_biden[date] = {'val':( round(task1_1_biden.get(date).get('val')+len(v) / 2, 1))}

            else:
                task1_1_biden[date] = {'val':len(v)}


        t_day = list(task1_1_trump.keys())
        t_n = []

        for i in t_day:
            t_n.append(task1_1_trump[i]['val'])

        b_day = list(task1_1_biden.keys())
        b_n = []

        for i in b_day:
            b_n.append(task1_1_biden[i]['val'])

        temp = [i for i in t_day] + [i for i in b_day]
        temp = list(set(temp))
        temp.sort()

        for i in temp:
            if i not in t_day:
                t_day.insert(temp.index(i), i)
                t_n.insert(temp.index(i), 0)

            if i not in b_day:
                b_day.insert(temp.index(i), i)
                b_n.insert(temp.index(i), 0)

        if normalize_mode:
            max_ = max(t_n + b_n)
            min_ = min(t_n + b_n)
            t_n = min_max_normalize(t_n, max_, min_)
            b_n = min_max_normalize(b_n, max_, min_)


        all_day = list(set(t_day+b_day))
        all_day.sort()

        labels = [f'{i[4:6]}.{i[6:]}' for i in all_day]
        x = np.arange(len(labels))  # the label locations

        bar_width = 0.4
        rects1 = None
        rects2 = None

        if bar_mode:
            rects1 = plt.bar(x-bar_width/2, t_n, bar_width, color='r', label="Trump", align='center')
            rects2 = plt.bar(x+bar_width/2, b_n, bar_width, label="Biden", align='center')

        else:
            plt.plot([f'{i[4:6]}.{i[6:]}' for i in t_day], t_n, marker='o',color='red', label="Trump")
            plt.plot([f'{i[4:6]}.{i[6:]}' for i in b_day], b_n, marker='s', label="Biden")

        table_contents = [
                    ['`20.11.17', '아프간 이라크 추가 철군, 모더나 백신 개발'],
                    ['`20.11.21', '트럼프장남 코로나확진, 트럼프그룹 탈세의혹'],
                    ['`20.12.01', '트럼프 측근들 취임식 참석 설 득중, 바이든 애리조나 승리'],
                    ['`20.12.03', '트럼프백신 영국에 선두 뺏겨, 트럼프 선거조작 연설'],
                    ['`20.12.12', '미국 FDA 백신 긴급 승인, 24시간내 접종 시작'],
                    ['`20.12.15', '트럼프 법무장관 해임'],
                    ['`20.12.19', '모더나 백신 승인'],
                    ['`20.12.23', '트럼프, 러시아 스캔들 연루 범죄자 무더기 사면'],
                    ['`21.01.07', '트럼프 지지자들 의회 난입'],
                    ['`21.01.09', '트럼프 트위터 계정 영구 정지, 취임식 가지 않겠다 선언'],
                    ['`21.01.13', '의회, 트럼프 탄핵 추진']
        ]

        # the_table = plt.table(cellText=table_contents,
        #                   colLabels=['Date', 'Event'],
        #                   loc='top', colWidths=[0.2, 0.2])

        plt.title('날짜별 연관기사 빈도수 그래프', fontproperties=fontprop)
        plt.ylabel('연관기사 빈도수', fontproperties=fontprop)
        plt.xlabel('날짜', fontproperties=fontprop)

        plt.xticks(x, labels, rotation=45)
        plt.legend(loc='upper left', fontsize=16)


        # 데이터값 라벨링
        if bar_mode:
            autolabel(rects1)
            autolabel(rects2)

        else:
            h = max(t_n+b_n) / (10 ** len(str(max(t_n))))

            for i, v in enumerate([f'{i[4:6]}.{i[6:]}' for i in t_day]):
                plt.text(v, t_n[i]+h, t_n[i], fontsize = 8, color='black')

            for i, v in enumerate([f'{i[4:6]}.{i[6:]}' for i in b_day]):
                plt.text(v, b_n[i]+h, b_n[i], fontsize = 8, color='black')

        # plt.tight_layout()
        # plt.savefig('Task1-1.png')
        
            z1 = np.array(t_n)
            z2 = np.array(b_n)
            plt.fill_between(labels, t_n, b_n, where=z1>z2, color='red', interpolate=True)
            plt.fill_between(labels, b_n, t_n, where=z2>z1, color='blue', interpolate=True)

        plt.show()
        plt.savefig(f"{us_platform}_task1-1.png") # Save to a PNG file
        print('Task1-1 종료')
    # 


    # Task 1-2
    import operator
    import dataframe_image as dfi

    def hub_authorities(G):
        return nx.hits(G, max_iter=500)

    if task1_2_run:
        plt.clf()
        print('Task1-2 시작')

        nx.draw_networkx(
            cbg,
            with_labels=True,
            node_size=20,
            font_size=10,
            pos = nx.drawing.layout.bipartite_layout(cbg, first_partition_nodes), 
            width = 1) # Or whatever other display options you like

        hubs, authorities = hub_authorities(cbg)
        csv(hubs, authorities, us_news, kr_news)


        for i in list(hubs.keys()):
            if "washingtonpost" in i or "nytimes" in i:
                hubs[us_news[i]['title']] = hubs.pop(i)
                
            else:
                hubs[kr_news[i]['title']] = hubs.pop(i)
                
        for i in list(authorities.keys()):
            if "washingtonpost" in i or "nytimes" in i:
                authorities[us_news[i]['title']] = authorities.pop(i)
            else:
                authorities[kr_news[i]['title']] = authorities.pop(i)

        hubs = sorted(hubs, key=operator.itemgetter(1))
        authorities = sorted(authorities, key=operator.itemgetter(1)) 

        hubs_ = df([str(x.encode('utf-8')) for x in hubs], columns=['title'])
        authorities_ = df([str(x.encode('utf-8')) for x in authorities], columns=['title'])
        hubs_.index += 1
        authorities_.index += 1

        # dfi.export(df(hubs[:20]), f'{us_platform}_Task1-2_hub_score.png', max_rows=-1)
        # dfi.export(df(authorities[:20]), f'{us_platform}Task1-2_authorities_score.png', max_rows=-1)
        dfi.export(df([x.encode('utf-8') for x in hubs[:20]]), 'Task1-2_hub_score.png', max_rows=-1)
        dfi.export(df([x.encode('utf-8') for x in authorities[:20]]), 'Task1-2_authorities_score.png', max_rows=-1)


    # Task 2
    if task2_run:
        plt.clf()
        print('Task2 시작')
        date_dic = info_time(dic, us_news, kr_news)

        bar_mode = True

        date_list = sorted( date_dic.items(), reverse=False, key=( lambda i : i[0] ) )


        labels = [f'{i[0][4:6]}.{i[0][6:]}' for i in date_list]
        x = np.arange(len(date_list))  # the label locations

        bar_width = 0.4
        rects = None

        if bar_mode:
            rects = plt.bar(x, [i[1] for i in date_list], bar_width, align='center')

        else:
            plt.plot([f'{i[4:6]}.{i[6:]}' for i in b_day], b_n, marker='o', label="Biden")

        plt.title('날짜별 미국기사와 한국기사 시차 평균', fontproperties=fontprop)
        plt.ylabel('시차 평균(시간)', fontproperties=fontprop)
        plt.xlabel('날짜', fontproperties=fontprop)

        plt.xticks(x, labels, rotation=45)
        # plt.legend(loc='upper left')


        # 데이터값 라벨링
        if bar_mode:
            autolabel(rects)
            pass

        else:
            h = max(t_n+b_n) / (10 ** len(str(max(t_n))))

            for i, v in enumerate([f'{i[4:6]}.{i[6:]}' for i in t_day]):
                plt.text(v, t_n[i]+h, t_n[i], fontsize = 8, color='black')

        # plt.tight_layout()
        plt.savefig(f'{us_platform}_Task2.png')

        plt.show()
        print('Task2 종료')
    # 

    # Task 3
    if task3_run:
        plt.clf()
        print('Task3 시작')
        normalize_mode = True
        companys_dic = {}

        for v in dic.values():
            for news in v:
                company = kr_news.get(news).get('company')

                if company in companys_dic.keys():
                    companys_dic[company] += 1

                else:
                    companys_dic[company] = 1

        companys = sorted(companys_dic.items(), reverse=True, key=(lambda x : int(x[1])) )
        top_10_companys = companys[:10]

        target = companys
        # target = top_10_companys

        
        labels = [i[0] for i in target]
        x = np.arange(len(labels))  # the label locations

        rects = plt.bar(x, [i[1] for i in target], align='center')
        
        plt.title('국내 언론사 빈도수 순위', fontproperties=fontprop)
        plt.ylabel('빈도수', fontproperties=fontprop)
        plt.xlabel('언론사', fontproperties=fontprop)

        plt.xticks(x, labels, rotation=30, fontsize=12)
        # plt.legend(loc='upper left')


        # 데이터값 라벨링
        autolabel(rects)

        # plt.tight_layout()
        plt.savefig(f'{us_platform}_Task3.png')
        plt.show()
        print('Task3 종료')

    from wordcloud import WordCloud
    def make_wc(d, filename):
        wordcloud = WordCloud(font_path=font_path, background_color='white',\
                        max_words=200, max_font_size=200, height=700, width=900)#.generate(text)

        wordcloud = wordcloud.generate_from_frequencies(frequencies=d)

        plt.figure() 
        plt.imshow(wordcloud, interpolation='lanczos') #이미지의 부드럽기 정도
        plt.axis('off') #x y 축 숫자 제거
        plt.savefig(filename+'-wordcloud.png', dpi=300)


    # Task 4
    if task4_run:
        plt.clf()
        stopwords = []
        with open('한글불용어.txt', 'r', encoding='utf8') as f:
            stopwords = f.read().split('\n')

        # trans = Translator(driver_url, chrome_options)

        peak_dic = {
            '20201117':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]},
            '20201121':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]},
            '20201201':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]},
            '20201203':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]},
            '20201212':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]},
            '20201215':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]},
            '20201219':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]},
            '20201223':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]},
            '20210107':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]},
            '20210109':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]},
            '20210113':{'us':0, 'kr':0, 'us_noun':[], 'kr_noun':[]}
        }



        for peak in peak_dic.keys():
            for k, v in dic.items():
                if us_news[k]['date'][:8] == peak:
                    peak_dic[ peak ]['us'] += 1
                    peak_dic[ peak ]['kr'] += len(v)

                    kr_noun = []
                    for news in v:
                        kr_noun += han.nouns( kr_news[news]['article'] )


                    #영어 본문 번역
                    # us_trans_article = trans.translate( us_news[k]['article'] )

                    # peak_dic[ peak ]['us_noun'] += han.nouns( us_trans_article )
                    peak_dic[ peak ]['kr_noun'] += kr_noun

            # word_list = pd.Series(peak_dic[ peak ]['us_noun'])
            # us_result = word_list.value_counts().head(20)
            # us_result = us_result.to_dict()
            # make_wc(us_result, peak+'us')
            

            # 특수문자와 불용어 제거
            
            kr_text = ' '.join(peak_dic[ peak ]['kr_noun'])
            # kr_text = re.sub('[0-9]+', '', kr_text)
            # kr_text = re.sub('[A-Za-z]+', '', kr_text)
            kr_text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ·!』\\‘’“”|\(\)\[\]\<\>`\'…》©]', '', kr_text)
            kr_text = ' '.join(kr_text.split())
            
            clean_kr_list = get_clean_words(kr_text, stopwords)

            word_list = pd.Series(clean_kr_list)
            # word_list = pd.Series(peak_dic[ peak ]['kr_noun'])
            kr_result = word_list.value_counts().head(20)
            # print(peak)
            # for i in kr_result.keys():
                # print(i)
            # print('\n\n')
            kr_result = kr_result.to_dict()
            # make_wc(kr_result, peak+'kr')

        print('Good')






    if word_bipartite_run:
        top_k_100_list = list(dic.keys())

        length = len(top_k_100_list)-1

        for i in range(length):
            for j in range(length-i):
                if len(dic.get(top_k_100_list[j])) < len(dic.get(top_k_100_list[j+1])):
                    top_k_100_list[j], top_k_100_list[j+1] = top_k_100_list[j+1], top_k_100_list[j]

        top_k_100_list = top_k_100_list[:100]



        trans = Translator(driver_url, chrome_options)

        top_k_100_dic = {}

        for idx, us_url in enumerate(top_k_100_list):
            print(f"{idx+1}번 째 진행 중")
            us_text = us_news.get(us_url).get('title') + trans.translate(us_news.get(us_url).get('article'))
            
            kr_text = ""

            for kr_url in dic.get(us_url):
                kr_text += kr_news.get(kr_url).get('title') + kr_news.get(kr_url).get('article')

            top_k_100_dic[idx+1] = {
                'us':us_text,
                'kr':kr_text
            }

        with open('top_k_100.json', 'w', encoding='utf8') as f:
            json.dump(top_k_100_dic, f, indent=4, sort_keys=True, ensure_ascii=False)



        top_k_100_dic = {}
        with open('top_k_100.json','r', encoding='utf8') as f:
            top_k_100_dic = json.load(f)

        top_k_100_list = sorted(top_k_100_dic.items(), key=(lambda x : int(x[0])))
        word_bipartite = {}



        stopwords = []
        with open('한글불용어.txt', 'r', encoding='utf8') as f:
            stopwords = f.read().split('\n')

        for idx, dic in top_k_100_list:
            print(idx)
            
            # 특수문자와 불용어 제거
            us_text = dic.get('us')
            us_text = re.sub('[0-9]+', '', us_text)
            us_text = re.sub('[A-Za-z]+', '', us_text)
            us_text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ·!』\\‘’“”|\(\)\[\]\<\>`\'…》©]', '', us_text)
            us_text = ' '.join(us_text.split())
            
            kr_text = dic.get('kr')
            kr_text = re.sub('[0-9]+', '', kr_text)
            kr_text = re.sub('[A-Za-z]+', '', kr_text)
            kr_text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ·!』\\‘’“”|\(\)\[\]\<\>`\'…》©]', '', kr_text)
            kr_text = ' '.join(kr_text.split())

            us_nouns = []
            temp = []
            count = 0
            for i in us_text.split(' '):
                if count>=500:
                    us_nouns.extend(han.nouns(' '.join(temp)))
                    temp = []
                    count = 0
                    continue

                temp.append(i)
                count+=1

            us_nouns.extend(han.nouns(' '.join(temp)))
            us_nouns = ' '.join(us_nouns)

            kr_nouns = []
            temp = []
            count = 0
            for i in kr_text.split(' '):
                if count>=500:
                    kr_nouns.extend(han.nouns(' '.join(temp)))
                    temp = []
                    count = 0
                    continue

                temp.append(i)
                count+=1

            kr_nouns.extend(han.nouns(' '.join(temp)))
            kr_nouns = ' '.join(kr_nouns)
            
            clean_us_list = get_clean_words(us_nouns, stopwords)
            clean_kr_list = get_clean_words(kr_nouns, stopwords)

            top = 10
            us_nouns_top = get_top_nouns(clean_us_list, top)
            kr_nouns_top = get_top_nouns(clean_kr_list, top)
            
            for i in range(top):
                if i >= len(us_nouns_top): break

                us_word = us_nouns_top[i]
                us_word = us_word[0]

                if us_word in word_bipartite.keys():
                    word_bipartite[us_word][0] += 1
                    
                else:
                    word_bipartite[us_word] = [1, {}]

                for j in range(top):
                    if j >= len(kr_nouns_top): break
                    
                    kr_word = kr_nouns_top[j]
                    kr_word = kr_word[0]
                    
                    if kr_word in word_bipartite.get(us_word)[1].keys():
                        word_bipartite[us_word][1][kr_word] += 1

                    else:
                        word_bipartite[us_word][1][kr_word] = 1


        word_bipartite_list = sorted(word_bipartite.items(), reverse=True, key=(lambda x : int(x[1][0])))
        for i in range(len(word_bipartite_list)):
            temp = ', '.join( [y[0] for y in sorted(word_bipartite_list[i][1][1].items(), reverse=True, key=(lambda x : int(x[1])))[:5] ] )
            word_bipartite_list[i] = word_bipartite_list[i][0] + " : " + temp


        with open('result.txt', 'w', encoding='utf8') as f:
            for row in word_bipartite_list:
                f.writelines(row+'\n')
