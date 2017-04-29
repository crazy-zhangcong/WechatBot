# -*- coding:utf-8 -*-
import os
import io
import json
import random
import re
import thread
import time
import urllib
import pickle
import xml.dom.minidom

import qrcode
import requests

from wechatbot.exc import BotServerException, BotErrorCode
from wechatbot.tools import create_logger

now = lambda: int(time.time())

directory = os.path.dirname(os.path.abspath(__file__))
PKL_FILE = '{directory}/wechat.pkl'.format(directory=directory)

WECHAT_APP_ID = 'wx782c26e4c19acffb'
WECHAT_FIRST_LOGIN_URL = 'https://login.weixin.qq.com/jslogin'
WECHAT_QR_CODE_STRING = 'https://login.weixin.qq.com/l/{}'
WECHAT_SECONT_LOGIN_URL = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip={tip}&uuid={uuid}&_={now}'
WECHAT_BOT_RUNNING = '机器人已经启动啦！你可以发送`ping`给机器人，机器人会回复哦。'
WECHAT_BOT_SYNC_CHECK_URL = 'https://{sync_host}/cgi-bin/mmwebwx-bin/synccheck?{params}'
WECHAT_BOT_SYNC_URL = '{base_uri}/webwxsync?sid={sid}&skey={skey}&lang=en_US&pass_ticket={pass_ticket}'
WECHAT_INIT_URL = '{base_uri}/webwxinit?r={r}i&lang=en_US&pass_ticket={pass_ticket}'

UPLOAD_IMG_URL = 'https://sm.ms/api/upload'

MSG = '{color}{content}{nc}'

RED = '\033[0;31m'
GREEN = '\033[0;32m'
NC = '\033[0m'  # No Color

red_alert = lambda content: MSG.format(color=RED, content=content, nc=NC)
green_alert = lambda content: MSG.format(color=GREEN, content=content, nc=NC)


WECHAT_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4',
    'cache-control': 'max-age=0',
    'host': 'login.wx.qq.com',
    'content-type': 'application/json; charset=UTF-8',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
}

WECHAT_SEND_MSG_HEADER = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4',
    'cache-control': 'max-age=0',
    'content-type': 'application/json; charset=UTF-8',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
}


