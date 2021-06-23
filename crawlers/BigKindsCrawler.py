from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)

import json
import pandas as pd
import jsonlines
import re
import pprint
import grequests
from utils.FeedbackCounter import FeedbackCounter


def write_jsonl(JSON_ARR, filename='output.jsonl'):
    with jsonlines.open(filename, mode='a') as writer:
        writer.write_all(JSON_ARR)


def text_preprocess(text):
    """
    텍스트 전처리
    1. span tag 삭재
    2. br tag 삭제
    3. 영어, 한글, 숫자, 온점 제외 삭제
    4. 온점을 구분으로 문장 구분
    """
    text = re.sub("(<span class='quot[0-9]'>|</span>|<br/>|<br />|([^0-9가-힣A-Za-z. ]))","",text)
    return '''
    '''.join([sen.strip() for sen in text.split('.') if sen.strip()])

def crawl(search, start_date, end_date):
    headers = {
        'Accept':'application/json, text/javascript, */*;',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36 Edg/87.0.664.75',
        'Referer':'https://www.bigkinds.or.kr/v2/news/search.do'
    }
    headers2 = {
        'Accept':'application/json, text/javascript, */*;',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36 Edg/87.0.664.75',
        'Referer':'https://www.bigkinds.or.kr/v2/news/index.do',
        'Host':'www.bigkinds.or.kr',
        'X-Requested-With':'XMLHttpRequest'
    }

    end_page = 537 #1000
    # end_page = 1 #1000

    fbc = FeedbackCounter( end_page )


    NEWS_LIST_URL = "https://www.bigkinds.or.kr/api/news/search.do"
    NEWS_LIST_PAYLOAD = {"indexName":"news",
            "searchKey":"%s AND  (%s)"%(search, search),
            "searchKeys":[{'orKeywords': ["%s"%search]}],
            "byLine":"",
            "searchFilterType":"1",
            "searchScopeType":"2",
            "searchSortType":"date",
            "sortMethod":"date",
            "mainTodayPersonYn":"",
            "startDate":"%s"%start_date,
            "endDate":"%s"%end_date,
            "newsIds":None,
            #    "categoryCodes":["001000000","001005000","001001000","001004000","001003000","001007000","001002000","001006000","002000000","002004000","002010000","002008000","002014000","002011000","002009000","002005000","002001000","002012000","002006000","002002000","002007000","002003000","002013000","003000000","003007000","003003000","003006000","003002000","003009000","003001000","003005000","003010000","003008000","003004000","004000000","004002000","004011000","004006000","004003000","004007000","004010000","004004000","004008000","004001000","004009000","004005000","008000000","008005000","008001000","008004000","008003000","008006000","008002000"],
            #    "providerCodes":["01100101","01100201","01100301","01100401","01100501","01100611","01100701","01100801","01100901","01101001","01101101"],
            "categoryCodes":[],
            "providerCodes":[],
            "incidentCodes":[],
            "networkNodeType":"",
            "topicOrigin":"",
            "dateCodes":[],
            "startNo":1,
            "resultNumber":"1000",
            "isTmUsable":True,
            "isNotTmUsable":False
    }
    result_len=1000

    rs = (print(f'{idx} url 수집 진행 / {end_page} ') or NEWS_LIST_PAYLOAD.update({"startNo":idx, "resultNumber":str(result_len)}) or grequests.post(NEWS_LIST_URL, headers=headers, data = json.dumps(NEWS_LIST_PAYLOAD),callback=fbc.feedback) for idx in range(1, end_page+1))
    a = grequests.map(rs)
    dfArr = [ print(f'detail {count+1} / {len(a)} url 수집 완료') or pd.json_normalize(i.json()['resultList']) for count, i in enumerate(a) if i is not None]

    df_total = pd.concat(dfArr)
    df_total.reset_index(drop=True, inplace=True)

    # 기사 데이터 jsonl 형식으로 저장
    with open('result/bigkinds/result.jsonl', 'w', encoding='utf8') as f:
        f.write('')

    json_arr = []
    url_list = []
    fbc = FeedbackCounter( len(df_total.NEWS_ID) )
    for i, news_id in df_total.NEWS_ID.items():
        if len(url_list)>=100:
            rs = (print(f'{idx+1 + int((i+1)/100)*100} / {len(df_total.NEWS_ID)} 내용 수집 진행 {u}') or grequests.get(f"https://www.bigkinds.or.kr/news/detailView.do?docId={u}&returnCnt=1&returnCnt=1&sectionDiv=1000", headers=headers2, callback=fbc.feedback) for idx, u in enumerate(url_list))
            a = grequests.map(rs)
            json_arr = [ print(f'detail {count+1} / {len(a)}') or i.json()['detail'] for count, i in enumerate(a) if i is not None]
            # json_arr.extend( [ print(f'detail {count+1} / {len(a)} jsonl 저장') or i.json()['detail'] for count, i in enumerate(a) if i is not None])
            write_jsonl(json_arr, 'result/bigkinds/result.jsonl')
            json_arr = []
            url_list = []

        if news_id:
            url_list.append(news_id)

    rs = (grequests.get(f"https://www.bigkinds.or.kr/news/detailView.do?docId={u}&returnCnt=1&sectionDiv=1000", headers=headers, callback=fbc.feedback) for idx, u in enumerate(url_list))
    a = grequests.map(rs)
    json_arr = [ i.json()['detail'] for count, i in enumerate(a) if i is not None]
    write_jsonl(json_arr, 'result/bigkinds/result.jsonl')

    data = {}

    # 저장된 기사 데이터 불러오기
    with jsonlines.open('result/bigkinds/result.jsonl') as reader:
        results = (obj for obj in reader.iter(type=dict, skip_invalid=True))
        for result in results:
            if result == {}:
                continue

            data[result['NEWS_ID']] = {
                'title':result['TITLE'],
                'author':result['BYLINE'],
                'date':result['NEWS_ID'].split('.')[1],
                'company':result['PROVIDER'],
                'article':text_preprocess( result['CONTENT'] )
            }
                
    with open('result/bigkinds/news_%s.json'%search, 'w', encoding='utf8') as f:
        json.dump(data, f, indent=4, sort_keys=True, ensure_ascii=False)
