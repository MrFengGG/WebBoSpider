from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from pymongo import mongo_client
import bs4
import os

import time

def login(url,username,password):
    '''
    用于登录微博
    :param url:微博的登录接口 
    :param username: 用户名
    :param password: 密码
    :return: cookie
    '''
    #browser = webdriver.Chrome()                                                     #用谷歌浏览器实验
    browser = webdriver.PhantomJS("E:/phantomjs-2.1.1-windows/bin/phantomjs.exe")      #用PhantomJS
    browser.maximize_window()                      #设置窗体为最大，如果没有这一行，表单可能无法操作
    browser.get(url)                               #打开登陆用的网页

    print("开始登陆")
    username_ele = browser.find_element_by_id("loginname")    #找到用于输入用户名的表格
    username_ele.clear()                                      #清空表格
    username_ele.send_keys(username)                          #输入账户
    password_ele = browser.find_element_by_name("password")   #找到用于输入密码的表格
    password_ele.clear()                                      #清空表格
    password_ele.send_keys(password)                          #输入密码
    submit = browser.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[6]/a/span')   #找到用于提交表单的类型为submit的input
    submit.click()          #点击
    time.sleep(5)
    WebDriverWait(browser, 10).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'WB_miniblog')))  #等待登陆页面加载完成
    if is_ele_exist(browser,"loginname"):
        print("登录失败")
        browser.quit()
        return None
    print("登陆成功")
    #return print(browser.get_cookies()
    return browser     #返回获得的cookie

def is_ele_exist(browser,id):
    '''
    根据一个id判断当前页面元素是否存在，find方法没有找到元素会抛出异常，利用异常判断元素是否存在
    :param browser: 浏览器
    :param id: 元素id
    :return: 存在返回True，不存在返回False
    '''
    try:
        s = browser.find_element_by_class_name(id)
        return True
    except:
        return False

def getweibohtml(browser,url):
    '''
    用于加载我们要爬取的用户的动态页面(单个页面上的所有信息)
    :param url: 要爬取用户的url
    :param cookie: 用于认证用户
    :return: 返回一个html页面
    '''''
    #browser = webdriver.PhantomJS("E:/phantomjs-2.1.1-windows/bin/phantomjs.exe")
    #browser = webdriver.Chrome()
    #browser.add_cookie(cookie)
    #判断broser是否可用
    if browser == None:
        return
    browser.get(url)
    browser.save_screenshot("f:\\test1.png")
    js = "var q=document.body.scrollTop=100000"       #用于下滑页面的js命令

    num = 0
    #判断翻页按钮是否出现，如果没有出现，将鼠标下滑
    while not is_ele_exist(browser,"W_pages"):
        num+=1
        browser.execute_script(js)
        print("还未找到元素")
        #最多翻页十次，防止进入死循环
        if(num>10):
            break

    print("用户的一页信息已加载完毕")
    html = browser.page_source
    return html

'''
def has_source(browser,url):
    
    判断一个微博页面是否有微博，如果没有，返回Fasle,
    最开始考虑不周到，这个函数导致需要再次用webdriver打开页面
    严重拖慢爬取速度，弃用
    
    browser.get(url)
    if is_ele_exist(browser,"WB_feed_handle"):
        return True
    else:
        return False
'''

def has_source(html):
    '''
    判断一个微博页面是否有微博，如果没有，返回Fasle,
    改良版，不用再次加载页面
    '''
    bs = bs4.BeautifulSoup(html,"lxml")
    if bs.find("div",class_="WB_detail") !=None:
        return True
    else:
        return False

def getusermessage(html):
    '''
    获取用户信息，包括头像，姓名。粉丝
    :param html: 
    :return: 
    '''
    user = {}
    bs = bs4.BeautifulSoup(html,"lxml")
    user["姓名"] = bs.find_all("h1",class_="username")[0].text
    user["头像"] = bs.find_all("p",class_="photo_wrap")[0].find_all("img")[0]["src"]
    user["认证"] = bs.find_all("div",class_="pf_intro")[0]["title"]
    messagebox = bs.find_all("div",class_="WB_innerwrap")
    messages = messagebox[0].find_all("td",class_="S_line1")
    for message in messages:
        title = message.find_all("span",class_="S_txt2")[0].text
        content = message.find_all("strong",class_="W_f16")[0].text
        user[title] = content
    print(user)
    return user
