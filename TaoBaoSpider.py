#coding=utf-8

import re
import requests
import traceback
import socket
from TaoBaoGetCookie import main
from TaoBaoSlidingValidation import main2
from TaoBaoComment import Comment
from TaoBaoDB import RedisString,Mysql
import asyncio
from time import sleep
import time


class Spider():

    def __init__(self):
        self.insert_sql = """insert into Products(Nid,UserId,Title,ImageUrl,ContentUrl,Price,Sales,CommentCount,Species) 
                                         values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        self.query_sql = 'select * from Products where nid = %s'
        self.update_sql = 'update Products set Price=%s,Sales=%s,CommentCount=%s where nid=%s'
        self.mysql = Mysql()
        self.cookie = RedisString('TaoBaoCookies').GetCkooie_Requests()
        self.User_Agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'

    def Login(self):
        username = '15170499385'  # 淘宝用户名
        pwd = 'Gao1262177832'  # 密码
        url = 'https://login.taobao.com/member/login.jhtml?spm=a21bo.2017.754894437.1.5af911d9c5CrsK&f=top&redirectURL=https%3A%2F%2Fwww.taobao.com%2F'
        loop = asyncio.get_event_loop()  # 协程，开启个无限循环的程序流程，把一些函数注册到事件循环上。当满足事件发生的时候，调用相应的协程函数。
        loop.run_until_complete(main(username, pwd, url))  # 将协程注册到事件循环，并启动事件循环

    def GetProductList(self, url):
        headers = {
            'cookie': self.cookie,
            'User-Agent': self.User_Agent,
            'Host': 's.taobao.com',
        }
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                return r.text
        except requests.exceptions.TooManyRedirects:
            print('cookie错误')
            self.Login()
            print('已更新cookie')
            try:
                r = requests.get(url, headers=headers)
                if r.status_code==200:
                    return r.text
            except requests.exceptions.TooManyRedirects:
                print('获取cookie后再次请求错误')
                return False
        except socket.error:
            print('超时')
            print(traceback.format_exc())
            return False
        except :
            print('其他错误')
            print(traceback.format_exc())
            return False

    def process(self,i):
        title_rule = '\"raw_title\":\"(.*?)\",\"pic_url'
        self.title = re.search(title_rule, i).group(1)
        # print(title)
        nid_rule = '\"nid\":\"(\d+)'
        self.nid = re.search(nid_rule, i).group(1)
        # print(nid)
        user_id_rule = 'user_id\":\"(\d+)'
        self.user_id = re.search(user_id_rule, i).group(1)
        # print(user_id)
        pic_rule = '\"pic_url\":\"(.*?)\",\"detail_url'
        pic_url = re.search(pic_rule, i).group(1)
        self.pic_url = 'https:' + pic_url
        # print(pic_url)
        content_rule = '\"detail_url\":\"(.*?)\",\"view_price'
        content_url = re.search(content_rule, i).group(1)
        self.content_url = 'https:' + content_url
        # print(conent_url)
        price_rule = '\"view_price\":\"(\d+\.\d+)'
        self.price = float(re.search(price_rule, i).group(1))
        # print(price)
        sales_rule = '\"view_sales\":\"(\d+)'
        sales = re.search(sales_rule, i)
        if not sales:
            self.sales = 0
        else:
            self.sales = int(sales.group(1))
        # print(sales)
        comment_count_rule = 'comment_count\":\"(\d+)'
        comment_count = re.search(comment_count_rule, i)
        if not comment_count:
            self.comment_count = 0
        else:
            self.comment_count = int(comment_count.group(1))
        # print(comment_count)

    def Main(self, url, model):
        html = self.GetProductList(url)
        if html:
            print('返回商品列表')
            rule = '\"auctions\":(.*),\"recommendAuctions\"'
            patt = re.compile(rule)
            try:
                result = patt.search(html).group(1)
            except:
                login_rule = '登 录'
                err_rule = '亲，小二正忙，滑动一下马上回来'
                if re.search(login_rule,html):
                    print('登录请求')
                    self.Login()
                    print('已更新cookie')
                if re.search(err_rule,html):
                    print('亲，小二正忙，滑动一下马上回来')
                    loop = asyncio.get_event_loop()  # 协程，开启个无限循环的程序流程，把一些函数注册到事件循环上。当满足事件发生的时候，调用相应的协程函数。
                    loop.run_until_complete(main2(url))  # 将协程注册到事件循环，并启动事件循环
                return False
            else:
                start = time.time()
                result = result.replace(r'\u003d','=').replace(r'\u0026','&')
                test_rule = '\"i2iTags\":(.*?)\"risk\"'
                pa = re.compile(test_rule)
                q_sum = 0
                u_sum = 0
                s_sum = 0
                c_sum = 0
                for i in pa.findall(result):
                    print('在解析商品')
                    self.process(i)
                    one_info = [self.nid,self.user_id,self.title, self.pic_url,
                                self.content_url,self.price,self.sales,self.comment_count, model]

                    q_time = time.time()
                    result = self.mysql.Query(self.query_sql, [self.nid]) #根据nid查询
                    q_sum+=(time.time()-q_time)
                    if result:
                        if self.price != result[6] or self.sales != result[7] or self.comment_count !=result[8]:
                            u_time = time.time()
                            self.mysql.Update(self.update_sql, [self.price, self.sales,self.comment_count,self.nid])
                            u_sum+=(time.time()-u_time)
                    else:
                        s_time  = time.time()
                        self.mysql.Save(self.insert_sql,one_info)
                        s_sum+=(time.time()-s_time)
                    self.mysql.con.commit()
                    c_time = time.time()
                    # Comment(self.nid,self.user_id,self.content_url).main()
                    c_sum+=(time.time()-c_time)

                print('-----------------------------')
                print('查询一页数据耗时:%s' % q_sum)
                print('更新一页数据耗时:%s' % u_sum)
                print('保存一页数据耗时:%s' % s_sum)
                print('获取一页评论耗时:%s' % c_sum)
                print('处理一页商品总耗时:%s' % ((time.time() - start)))
                print('-----------------------------')
                return True

        else:
            print('未返回正确html')
            return False


if __name__=="__main__":

    spider = Spider()
    product_list = ['python']
    page = 10
    for model in product_list:
        for num in range(page):
            result = spider.Main('https://s.taobao.com/search?q=%s&s=%s' % (model, num * 44), model)
            if result:
                print('当前获取%s,第%s页成功,共%s页' % (model, (num + 1), (page * len(product_list))))
            else:
                print('当前获取%s,第%s页失败,共%s页' % (model, (num + 1), (page * len(product_list))))
                result = spider.Main('https://s.taobao.com/search?q=%s&s=%s' % (model, num * 44), model)

    print('爬取完成')
