# coding: utf-8
import os
import sys
import subprocess
import pickle
import json
import base64

import requests
import re

import cv2
import numpy as np

class NoCircle(Exception):
    pass

class NoLine(Exception):
    pass

def pull_screenshot():
    process = subprocess.Popen('adb shell screencap -p', shell=True, stdout=subprocess.PIPE)
    screenshot = process.stdout.read()
    if sys.platform == 'win32':
        screenshot = screenshot.replace(b'\r\n', b'\n')
    raw=cv2.imdecode(np.fromstring(screenshot,np.uint8),1)
    scale=720/raw.shape[0]
    frame = cv2.resize(raw,None,fy=scale,fx=scale)
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

    ret, binary = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)
    return binary,gray,frame,scale

def detect_circle(gray):
    shape=gray.shape
    r_min,r_max=int(shape[0]/40),int(shape[0]/20)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT,
                               1,100,
                               param1=100, param2=100,
                               minRadius=r_min, maxRadius=r_max)
    if isinstance(circles,type(None)):
        raise NoCircle('No circle detected!May be try it later!')
        return None
    return circles[0,:]

def detect_line(gray):
    height,width=gray.shape
    
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)  
      
    minLineLength = int(width/2.5)
    maxLineLength = int(width*0.8)
    maxLineGap = int(height/50)  
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength, maxLineGap)  
    
    ll=[]
    nx,ny=0,0
    for line in lines[:,0,:]:  
        length=np.sqrt(np.sum((line[:2]-line[-2:])**2))
        dis=np.abs((line[:2]-line[-2:]))
        tan=dis[-1]/(dis[0]+0.001)
        if length>=minLineLength and (tan<=0.1 or tan>=100) and length<=maxLineLength:
            nx+=int(tan<=0.1)
            ny+=int(tan>=100)
            ll.append(line)
    print(nx,ny)
    return np.asarray(ll),nx,ny

def detect_question(gray,binary,bottom_circles,top_rects):
    shape=gray.shape
    
    top=int(bottom_circles+shape[0]/20)
    bottom=int(top_rects-shape[0]/15)
    
    nonzero=np.where(binary[top:bottom].sum(axis=0)>0)[0]
    
    left,right=nonzero.min(),nonzero.max()
    
    return top,bottom,left,right

def lines_to_rect(lines):
    left,right,top,bottom=np.min(lines[:,[0,2]]),np.max(lines[:,[0,2]]),np.min(lines[:,[1,3]]),np.max(lines[:,[1,3]])
    return top,bottom,left,right


def get_roi(binary,gray,frame,config='config.d'):
    if os.path.exists(config):
        with open(config,'rb') as fc:
            params=pickle.load(fc)
            if isinstance(fc,(tuple,list)):
                top_rects,bottom_rects,left_rects,right_rects,bottom_circles=params
                loaded=True
            else:
                loaded=False
    else:
        loaded=False
    
    if not loaded:
        circles=detect_circle(gray)
        bottom_circles=int((circles[:,-2]+circles[:,-1]).max())
    
        lines,nx,ny=detect_line(gray[bottom_circles:])
    
        if len(lines)>2:
        
            lines[:,[1,3]]+=bottom_circles
        
            top_rects,bottom_rects,left_rects,right_rects=lines_to_rect(lines)
            
            if nx<4:
                state='q'
            else:
                state='qa'
            params=(top_rects,bottom_rects,left_rects,right_rects,bottom_circles)
            with open('config.d','wb') as fc:
                pickle.dump(params,fc)
        else:
            raise NoLine('No line detected!Maybe try it later!')
            return None
    tq,bq,lq,rq=detect_question(gray,binary,bottom_circles,top_rects)

    width=np.max([right_rects-left_rects,rq-lq])
    height=bottom_rects-top_rects+bq-tq
    
    new=np.zeros((height,width,3),dtype=frame.dtype)
    
    new[:(bq-tq),:(rq-lq)]=frame[tq:bq,lq:rq].copy()
    new[(bq-tq):,:(right_rects-left_rects)]=frame[top_rects:bottom_rects,left_rects:right_rects].copy()
    
    
    return new,(bq-tq),state

def rgb_to_content(img):
    return cv2.imencode('.jpg',img)[1].tostring()

def search(word):
    __url = 'http://www.baidu.com/s?wd='  # 搜索请求网址

    r = requests.get(__url + word)
    if r.status_code == 200:  # 请求错误（不是200）处理
        return r.text
    else:
        print(r.status_code)
        return False

def _proccessResult(content):
    """
        formate result
    """

    if sys.version_info.major == 2:
        return json.loads(content) or {}
    else:
        return json.loads(content.decode()) or {}
    
def post_login(uname,passwd):
# =============================================================================
#     url='123.206.208.40:8080/login'
# =============================================================================
    url='http://127.0.0.1:5000/login'
    user_info={'uname':uname,'passwd':passwd}
    response = requests.post(url, data=user_info)
    print(response.text)
    return _proccessResult(response.content)

def post_read(uname,passwd,content):
# =============================================================================
#     url='123.206.208.40:8080/read'
# =============================================================================
    content=base64.b64encode(content).decode()
    url='http://127.0.0.1:5000/read'
    user_info={'uname':uname,'passwd':passwd,'content':content}
    print(len(content))
    response = requests.post(url, data=user_info)
    return _proccessResult(response.content)

# =============================================================================
# def read_screen():
#     binary,gray,frame,scale=pull_screenshot()
#     try:
#         roi,bound,state=get_roi(binary,gray,frame)
#     except (NoCircle,NoLine):
#         traceback.print_exc()
#         return read_screen()
#     except:
#         traceback.print_exc()
#         Warning('Got uneepected ERROR, retrying...')
#         time.sleep(0.5)
#         return read_screen()
#     if state=='q':
#         time.sleep(0.5)
#         return read_screen()
#     print('Text type :{}.'.format('question only' if state=='q' else 'question and answer'))
#     content=rgb_to_content(roi)
#     response=post_to_server(content)
#     
#     return response,bound,state
# =============================================================================

def get_result(response,bound,state):
    question,answers='',[]
    for wr in response['words_result']:
        location=wr['location']
        word=wr['words']
        if location['top']+location['height']<=bound:
            question+=word
        else:
            answers.append(word)
    page=search(question)
    nbs=np.asarray([len(re.findall('\s*'.join(list(a)),page)) for a in answers])
    total=np.sum(nbs)+0.01
    
    probs=nbs*100/total
    
    reference=answers[np.argmax(probs)]
    
    return question,answers,nbs,probs,reference

def show_result(question,answers,nbs,probs,reference):
    text='问题：{}\n参考答案:{}\n选项与概率：\n{}'
    answer_text='\n'.join([str(a)+'：'+str(p) for a,p in zip(answers,probs)])
    text=text.format(question,reference,answer_text)
    print(text)
    return text