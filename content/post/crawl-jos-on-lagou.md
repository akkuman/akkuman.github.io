---
title: 拉勾抓职位简单小爬虫
date: 2018-09-11 04:12:38
tags: 
- Python
categories:
- Python
---


花了十来分钟写了个这个小爬虫，目的就是想能够方便一点寻找职位，并且大四了，没有工作和实习很慌啊！

<!-- more -->

爬虫不具有扩展性，自己随手写的，改掉里面的 `keyword` 和 `region` 即可爬行所有的招聘，刚开始测试的是5s访问一次，不过还是会被ban，所以改成了20s一次，没有使用多线程和代理池，懒，够用就行了，结果会保存到一个csv文件里面，用excel打开即可。

直接上代码：

```python
import requests
import urllib.parse
import json
import time
import csv


def main():
    keyword = '逆向'
    region = '全国'
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Length': '37',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'www.lagou.com',
        'Origin': 'https://www.lagou.com',
        'Pragma': 'no-cache',
        'Referer': 'https://www.lagou.com/jobs/list_%s?city=%s' % (urllib.parse.quote(keyword), urllib.parse.quote(region)),
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36',
        'X-Anit-Forge-Code': '0',
        'X-Anit-Forge-Token': 'None',
        'X-Requested-With': 'XMLHttpRequest',
    }
    data = {
        'pn': 1,
        'kd': keyword,
    }

    total_count = 1
    pn = 1
    jobjson = []

    while 1:
        if total_count <= 0:
            break
        data['pn'] = pn
        lagou_reverse_search = requests.post("https://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false", headers=headers, data=data)
        datajson = json.loads(lagou_reverse_search.text)
        print('page %d get finish' % pn)
        if pn == 1:
            total_count = int(datajson['content']['positionResult']['totalCount'])
        jobjson += [{'positionName': j['positionName'], 'salary': j['salary'], 'workYear': j['workYear'], 'education': j['education'], 'city': j['city'], 'industryField': j['industryField'], 'companyShortName': j['companyShortName'], 'financeStage': j['financeStage']} for j in datajson['content']['positionResult']['result']]
        total_count -= 15
        pn += 1
        time.sleep(20)

    csv_header = ['positionName', 'salary', 'workYear', 'education', 'city', 'industryField', 'companyShortName', 'financeStage']
    with open('job.csv','w') as f:
        f_csv = csv.DictWriter(f, csv_header)
        f_csv.writeheader()
        f_csv.writerows(jobjson)


if __name__ == '__main__':
    main()
```

ajax动态加载的，直接打开调试工具看XHR即可。