class WechatBot(object):

    def __init__(self):

        self.session = requests.Session()
        self.params = dict()

        self.params['uuid'] = None
        self.params['base_uri'] = None
        self.params['base_host'] = None

        self.params['skey'] = None
        self.params['sid'] = None
        self.params['uin'] = None
        self.params['pass_ticket'] = None
        self.params['device_id'] = 'e' + repr(random.random())[2:17]

        self.params['base_host'] = None
        self.params['base_request'] = None
        self.params['sync_host'] = None
        self.params['sync_key'] = None
        self.params['sync_key_str'] = None

        self.func = None

    def read_snapshot(self):
        with open(PKL_FILE, 'r') as fp:
            self.params = pickle.load(fp)

    def save_snapshot(self):
        with open(PKL_FILE, 'w') as fp:
            pickle.dump(self.params, fp, protocol=2)

    def _get_qr_code(self):
        """
        生成微信登录二维码
        :return:
        """
        params = {
            'appid': WECHAT_APP_ID,
            'fun': 'new',
            'lang': 'zh_CN',
            '_': int(time.time()) * 1000 + random.randint(1, 999),
        }
        r = self.session.get(WECHAT_FIRST_LOGIN_URL, params=params)
        r.encoding = 'utf-8'
        data = r.text
        regex = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        pm = re.search(regex, data)
        if pm:
            code = pm.group(1)
            self.params['uuid'] = pm.group(2)
            assert code == '200'
        else:
            raise BotServerException(BotErrorCode.GET_UUID_ERROR)

        img = qrcode.make(WECHAT_QR_CODE_STRING.format(self.params['uuid']))
        img_in_memory = io.BytesIO()
        img.save(img_in_memory, 'png')
        img_in_memory.seek(0)
        files = {'smfile': img_in_memory}
        resp = requests.post(UPLOAD_IMG_URL, files=files)
        qr_code_url = json.loads(resp.content)['data']['url']
        self.logger.info(red_alert("请打开此网页并扫描二维码：{}".format(qr_code_url)))
        img_in_memory.truncate()

    def init(self):
        """
        初始化，在login之后来获取sync key
        :return:
        """
        url = WECHAT_INIT_URL.format(base_uri=self.params['base_uri'],
                                     r=int(time.time()),
                                     pass_ticket=self.params['pass_ticket'])
        params = {
            'BaseRequest': self.params['base_request']
        }
        r = self.session.post(url, data=json.dumps(params))
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        self.params['sync_key'] = dic['SyncKey']
        self.params['sync_key_str'] = '|'.join([str(keyVal['Key']) + '_' + str(keyVal['Val'])
                                                for keyVal in self.params['sync_key']['List']])
        return dic['BaseResponse']['Ret'] == 0

    def login(self, using_snap_shot=True):
        """
        登录
        :return:
        """
        self._get_qr_code() if not using_snap_shot else self.read_snapshot()

        redirect_url = None
        tip = 1

        while not redirect_url:
            url = WECHAT_SECONT_LOGIN_URL.format(tip=tip, uuid=self.params['uuid'], now=now())
            resp = self.session.get(url, headers=WECHAT_HEADERS)

            param = re.search(r'window.code=(\d+);', resp.text)
            code = param.group(1)

            if code == '201':
                tip = 0
            elif code == '200':
                redirect_urls = re.search(r'\"(?P<redirect_url>.*)\"', resp.content)
                if redirect_urls:
                    redirect_url = redirect_urls.group('redirect_url') + '&fun=new'
                    self.params['base_uri'] = redirect_url[:redirect_url.rfind('/')]
                    temp_host = self.params['base_uri'][8:]
                    self.params['base_host'] = temp_host[:temp_host.find("/")]
            elif code == '400':
                raise BotServerException(BotErrorCode.SNAPSHOT_EXPIRED)
            else:
                tip = 1

        resp = self.session.get(redirect_url)

        doc = xml.dom.minidom.parseString(resp.text.encode('utf-8'))
        root = doc.documentElement

        for node in root.childNodes:
            if node.nodeName == 'skey':
                self.params['skey'] = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                self.params['sid'] = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                self.params['uin'] = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                self.params['pass_ticket'] = node.childNodes[0].data
        if all([self.params['skey'], self.params['sid'], self.params['uin'], self.params['pass_ticket']]):
            self.params['base_request'] = {
                'DeviceID': self.params['device_id'],
                'Sid': self.params['sid'],
                'Skey': self.params['skey'],
                'Uin': self.params['uin']
            }
            self.init()
            self.save_snapshot()
            return True
        raise BotServerException(BotErrorCode.LOGIN_ERROR)

    def sync_check(self):
        """
        sync check.
        """

        params = {
            'r': now(),
            'skey': self.params['skey'],
            'sid': self.params['sid'],
            'uin': self.params['uin'],
            'deviceid': self.params['device_id'],
            'synckey': self.params['sync_key_str'],
            '_': now()
        }

        url = WECHAT_BOT_SYNC_CHECK_URL.format(sync_host=self.params['sync_host'], params=urllib.urlencode(params))

        while True:
            try:
                r = self.session.get(url, timeout=20)
                r.encoding = 'utf-8'
                data = r.text
                pm = re.search(r'window.synccheck=\{retcode:"(\d+)",selector:"(\d+)"\}', data)
                retcode = pm.group(1)
                selector = pm.group(2)
                return [retcode, selector]
            except requests.exceptions.ReadTimeout:
                # This is a normal response. Just ignore this exception.
                pass
            except:
                raise BotServerException(BotErrorCode.SYNC_CHECK_ERROR)

    def sync_host_check(self):
        for host1 in ['webpush.', 'webpush2.']:
            self.params['sync_host'] = host1 + self.params['base_host']
            try:
                code, selector = self.sync_check()
                if code == '0':
                    return True
            except Exception as e:
                self.logger.info(e)
        raise BotServerException(BotErrorCode.SYNC_HOST_CHECK_ERROR)

    def sync(self):
        url = WECHAT_BOT_SYNC_URL.format(base_uri=self.params['base_uri'],
                                         sid=self.params['sid'],
                                         skey=self.params['skey'],
                                         pass_ticket=self.params['pass_ticket'])

        params = {
            'BaseRequest': self.params['base_request'],
            'SyncKey': self.params['sync_key'],
            'rr': ~int(time.time())
        }
        try:
            r = self.session.post(url, data=json.dumps(params), timeout=60)
            r.encoding = 'utf-8'
            dic = json.loads(r.text)
            if dic['BaseResponse']['Ret'] == 0:
                self.params['sync_key'] = dic['SyncKey']
                self.params['sync_key_str'] = '|'.join(str(data['Key']) + '_' + str(data['Val'])
                                                       for data in self.params['sync_key']['List'])
            return dic
        except Exception:
            raise BotServerException(BotErrorCode.SYNC_ERROR)

    def proc_msg(self):

        self.sync_host_check()

        while True:
            check_time = now()
            self.sync_check()
            msg = self.sync()
            try:
                self.handle_msg(msg)
            except Exception as e:
                self.logger.info(e)
            check_time = now() - check_time
            if check_time < 1:
                time.sleep(1 - check_time)
            self.save_snapshot()

    def handle_msg(self, msgs):
        for msg in msgs["AddMsgList"]:
            if ':<br/>!' in msg['Content']:
                _, msg['Content'] = msg['Content'].split('<br/>', 1)
            self.logger.info(green_alert(msg['Content']))
            response = self.call(msg['Content'])
            if not msg['Content'] or not response:
                continue
            reply = {
                'BaseRequest': self.params['base_request'],
                'Msg': {
                    'Type': 1,
                    'Content': response,
                    'FromUserName': msg['ToUserName'],
                    'ToUserName': msg['FromUserName']
                },
                'Scene': msg['RecommendInfo']['Scene']
            }
            try:
                self.send_msg(reply)
            except Exception as e:
                reply['Msg']['Content'] = 'error occurs: {}'.format(e)
                self.send_msg(reply)

    def text_reply(self, _func):
        """
        后续应该把发送消息的用户信息也附上，以及群组
        继承类应该重新这个方法
        :return:
        """
        self.func = _func

        def func_wrapper(_func):
            self.logger.info('loading func:{}'.format(_func.__name__))
            return _func
        return func_wrapper

    def call(self, msg):
        return self.func(msg)

    def send_msg(self, reply):
        url = self.params['base_uri'] + '/webwxsendmsg'
        msg_id = str(now() * 1000) + str(random.random())[:5].replace('.', '')
        reply['Msg'].update({'LocalId': msg_id, 'ClientMsgId': msg_id})
        data = json.dumps(reply, ensure_ascii=False).encode('utf-8')
        # i haven't figured out, but you have to do this...
        # i assume, the host option is used to route. So, you have to remove host before post request
        for i in range(5):
            try:
                r = self.session.post(url, data=data, headers=WECHAT_SEND_MSG_HEADER)
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                pass
            if r.status_code == 200:
                return
        raise BotServerException(BotErrorCode.SEND_MSG_ERROR)

    @property
    def logger(self):
        """Create a logger for Bot
        """
        with thread.allocate_lock():
            return create_logger(self.__class__.__name__)

    def run(self):
        try:
            self.login(using_snap_shot=True)
        except:
            self.login(using_snap_shot=False)
        self.logger.info(green_alert(WECHAT_BOT_RUNNING))
        self.proc_msg()
