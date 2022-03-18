# encoding=utf-8
# 參考資料
# https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/

'''
如果出現以下文字
SyntaxError: (unicode error) 'utf-8' codec can't decode byte 0xa4 in position 0: invalid start byte

請將檔案以utf-8碼存檔
'''

from datetime import datetime
import demjson
import os
from os import path
import requests
import shutil
import time
import sys
import json
import urllib
import openpyxl
from bs4 import BeautifulSoup
from requests_html import HTML
import re

import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt

import numpy as np
from PIL import Image

from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from json import *
from linebot.models import *
from multiprocessing import Process

import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import collections
from PIL import Image
import operator
import base64

#############################
#  函式庫
#############################

###########LineBot互動###############

app = Flask(__name__, template_folder='template')

_token='rv7P6DgWEFj0AfNFq2dfDZbRHuNNlw6tCMTgz38+u6Fa7o1jln7c1NMlwBHBFjk016zsJ+FJI/FBI4t4Cm+36woWIyjzriMMba2uWAE/WmSBs2/aQwlskQBNuqW0lFHLX9ivFqTm/ntEq0yl3G4dvwdB04t89/1O/w1cDnyilFU='
_secret='a91ae69e3fd73b16b8767823704aa9ee'
line_bot_api = LineBotApi(_token)
handler = WebhookHandler(_secret)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    pass
    return 'OK'
pass

@app.route('/', methods = ['GET','POST'])
def hello_world():
  return render_template('0425.html')

