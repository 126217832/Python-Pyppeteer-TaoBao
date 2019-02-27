#coding=utf-8

import traceback
import asyncio
import time,random
from time import sleep
from pyppeteer.launcher import launch # 控制模拟浏览器用
from retrying import retry #设置重试次数用的
from TaoBaoDB import RedisString
import json

async def main(username, pwd, url):# 定义main协程函数，
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
    await page.goto(url) # 访问登录页面
    await Js(page) #替换JS
    await asyncio.sleep(5)
    await page.waitFor('#J_Quick2Static')
    # await page.click('#J_Quick2Static')
    await page.type('#TPL_username_1', username, {'delay': input_time_random() - 50})
    print('正在输入密码')
    await page.type('#TPL_password_1', pwd, {'delay': input_time_random()})
    print('账号密码已输入')
    await asyncio.sleep(2)
    # 检测页面是否有滑块。原理是检测页面元素。
    await process_slider(page,pwd)
    await browser.close()


async def process_slider(page,pwd):

    slider = await page.Jeval('#nocaptcha', 'node => node.style')  # 是否有滑块
    if slider:
        print('当前页面出现滑块')
        flag, page = await mouse_slide(page=page)  # js拉动滑块过去。
        await asyncio.sleep(1)
        if flag:
            await page.evaluate('''document.getElementById("J_SubmitStatic").click()''')
            if await affirm(page):  # 确认是否需要手机验证
                await asyncio.sleep(3)
                await get_cookie(page)  # 导出cookie 完成登陆后就可以拿着cookie玩各种各样的事情了。
                return True
        else:
            print('滑动失败')

    else:
        await page.evaluate('''document.getElementById("J_SubmitStatic").click()''')
        await page.waitFor(20)
        await page.waitForNavigation()
        slider = await page.Jeval('#nocaptcha', 'node => node.style')  # 是否有滑块
        if slider:
            print('正在输入密码')
            await page.type('#TPL_password_1', pwd, {'delay': input_time_random()})
            flag, page = await mouse_slide(page=page)  # js拉动滑块过去。
            if flag:
                await page.evaluate('''document.getElementById("J_SubmitStatic").click()''')
                print("print enter")
                if await affirm(page):  # 确认是否需要手机验证
                    await get_cookie(page)  # 导出cookie 完成登陆后就可以拿着cookie玩各种各样的事情了。
            else:
                print('滑动失败')

        else:
            if await affirm(page):  # 确认是否需要手机验证
                await asyncio.sleep(2)
                await get_cookie(page)  # 导出cookie 完成登陆后就可以拿着cookie玩各种各样的事情了。

# 获取登录后cookie
async def get_cookie(page):
    cookies_list = await page.cookies()
    key = 'TaoBaoCookies'
    value = cookies_list
    RedisString(key, json.dumps(value)).Setcookie()
    print('已保存cookie')

def retry_if_result_none(result):
    return result is None

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

async def affirm(page):
    await asyncio.sleep(5)
    flag = 0
    try:
        iframe = page.frames
        if len(iframe) == 0:
            raise TypeError
        for i in iframe:
            flag+=1
            if  await i.querySelector('#J_GetCode'):
                print('存在')
                await i.evaluate('''document.getElementById("J_GetCode").click()''')  # 点击获取验证码
                print('需要手机号验证')
                cap = str(input('cat:'))
                await i.type('#J_Phone_Checkcode', cap, {'delay': input_time_random()})  # 输入验证码
                await i.evaluate('''document.getElementById('submitBtn').click()''') # 确定
                await asyncio.sleep(2)
                return True
            if flag == len(iframe):
                raise TypeError

    except:
        print(traceback.format_exc())
        print('不需要手机号验证')
        return True

@retry(retry_on_result=retry_if_result_none,)
async def mouse_slide(page=None):
    await asyncio.sleep(2)
    try :
        #鼠标移动到滑块，按下，滑动到头（然后延时处理），松开按键
        sleep(1)
        print('准备滑动')
        await page.hover('#nc_1_n1z') # 不同场景的验证码模块能名字不同
        print('按下')
        await page.mouse.down()
        print('滑动')
        await page.mouse.move(2000, 0, {'delay': random.randint(2000, 3000)})
        print('松开')
        await page.mouse.up()
    except Exception as e:
        print(e, ':验证失败')
        print(traceback.format_exc())
        return 0,page
    else:
        sleep(2)
        # 判断是否通过
        try:
            slider_again = await page.Jeval('.nc-lang-cnt', 'node => node.textContent')
            if slider_again != '验证通过':
                print('验证不通过')
                return None, page
            else:
                await page.screenshot({'path': 'headless-slide-result.png'})  # 截图测试
                print('验证通过')
                return 1, page
        except:
            return 1, page

def input_time_random():
    return random.randint(100, 151)


if __name__ == '__main__':
    username = '15170499385' # 淘宝用户名
    pwd = 'Gao1262177832' #密码
    url = 'https://login.taobao.com/member/login.jhtml?spm=a21bo.2017.754894437.1.5af911d9c5CrsK&f=top&redirectURL=https%3A%2F%2Fwww.taobao.com%2F'
    loop = asyncio.get_event_loop()  #协程，开启个无限循环的程序流程，把一些函数注册到事件循环上。当满足事件发生的时候，调用相应的协程函数。
    loop.run_until_complete(main(username, pwd, url))  #将协程注册到事件循环，并启动事件循环