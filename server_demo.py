# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 06:30:28 2018

@author: Quantum Liu
"""

from flask import Flask, request
import json
import base64
from aip import AipOcr


""" 你的 APPID AK SK """
APP_ID = '111'
API_KEY = '111'
SECRET_KEY = '111'


CLIENT = AipOcr(APP_ID, API_KEY, SECRET_KEY)

OPTIONS = {}
OPTIONS["recognize_granularity"] = "big"
OPTIONS["language_type"] = "CHN_ENG"
OPTIONS["detect_direction"] = "true"
OPTIONS["detect_language"] = "true"
OPTIONS["vertexes_location"] = "true"
OPTIONS["probability"] = "true"

USRS={'self':{'passwd':'a','number':999}}

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'hello world'

@app.route('/login', methods=['POST'])
def login():
    global USRS
    enable=False
    number=0
# =============================================================================
#     print(request.headers)
#     print(request.form)
# =============================================================================
    uname=request.form.get('uname',False)
    passwd=request.form.get('passwd',False)
    if all([uname,passwd]):
        usr=USRS.get(uname,None)
        if isinstance(usr,dict):
            real_passwd=usr.get('passwd',False)
            if passwd==real_passwd:
                enable=True
                number=usr.get('number',0)
    return json.dumps({'enable':enable,'number':number})

@app.route('/read', methods=['POST'])
def read():
    global USRS
    enable=False
    number=0
# =============================================================================
#     print(request.headers)
#     print(request.form)
# =============================================================================
    uname=request.form.get('uname',False)
    passwd=request.form.get('passwd',False)
    if all([uname,passwd]):
        usr=USRS.get(uname,None)
        if isinstance(usr,dict):
            real_passwd=usr.get('passwd',False)
            if passwd==real_passwd:
                enable=True
                number=usr.get('number',0)
    if number>0:
        content=request.form.get('content',False)
# =============================================================================
#         print(len(content))
#         with open('log.txt','w') as f:
#             f.write(content.encode("utf8").decode("utf8"))
# =============================================================================
        data=base64.b64decode(content)
        print(len(data))
        res_baidu=post(data)
        usr['number']-=1
        if isinstance(res_baidu,dict):
            res_baidu.update({'enable':enable,'number':number})
            return json.dumps(res_baidu)
    return json.dumps({'enable':enable,'number':number})

def post(content):
    global OPTIONS
    global CLIENT
    return CLIENT.general(content, OPTIONS)



# =============================================================================
# def search(word):
#     __url = 'http://www.baidu.com/s?wd='  # 搜索请求网址
# 
#     r = requests.get(__url + word)
#     if r.status_code == 200:  # 请求错误（不是200）处理
#         return r.text
#     else:
#         print(r.status_code)
#         return False
#     
# def read(content):
#     response=post(content)
#     return response
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True)