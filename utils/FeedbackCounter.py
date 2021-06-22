# 
# FeedbackCounter.py
# Author : Ji-yong219
# Project Start:: 2020.12.18
# Last Modified from Ji-yong 2021.06.22
#

class FeedbackCounter:
    """Object to provide a feedback callback keeping track of total calls."""
    def __init__(self, all):
        self.counter = 1
        self.all = all

    def feedback(self, r, **kwargs):
        self.counter += 1
        print(f'{self.counter} / {self.all+1}, {r.url}')
        return r