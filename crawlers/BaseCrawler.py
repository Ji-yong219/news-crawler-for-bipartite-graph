# 
# baseCrawler.py
# based class for Web crawling program
# Author : Ji-yong219
# Project Start:: 2020.12.18
# Last Modified from Ji-yong 2021.06.22
#

from bs4 import BeautifulSoup as bs
from urllib.request import HTTPError

import grequests
from functools import partial

class Crawler:
    def crawlLinks(self):
        pass

    def crawlNews(self):
        pass

    async def getSoup(self, url):
        try:
            print(f'{self.news_queue.index(url)+1} / {len(self.news_queue)} url 요청 중 ... ')

            request = partial(grequests.get, url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'})
            res = await self.loop.run_in_executor(None, request)
            
            print(f'{self.news_queue.index(url)+1} / {len(self.news_queue)} url 요청 완료 {url}')
            
            res = grequests.map([res], size=1)[0]

            if res is not None:
                res = res.content
                soup = await self.loop.run_in_executor(None, bs, res, 'html.parser')
                
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

    def getTitle(self):
        pass

    def getAuthor(self):
        pass
        
    def getDate(self):
        pass

    def getArticle(self):
        pass