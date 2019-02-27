#coding=utf-8
import re
import requests
import json
from TaoBaoGetCookie import main
from TaoBaoDB import RedisString,Mysql
from TaoBaoSlidingValidation import main2
import asyncio
import traceback
from time import sleep



class Comment():
    def __init__(self,nid,sellerId,content_url):
        self.nid = nid
        self.tag_url = 'https://rate.tmall.com/listTagClouds.htm?itemId=%s&isAll=true'%self.nid
        self.sellerId = sellerId
        self.content_url = content_url
        self.mysql = Mysql()
        self.cookie = RedisString('TaoBaoCookies').GetCkooie_Requests()
        self.User_Agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
        self.query_sql = 'select * from Comments where CommentId=%s'
        self.query_id_sql = 'select id from Products where Nid=%s'
        self.insert_sql = """insert into Comments(ProductId,Nid,CommentId,Tag,TagId,Content,Reply,AppendComment,Positions) 
                             values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    def main(self):
        print('获取商品评论信息')
        r = requests.get(self.tag_url, headers={'User-Agent':self.User_Agent})
        print('---------------------------------------')
        print(r.text)
        print('---------------------------------------')
        if r.status_code == 200:
            print('获取评论标签')
            Tag = json.loads(r.text.replace('(', '').replace(')', ''))
            tagClouds = Tag.get("tags").get("tagClouds")
            if tagClouds:
                for tag in tagClouds:
                    if '一般' in tag.get('tag'):
                        self.Tag = tag.get('tag')
                        self.tag_id = str(tag.get("id"))
                        self.posi = tag.get("posi")
                        if self.posi:
                            self.posi=1
                        else:
                            self.posi=-1
                        count = tag.get("count")
                        if int(count) == 0:
                            break
                        if int(count)%10 > 0:
                            page = (int(count) // 10) + 1
                        else:
                            page = (int(count) // 10)
                        for num in range(1,page+1):
                            print('正在获取第%s页评论'%num)
                            self.comment_url = 'https://rate.tmall.com/list_detail_rate.htm?itemId=%s&sellerId=%s&order=3&currentPage=%s&tagId=%s&posi=%s'%(self.nid,self.sellerId,num,self.tag_id,self.posi)
                            self.comment()

    def Login(self):
        username = '15170499385'  # 淘宝用户名
        pwd = 'Gao1262177832'  # 密码
        url = 'https://login.taobao.com/member/login.jhtml?spm=a21bo.2017.754894437.1.5af911d9c5CrsK&f=top&redirectURL=https%3A%2F%2Fwww.taobao.com%2F'
        loop = asyncio.get_event_loop()  # 协程，开启个无限循环的程序流程，把一些函数注册到事件循环上。当满足事件发生的时候，调用相应的协程函数。
        loop.run_until_complete(main(username, pwd, url))  # 将协程注册到事件循环，并启动事件循环


    def process(self):
        try:
            print('解析一页评论列表')
            rateList = self.result.get('rateDetail').get('rateList')
            for i in rateList:
                content = i.get('rateContent')
                # dirty_stuff = ["👎","😠","😡"]
                # for stuff in dirty_stuff:
                #     content = content.replace(stuff, "")
                # print(content)
                comment_id = str(i.get('id'))
                reply = i.get('reply')
                if i.get('appendComment'):
                    appendComment = i.get('appendComment').get('content')
                else:
                    appendComment=None
                positions  = i.get('position')
                try:
                    query_result = self.mysql.Query(self.query_sql,[comment_id])
                    if not query_result:
                        ProductsId = self.mysql.Query(self.query_id_sql,[self.nid]) #查询Products表的id
                        args = [ProductsId[0],self.nid, comment_id, self.Tag, self.tag_id, content, reply, appendComment, positions]
                        self.mysql.Save(self.insert_sql, args)
                except:
                    print(traceback.format_exc())
            self.mysql.con.commit()
            print('保存一页评论')
            return True
        except:
            return False

    def comment_unit(self):
        headers = {
            'cookie': self.cookie,
            'User-Agent': self.User_Agent,
            'Host' : 'rate.tmall.com'
        }
        comment_r = requests.get(self.comment_url, headers=headers).text
        rule = '\((.*?)\)'
        try:
            result = re.search(rule, comment_r).group(1)
            try:
                self.result = json.loads(result)
                if self.process():
                    return True
                else:
                    return False
            except:
                print('评论数据不能被转化为json')
                with open('评论数据不能被转化为json.txt', 'a+') as f:
                    f.write(comment_r + '\n')
                return False

        except:
            print('评论数据获取错误')
            with open('评论数据获取错误.txt', 'a+') as f:
                f.write(comment_r + '\n')
            return False

    def comment(self):
        try:
            if not self.comment_unit():
                raise AttributeError
            else:
                return True
        except:
            print('需要验证')
            loop = asyncio.get_event_loop()  # 协程，开启个无限循环的程序流程，把一些函数注册到事件循环上。当满足事件发生的时候，调用相应的协程函数。
            loop.run_until_complete(main2(self.content_url))  # 将协程注册到事件循环，并启动事件循环
            sleep(2)
            self.comment_unit()
