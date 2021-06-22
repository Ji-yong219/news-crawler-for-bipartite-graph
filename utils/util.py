# 
# util.py
# Author : Ji-yong219
# Project Start:: 2020.12.18
# Last Modified from Ji-yong 2021.06.22
#

import calendar, datetime

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)
        
def get_num_month(str_month):
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
                
def convert_date(original_date):
    data = original_date.split(' ')
    # print(f'data:{data}')
    month = get_num_month(data[0].replace('.', ''))
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