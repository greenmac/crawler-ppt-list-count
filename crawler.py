import requests
from requests_html import HTML
from pretty_print import pretty_print
import urllib
import re
import html
import time
from multiprocessing import Pool

def fetch(url):
    response = requests.get(url)
    response = requests.get(url, cookies={'over18' : '1'}) # 一直向伺服器傳送已經18歲
    return response

def parse_articles_entrie(doc):
    html = HTML(html=doc)
    post_entries = html.find('div.r-ent')
    return post_entries

def parse_article_meta(entry):
    meta=  {
        'title' : entry.find('div.title', first = True).text,
        'push' : entry.find('div.nrec', first = True).text,
        'date' : entry.find('div.date', first = True).text,
    }

    try:
        # 正常狀況取得資料
        meta['author'] = entry.find('div.author', first = True).text
        meta['link'] = entry.find('div.title > a', first = True).attrs['href']
    except AttributeError:
        # 但碰上文章被刪除時，就沒有辦法像原本的方法取得 作者 跟 連結
        if '(本文已被刪除)' in meta['title']:
            # e.g., "(本文已被刪除) [hohho]"
            match_author = re.search('\[(\w*)\]', meta['title'])
            if match_author:
                meta['author'] = match_author.group(1)
        elif re.search('已被\w*刪除', meta['title']):
            # e.g., "(已被lgyfdf刪除) <edisonchu> op"
            match_author = re.search('\<(\w*)\>', meta['title'])
            if match_author:
                meta['author'] = match_author.group(1)
    return meta

def  parse_next_link(doc):
    html = HTML(html=doc)
    paging = html.find('.btn-group-paging a.btn.wide')
    link = paging[1].attrs.get('href') # attrs 沒加不能get
    page_url = urllib.parse.urljoin('https://www.ptt.cc/', link)
    return page_url

# 抓取一頁 (某頁面 URL) 中所有的文章的 metadata，並回傳一串 key-value 類型的資料及下一頁的 URL
def get_metadata_from(url):

    resp = fetch(url) # step-1

    doc = resp.text
    post_entries = parse_articles_entrie(doc) # result of setp-2
    next_link = parse_next_link(doc)
    meta_data = [parse_article_meta(entry) for entry in post_entries]
    return meta_data, next_link

def get_paged_meta(url, pages):
    collected_meta = []
    for _ in range(pages):
        posts, link = get_metadata_from(url)
        collected_meta += posts
        url = urllib.parse.urljoin('https://www.ptt.cc/', link)
    return collected_meta

def get_posts(data):
    # 將所有文章連結收集並串接成完整 URL
    post_links = [
        urllib.parse.urljoin('https://www.ptt.cc/', meta['link'])
        for meta in data if 'link' in meta
    ]
    # 給四顆核心運行Pool(processes = 4),可自由控制運算核心
    with Pool(processes = 4) as pool:
        contents = pool.map(fetch, post_links)
        return contents

if __name__ == '__main__':
    url = 'https://www.ptt.cc/bbs/Gossiping/index.html'
    pages = 5
    start_time = time.time()
    data = get_paged_meta(url, pages)
    resps = get_posts(data)

    # %f 格式化浮点数字，可指定小数点后的精度
    print('花費: %f 秒' % (time.time() - start_time))
    print('共 %d 項結果:' % len(resps))
    for posts, resps in zip(data, resps):
        print('{0} {1: <15} {2}, 網頁內容共 {3}字'.format(posts['date'], posts['author'], posts['title'], len(resps.text)))


# ===以下是測試印出資料===
# for meta in data:
#     # print(meta)
#     pretty_print(meta['push'], meta['title'], meta['date'], meta['author'])  # for below results

# for entry in post_entries:
#     meta = parse_article_meta(entry)
#     # print(meta)
#     pretty_print(meta['push'], meta['title'], meta['date'], meta['author'])  # for below results