def getweibo(filename,html):
    '''
    获取一个页面上的所有信息，包括每一条微博的内容，转发，评论，点赞数量
    '''
    pic_num = 0
    if not os.path.exists(filename):
        os.mkdir(filename)
    file = open(filename+"\weibo.txt","a",encoding="utf-8")
    beautifulsoup = bs4.BeautifulSoup(html,"lxml")
    weibos = beautifulsoup.find_all("div",class_="WB_cardwrap WB_feed_type S_bg2 ")  #获得用于显示微博的父节点
    weibonum = 0     #计算该页微博数量
    for weibo in weibos:
        #对每一个微博父节点进行处理
        weibotext = weibo.find_all("div",class_ = "WB_text W_f14") #获取微博文本内容
        message = weibotext[0].text.replace(" ","")                #取出文本中的所有空格
        weibonum+=1                                                #微博数量+1
        file.write("\n第"+str(weibonum)+"条微博内容是:"+message+"\n")

        weibopics = weibo.find_all("div",class_="WB_media_wrap clearfix")   #获取用于显示图片的标签
        if len(weibopics) != 0:                                             #判断标签是否存在
            pics = weibopics[0].find_all("img")                             #获取该标签中的所有图片
            for pic in pics:
                download(pic["src"],filename+"\\"+str(pic_num+1))
                pic_num+=1
                file.write(pic["src"]+"\n")

        weibomessages = weibo.find_all("div", class_="WB_feed_handle")  # 获取微博信息父节点
        weibomessagecontents = weibomessages[0].find_all("a", class_="S_txt2")  #获取用于显示微博信息的节点（包括转发，评论，点赞数量）
        for weibomessagecontent in weibomessagecontents[1:]:                    #分别获取信息
            contents = weibomessagecontent.find_all("em")
            file.write(contents[1].text+"  ")
    file.close()
    print("成功存储一个页面的微博")
    return weibonum


def getpageurl(url,num):
    '''
    根据一个用户的第一页获取后续的url
    http://www.weibo.com/u/1858002662?c=spr_sinamkt_buy_hyww_weibo_p113&is_hot=1#1496336038914
    http://www.weibo.com/u/1858002662?is_search=0&visible=0&is_hot=1&is_tag=0&profile_ftype=1&page=2#feedtop

    http://weibo.com/leehom?refer_flag=1005055013_&is_all=1
    http://weibo.com/leehom?is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page=2#feedtop
    通过分析指导，page应该是表示的页面，is_all和is_hot应该对应的是热门微博和全部微博
    '''
    preurl = url.split("?")
    preurl = preurl[0]
    pageurl = preurl+"?is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page="+str(num)+"#feedtop"
    return pageurl

def spider(url,username,password):
    num = 0;
    browser = login("http://weibo.com/login.php",username,password)
    print("开始获取第1页的微博")
    html = getweibohtml(browser,url)
    file = open("f:\\xuanzi\\weibo.txt","a",encoding="utf-8")
    user = getusermessage(html)
    for key in user.keys():
        file.write(key+":"+user[key]+"\n")
    file.close()
    num += getweibo("f:\\xuanzi.txt",html)
    print("获取第1页的微博成功")
    page = 1;
    while True:
        page+=1
        pageurl = getpageurl(url,page)
        print(pageurl)
        html = getweibohtml(browser, pageurl)
        if has_source(html):
            print("开始获取第"+str(page)+"页的微博")
            num += getweibo("f:\\xuanzi.txt",html)
        else:
            return
    return num

def download(url,filename):
    pic = urllib.request.urlopen(url).read()
    file = open(filename,"wb")
    file.write(pic)
    file.close()

if __name__ =="__main__":

    #browser = login("http://weibo.com/login.php","15271183269","f43312626")

    '''
    for cookie in cookies:
        if cookie["name"] == "_s_tentry":
            log_cookie = cookie
            break
    '''
    '''
    getweibohtml("http://www.weibo.com/u/1858002662?is_search=0&visible=0&is_tag=0&profile_ftype=1&page=3&c=spr_sinamkt_buy_hyww_weibo_t113&is_all=1", browser)
    '''
    #print(has_source(browser,"http://www.weibo.com/u/1858002662?is_search=0&visible=0&is_tag=0&profile_ftype=1&page=21&c=spr_sinamkt_buy_hyww_weibo_t113&is_all=1"))
    #file = open("f:\\test5.html","rb").read()
    #html = file.decode("utf-8","ignore")
    #getweibo(html)

    #url = getpageurl("http://weibo.com/dasima315?sudaref=passport.weibo.com&is_all=1", 4)
    #print(url)
    #num = spider("http://www.weibo.com/u/1858002662?c=spr_sinamkt_buy_hyww_weibo_p113&is_hot=1", "15271183269", "f43312626")
    #print("一共获取"+str(num)+"条微博")

    spider("http://www.weibo.com/u/1858002662?c=spr_sinamkt_buy_hyww_weibo_p113&is_hot=1","15271183269","f43312626")
