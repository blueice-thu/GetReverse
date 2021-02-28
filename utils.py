from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from browsermobproxy import Server
import os, requests
from time import sleep

DEVIDER = '$$$$$$$$$$$$$$$$'

HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Cookie': 'll="118318"; bid=VphkMecYUeI; __yadk_uid=RmReW2rcZ2z0mvK7XU2Hk5lbJRkh9Xmt; viewed="1140457"; gr_user_id=06ee0f44-322d-4247-93ac-de144da52338; _vwo_uuid_v2=DC05E55FE4B8188FEF5DD65F5152BE5D2|7eed6e6d696f6c06984eef171f438b14; __utmz=30149280.1576832766.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmc=30149280; dbcl2="2241899:Qr3KzLK8mY4"; push_doumail_num=0; push_noty_num=0; __utmv=30149280.224; ck=QxRM; douban-fav-remind=1; __gads=ID=c2c2b4d1b545c075:T=1576833631:S=ALNI_ManfN_EbMMtHwjeyAGIuRlVSkk3kw; _pk_ses.100001.8cb4=*; ap_v=0,6.0; __utma=30149280.426358312.1576832766.1576840609.1576845825.3; __utmt=1; loc-last-index-location-id="118318"; _pk_id.100001.8cb4=9fac3e30c5487d2c.1576832764.3.1576845892.1576840608.; __utmb=30149280.8.10.1576845825',
    'Host': 'reserves.lib.tsinghua.edu.cn',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.81',
    'X-Requested-With': 'XMLHttpRequest'
}

SLEEP_TIME = 2

def get_book_info(USERID, PASSWORD, BOOKID):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    browser = webdriver.Chrome(chrome_options=chrome_options)
    browser.delete_all_cookies()
    browser.get('http://reserves.lib.tsinghua.edu.cn/Home')
    sleep(SLEEP_TIME)

    login = browser.find_element_by_xpath('/html/body/div/div[2]/div/a[10]')
    login.click()
    sleep(SLEEP_TIME)
    user = browser.find_element_by_xpath(r'//*[@id="i_user"]')
    user.click()
    user.send_keys(USERID)
    password = browser.find_element_by_xpath(r'//*[@id="i_pass"]')
    password.click()
    password.send_keys(PASSWORD)
    browser.find_element_by_xpath('//*[@id="theform"]/div[4]/a').click()
    sleep(SLEEP_TIME * 2)

    browser.get('http://reserves.lib.tsinghua.edu.cn/Search/BookDetail?bookId={}'.format(BOOKID))
    sleep(SLEEP_TIME)
    book_info = {}
    book_info['title'] = browser.find_element_by_xpath('/html/body/div/div[4]/div[2]/div[2]/table/tbody/tr[1]/td[2]/font/b').text
    contents = browser.find_element_by_xpath('/html/body/div/div[4]/div[2]/div[2]/p[2]')
    links = contents.find_elements_by_tag_name('a')
    book_info['chapters'] = [link.text.replace('/', '_').replace('\\', '_') for link in links]
    book_info['links'] = [link.get_attribute("href") for link in links]

    browser.find_element_by_class_name('btn-exit').click()
    browser.delete_all_cookies()
    browser.quit()

    return book_info

def prepareFolders(bookInfo: dict):
    if not os.path.isdir('./result'):
        os.mkdir('./result')
    for chapter in bookInfo['chapters']:
        folder = './result/{}'.format(chapter)
        if not os.path.isdir(folder):
            os.mkdir(folder)

def get_chapter_info(link):
    server = Server(r'.\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat')
    server.start()
    proxy = server.create_proxy()
    
    chrome_options = Options()
    chrome_options.add_argument('--headless --proxy-server={0}'.format(proxy.proxy))
    browser = webdriver.Chrome(chrome_options=chrome_options)

    proxy.new_har('blueice', options={'captureHeaders': True, 'captureContent': True})
    browser.get(link)
    sleep(SLEEP_TIME)
    page = len(browser.find_elements_by_class_name('item_focus')) // 2 * 4
    res = proxy.har
    for entry in res['log']['entries']:
        res_url = entry['request']['url']
        if "/files/mobile/1" in res_url:
            break

    sleep(SLEEP_TIME)
    browser.delete_all_cookies()
    browser.quit()
    server.stop()
    return page, res_url

def downloadChapter(page: int, url: str, chapter: str):
    for i in range(1, int(page) + 1):
        realurl = url.format(i)
        print(chapter + ' ' + str(i))
        picFile = './result./{}/{}.jpg'.format(chapter, i)
        if os.path.isfile(picFile):
            continue
        pic = requests.get(realurl, headers=HEADERS, timeout=50)
        fp2 = open(picFile, 'wb')
        fp2.write(pic.content)
        fp2.close()
        sleep(2)
