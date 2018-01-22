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
    '''
    使用adb截屏并做缩放、灰度化、二值化处理
    return:
        binary:uint8 array,binarized screen
        gray:uint8 array,grey screen
        frame::uint8 array,BGR screen
        scale:float
    '''
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
    '''
    从灰度图中使用Hough算法定位头像和计时圆框，
    进而根据底部坐标获得问题和答案所在的ROI
    '''
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
    '''
    使用Hough算法定位置线，根据ROI的灰度图，定位选项的矩形框
    return:
        lines:array,list of lines
        nx,ny:nb of 
    '''
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
    '''
    根据圆框底部和选项矩形的顶部，计算问题位置
    '''
    shape=gray.shape
    
    top=int(bottom_circles+shape[0]/20)
    bottom=int(top_rects-shape[0]/15)
    
    nonzero=np.where(binary[top:bottom].sum(axis=0)>0)[0]
    
    left,right=nonzero.min(),nonzero.max()
    
    return top,bottom,left,right

def lines_to_rect(lines):
    '''
    计算包含所有直线的最小矩形
    '''
    left,right,top,bottom=np.min(lines[:,[0,2]]),np.max(lines[:,[0,2]]),np.min(lines[:,[1,3]]),np.max(lines[:,[1,3]])
    return top,bottom,left,right


def get_roi(binary,gray,frame,config='config.d'):
    '''
    获取ROI，并保存为本地文件
    '''
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
        circles=detect_circle(gray)#定位圆框
        bottom_circles=int((circles[:,-2]+circles[:,-1]).max())#圆框底部
    
        lines,nx,ny=detect_line(gray[bottom_circles:])#定位直线
    
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
        
    tq,bq,lq,rq=detect_question(gray,binary,bottom_circles,top_rects)#定位问题

    width=np.max([right_rects-left_rects,rq-lq])
    height=bottom_rects-top_rects+bq-tq
    
    new=np.zeros((height,width,3),dtype=frame.dtype)#新建一个最小的RGB图片，包含问题和选项
    
    new[:(bq-tq),:(rq-lq)]=frame[tq:bq,lq:rq].copy()
    new[(bq-tq):,:(right_rects-left_rects)]=frame[top_rects:bottom_rects,left_rects:right_rects].copy()
    
    
    return new,(bq-tq),state

def rgb_to_content(img):
    '''
    将BGR图片转换为bytes数据
    '''
    return cv2.imencode('.jpg',img)[1].tostring()

def search(word):
    '''
    使用百度搜索搜索关键词
    '''
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
    '''
    向服务器端发送登录验证请求
    '''
# =============================================================================
#     url='123.206.208.40:8080/login'
# =============================================================================
    url='http://127.0.0.1:5000/login'
    user_info={'uname':uname,'passwd':passwd}
    response = requests.post(url, data=user_info)
    print(response.text)
    return _proccessResult(response.content)

def post_read(uname,passwd,content):
    '''
    向服务器端发送OCR请求
    '''
# =============================================================================
#     url='123.206.208.40:8080/read'
# =============================================================================
    url='http://127.0.0.1:5000/read'
    content=base64.b64encode(content).decode()
    user_info={'uname':uname,'passwd':passwd,'content':content}
    print(len(content))
    response = requests.post(url, data=user_info)
    return _proccessResult(response.content)


def get_result(response,bound,state):
    '''
    根据搜索响应，使用正则匹配选项出现次数，推算是正确答案的可能性
    '''
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
    '''
    将答案格式化为可读文本
    '''
    text='问题：{}\n参考答案:{}\n选项与概率：\n{}'
    answer_text='\n'.join([str(a)+'：'+str(p) for a,p in zip(answers,probs)])
    text=text.format(question,reference,answer_text)
    print(text)
    return text