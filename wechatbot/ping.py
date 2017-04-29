# -*- coding:utf-8 -*-
from wechatbot import WechatBot

bot = WechatBot()


@bot.text_reply
def ping(msg):
    print msg
    if msg == 'ping':
        return 'pong'

if __name__ == '__main__':
    bot.run()