def startmessage():

    line_bot_api.broadcast(TextSendMessage(text='今天過得好嗎?來看看最近有哪些熱門話題......'))
    line_bot_api.broadcast(TemplateSendMessage
                                                (alt_text='新訊息來囉~點開來看看吧',
                                                template=ConfirmTemplate(
                                                    title='Bcard',
                                                    text='閱讀Dcard熱門文章?(請在30秒內點選)',
                                                        actions=[                              
                                                            MessageTemplateAction(
                                                                label='好呀!',
                                                                text='好呀!',
                                                                ),
                                                            MessageTemplateAction(
                                                                label='等等再看~',
                                                                text='等等再看~'
                                                            )
                                                        ]   
                                                    )
                                                )
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    #讀熱門標題的排序檔
    f=open('words_sort.txt', "r",encoding="ansi")
    title = f.read()

    #熱門標題_list to dict
    new_dict = dict(eval(title))
    only_title = []
    for key in new_dict.keys():
        only_title.append(key)

    #熱門標題_網址
    url_list = []
    url="https://www.dcard.tw/search"
    for i in range(5): 
        data = {'query' : only_title[i]}
        resq = requests.get(url, params = data)
        url_list.append(resq.url)
    
    # get user id when reply
    user_id = event.source.user_id
    print("user_id =", user_id)

    if event.message.text == "好呀!":
        line_bot_api.reply_message(event.reply_token,TemplateSendMessage
                                                    (alt_text='新訊息來囉~點開來看看吧',
                                                    template=ButtonsTemplate(
                                                        title='Bcard', 
                                                        text='請選擇熱門話題',
                                                        thumbnail_image_url='https://i.imgur.com/TWt1R8v.jpg',
                                                        # ratio="1.51:1",
                                                        # image_size="cover",
                                                            actions=[                              
                                                                URITemplateAction(
                                                                label='熱門話題[1]:' + only_title[0], uri= url_list[0]
                                                                ),
                                                                URITemplateAction(
                                                                label='熱門話題[2]:' + only_title[1], uri= url_list[1]
                                                                ),
                                                                URITemplateAction(
                                                                label='熱門話題[3]:' + only_title[2], uri= url_list[2]
                                                                ),
                                                                URITemplateAction(
                                                                label='熱門話題[4]:' + only_title[3], uri= url_list[3]
                                                                )
                                                            ]
                                                        )
                                                    )
        )
    elif event.message.text == "等等再看~": 
        line_bot_api.reply_message(event.reply_token,TemplateSendMessage
                                                    (alt_text='新訊息來囉~點開來看看吧',
                                                    template=ImageCarouselTemplate(
                                                        columns=[
                                                            ImageCarouselColumn(
                                                                image_url='https://i.imgur.com/nYylPGC.jpg',
                                                                action=URIAction(
                                                                    label='先看詞雲~等等記得回來',
                                                                    uri='https://1eaf3cb5.ngrok.io/'
                                                                )
                                                            )
                                                        ]
                                                    )
                                                    )
        )
    
###########分詞&詞雲###############
    
# 讀取文檔，且分詞
def cut_words(i_filename):
    d = path.dirname(__file__) if "__file__" in locals() else os.getcwd()
    text = open(path.join(d, i_filename), encoding='ansi').read()
    text = jieba.lcut(text, cut_all=False)
    return text
pass

# 引用外部停止詞
def load_stopwords(i_filename):
    d = path.dirname(__file__) if "__file__" in locals() else os.getcwd()
    filepath = path.join(d, i_filename)
    stopwords = [line.strip() for line in open(
        filepath, encoding='utf-8').readlines()]
    pass
    # print(stopwords) # test
    return stopwords
pass

# 去除原文stopwords，並生成新的文本及最熱門的五個詞彙
def move_stopwwords(content, stopwords, new_filename):
    
    #1. 去除stopwords
    stopwords = [stop_word.rstrip() for stop_word in stopwords]
    
    new_list = []
    counts = {}
    for word in content:
        if word not in stopwords:
            new_list.append(word.strip())
            if len(word) == 1:  
              continue  
            else:  
              counts[word] = counts.get(word,0) + 1
        pass
    pass
    
    #2. 排序詞頻並將前五個寫到新文本
    word_counts = sorted(counts.items(), key = operator.itemgetter(1), reverse=True)
    new_word_counts = word_counts[:5]
    
    word_counts_file = open("words_sort.txt", 'w')
    word_counts_file.write(str(new_word_counts))
    word_counts_file.close()
    
    #3. 更新無stopwords的文本
    word_new_list_file = open(new_filename, 'w')
    word_new_list_file.write(str(new_list))
    word_new_list_file.close()
pass

# 辭雲
def gen_wc(i_filename):

    # 1. 讀檔
    filename = i_filename
    f=open(filename, "r",encoding="ansi")
    mytext = f.read()
    # print(mytext)
    
    # 2. 中文分詞分詞
    mytext = " ".join(jieba.cut_for_search(mytext, HMM = True))
    # print(mytext)
    
    # 设置自定义词典
    jieba.load_userdict("userdict.txt")
    
    # 手動新增中文停止詞
    stopwords_set = set('')
    
    wordcloud = WordCloud(font_path="font/msjh.ttf",  
                            stopwords = stopwords_set,
                            scale=1, # 縮放2倍
                            max_font_size = 200,  
                            max_words=10, # 最多顯示的詞彙量 
                            background_color = '#383838',  # 灰色
                            colormap = 'GnBu', # colormap名稱 https://matplotlib.org/examples/color/colormaps_reference.html
                            width=1000, 
                            height=1000,
                            mask=np.array(Image.open( "dcard.png")) # 需要是去背的圖片
                            ).generate(mytext)


    # 4. 存檔
    # 方法1: 用wordcloudS
    wordcloud.to_file('template/0419_new_doc.png')

    # 5. show在螢幕上
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    # plt.show()
    
pass

###########爬蟲###############

# 取得 html code
def get_web_page(url):
  resp = requests.get(url=url, cookies={'over18': '1'})
  
  if resp.status_code != 200:
    print('Invalid url:', resp.url)
    return None
  else:
    # address UnicodeEncodeError: ‘cp950’ codec can’t encode character
    text = resp.text
    text = text.encode(sys.stdin.encoding, "replace").decode(sys.stdin.encoding)
    return text
  pass
pass

# 取得html code的特定資料
def get_articles(html_code):
  soup = BeautifulSoup(html_code, 'html.parser')
  
  id = 1
  fp = open('0419.txt','a')
  
  for i in soup.find_all('h2'):
    title = i.get_text('class')
   
    print(title)
    
    id += 1
    fp.writelines(title+'\n')
  fp.close()  
pass

########################################
#  主程式
########################################

#########爬蟲
def main():
    url="https://www.dcard.tw/f"
    data = {'popular' : 'true'}
    resq = requests.get(url, params = data)
    
    html_code=get_web_page(resq.url) 
    get_articles(html_code)
    
    print("========"+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"========")
pass

#########分詞&詞雲
def main2():
    content = cut_words(r'0419.txt')
    stopwords = load_stopwords(r'stopwords.txt')
    move_stopwwords(content, stopwords, r'0419_new_doc.txt')
    gen_wc(r'0419_new_doc.txt')

#########上傳更新後的詞雲
def main3():
    with open("template/0419_new_doc.png", "rb") as imageFile:
        str = base64.b64encode(imageFile.read())
        str1 = bytes.decode(str)
    
    f = open('template/0425.html','w')

    message = """<html>
      <head>
        <title>wordcloud</title>
      </head>
      <body>
      
      <img src='data:image/png;base64,"""+str1+"""'>
      </body>
    </html>"""

    f.write(message)
    f.close()

#########LineBot   
def apppy():
    app.run(host='0.0.0.0',port=10077)

if __name__ == "__main__":  
      
    main()     
    main2() 
    main3()
    
    startmessage()

    p = Process(target = apppy)
    p.start()    
    time.sleep(30)
    p.terminate()

pass