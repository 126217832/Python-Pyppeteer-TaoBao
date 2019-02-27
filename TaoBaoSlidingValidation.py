#coding=utf-8

import traceback
import asyncio
import random
from time import sleep
from pyppeteer.launcher import launch # 控制模拟浏览器用
from retrying import retry #设置重试次数用的
import json
from TaoBaoDB import RedisString

async def main2(url):# 定义main协程函数，
    #以下使用await 可以针对耗时的操作进行挂起
    # browser = await launch({'headless': False, 'devtools':False,'args': ['--no-sandbox'], }) # 启动pyppeteer 属于内存中实现交互的模拟器
    browser = await launch({
        'headless': False,
        'dumpio': True,
        'args': [
            '--disable-extensions',
            '--hide-scrollbars',
            '--disable-bundled-ppapi-flash',
            '--mute-audio',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-gpu',
        ],
    })
    page = await browser.newPage()  # 启动个新的浏览器页面
    await page.setViewport({'width': 1200, 'height': 800})
    await page.setUserAgent(
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36')

    key = 'TaoBaoCookies'
    for cookie in RedisString(key).GetCkooie_Pyppeteer():
        await page.setCookie(cookie)
    await page.goto(url)
    await asyncio.sleep(5)
    try:
        flag = False
        iframe = page.frames
        for frame in iframe:
            if await frame.title() == '亲，访问被拒绝':
                print('访问被拒绝')
                await page.evaluate('''document.getElementById("sufei-dialog-close").click()''')
                await asyncio.sleep(1)
                await page.evaluate('''window.scrollTo(0,1000)''')
                flag = True
                await asyncio.sleep(5)
                if await user_frame(page):
                    break
        if not flag:
            await page.evaluate('''window.scrollTo(0,1000)''')
        await asyncio.sleep(5)
        em = await page.querySelector('a[href="#J_Reviews"]')
        await em.click()
        await asyncio.sleep(15)
        if await user_frame(page):
            em = await page.querySelector('a[href="#"]')
            await em.click() #重新刷新页面
            await asyncio.sleep(1)
            await get_cookie(page)  # 导出cookie 完成登陆后就可以拿着cookie玩各种各样的事情了。

    except:
        print(traceback.format_exc())
        await Js(page)  # 替换JS
        if await Sliding(page,page):
            em = await page.querySelector('button[type="submit"]')
            await em.click()
            await asyncio.sleep(2)
            await get_cookie(page)  # 导出cookie 完成登陆后就可以拿着cookie玩各种各样的事情了。
        else:
            if await page.querySelector('button[type="submit"]'):
                await get_cookie(page)  # 导出cookie 完成登陆后就可以拿着cookie玩各种各样的事情了。
    await browser.close()

async def user_frame(page):
    iframe = page.frames
    for frame in iframe:
        if await frame.title() == '亲，访问受限了':
            print('访问受限')
            await asyncio.sleep(2)
            await Js(frame)  # 替换JS
            await frame.evaluate('''window.scrollTo(0,1000)''')
            if await Sliding(page,frame):
                await asyncio.sleep(2)
                return True
        if await frame.querySelector('#TPL_password_1'):
            print('访问需登录')
            await Js(frame)  # 替换JS
            await frame.evaluate('''window.scrollTo(0,1000)''')
            await asyncio.sleep(2)
            await frame.type('#TPL_password_1', 'Gao1262177832', {'delay': input_time_random()})
            await frame.evaluate('''document.getElementById("J_SubmitStatic").click()''')
            return True


async def Sliding(page,frame):
    # 检测页面是否有滑块。原理是检测页面元素。
    try:
        slider = await page.Jeval('#nocaptcha', 'node => node.style')  # 是否有滑块
        if slider:
            print('当前页面出现滑块')
            for i in range(2):
                flag, page = await mouse_slide(page,frame)  # js拉动滑块过去。
                if flag:
                    return True
                else:
                    print('滑动失败')
                    try:
                        em = await page.querySelector('a[href="javascript:noCaptcha.reset(1)"]')  # 点击获取验证码
                        await asyncio.sleep(1)
                        await em.click()
                    except:
                        pass
                if i == 1:
                    return False
    except:
        return False

def retry_if_result_none(result):
    return result is None

@retry(retry_on_result=retry_if_result_none)
async def mouse_slide(page,frame):
    await asyncio.sleep(2)
    try :
        #鼠标移动到滑块，按下，滑动到头（然后延时处理），松开按键
        print('准备滑动')
        await frame.hover('#nc_1_n1z')  # 不同场景的验证码模块能名字不同
        handler = page.mouse
        print('按下')
        await handler.down()
        print('滑动')
        await handler.move(2000, 0, {'delay': random.randint(3000, 4000)})
        print('松开')
        await handler.up()
    except Exception as e:
        print(e, ':验证失败')
        print(traceback.format_exc())
        if type(page) == type(frame): #都是主框架
            return 0,page
        else:
            return 0, frame
    else:
        sleep(2)
        # 判断是否通过
        try:
            slider_again = await page.Jeval('.nc-lang-cnt', 'node => node.textContent')
            if slider_again != '验证通过':
                print('验证不通过')
                if type(page) == type(frame):  # 都是主框架
                    return 0, page
                else:
                    return 0, frame
            else:
                print('验证通过')
                return 1, page
        except:
            return 1, page


# 获取登录后cookie
async def get_cookie(page):
    cookies_list = await page.cookies()
    key = 'TaoBaoCookies'
    value = cookies_list
    RedisString(key, json.dumps(value)).Setcookie()


async def Js(page):
    # 替换淘宝在检测浏览时采集的一些参数。
    # 就是在浏览器运行的时候，始终让window.navigator.webdriver=false
    # navigator是windiw对象的一个属性，同时修改plugins，languages，navigator 且让
    await page.evaluate(
        '''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }''')  # 以下为插入中间js，将淘宝会为了检测浏览器而调用的js修改其结果。
    await page.evaluate('''() =>{ window.navigator.chrome = { runtime: {},  }; }''')
    await page.evaluate('''() =>{ Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] }); }''')
    await page.evaluate('''() =>{ Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5,6], }); }''')
    # 使用type选定页面元素，并修改其数值，用于输入账号密码，修改的速度仿人类操作，因为有个输入速度的检测机制
    # 因为 pyppeteer 框架需要转换为js操作，而js和python的类型定义不同，所以写法与参数要用字典，类型导入

def input_time_random():
    return random.randint(100, 151)


if __name__ == '__main__':

    url = 'https://s.taobao.com/search?q=ipad&s=44'
    loop = asyncio.get_event_loop()  #协程，开启个无限循环的程序流程，把一些函数注册到事件循环上。当满足事件发生的时候，调用相应的协程函数。
    loop.run_until_complete(main2(url))  #将协程注册到事件循环，并启动事件循环