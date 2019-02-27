#coding=utf-8

from redis import StrictRedis
import json
import pymysql


class RedisString():
    def __init__(self,key,value=None):
        self.con = StrictRedis(host='203.195.171.237', port=6379, password='1262177832')
        self.key = key
        self.value = value
    def GetCkooie_Requests(self):
        result = self.con.get(self.key)
        cookies = ''
        for cook in json.loads(result):
            cookie = '{0}={1};'
            cookie = cookie.format(cook.get('name'), cook.get('value'))
            cookies += cookie
        return cookies
    def GetCkooie_Pyppeteer(self):
        result = self.con.get(self.key)
        return json.loads(result)

    def Setcookie(self):
        last = self.GetCkooie_Pyppeteer()
        self.con.set(self.key,self.value)
        now = self.GetCkooie_Pyppeteer()
        if last != now:
            print('保存cookie成功')
        else:
            print('保存cookie不成功')



class Mysql():
    def __init__(self):
        self.con = pymysql.connect(
            host='cdb-b8p0y5al.gz.tencentcdb.com', port=10063, db='TaoBao',
            user='root', passwd='@Gao1262177832', charset='utf8')
        self.cur = self.con.cursor()

    def Save(self,sql,args):
        try:
            self.cur.execute(sql, args)
        except:
            with open('数据不能保存到数据库.txt','a+') as f:
                f.write(args[4]+'\n')

    def Query(self,sql,args):
        self.cur.execute(sql,args)
        result = self.cur.fetchone()
        return result
    def Query_all(self,sql,args):
        self.cur.execute(sql, args)
        result = self.cur.fetchall()
        return result

    def Update(self,sql,args):
        self.cur.execute(sql, args)
    def close(self):
        self.cur.close()
        self.con.close()

    """
    create table Comments( id int auto_increment primary key,
                          ProductId int,
                          foreign key(ProductId) REFERENCES Products(id) on delete CASCADE,
                          Nid varchar(20) not null,
                          CommentId varchar(20) not null UNIQUE,
                          Tag varchar(20),
                          TagId varchar(20),
                          Content text,
                          Reply text,
                          AppendComment text,
                          Positions varchar(50))
    """

    """
    create table Products( id int auto_increment primary key,
                            Nid varchar(20) not null,
                            UserId varchar(20),
                            Title text,
                            ImageUrl text,
                            ContentUrl text,
                            Price int,
                            Sales int,
                            CommentCount int,
                            Species varchar(50))
    """
