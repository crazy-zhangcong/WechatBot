=========================
WechatBot
=========================

.. image:: https://travis-ci.org/chuanwu/WechatBot.svg?branch=master


*WechatBot* is a wechat bot built for geeks.

========================
 1. 快速上手
========================


---------------------
1.1 安装
---------------------

.. code-block:: python
       
       pip install wechatbot
 
---------------------
1.2 用法
---------------------

贴上示例代码， wechatbot/ping.py。

.. code-block:: python

    from wechatbot import WechatBot

    bot = WechatBot()


    @bot.text_reply
    def ping(msg):
        print msg
        if msg == 'ping':
            return 'pong'

    if __name__ == '__main__':
        bot.run()


扫描二维码之后，机器人就跑起来啦。
这时，可以向机器人发送一个ping的消息来看看服务是否正常。
对了，短暂退出不需要重新扫描二维码登录哦～

========================
2. 规划
========================

接下来会把Bot做成一个更加基础的服务，只对外暴露两个模块:

- 在接受指令之后发送定制消息

后续会增加session的概念，可能会支持AI，并通过向机器人发送消息来开关AI。

来自用户的每一条消息都是作为一个命令。


- 主动向某个用户发送消息


已支持pip安装，但是文档还没有更新，请fork后等待更新。如果你对这个项目有兴趣，啊哈，请通过chuanwusun@gmail.com或者扫描下方微信二维码联系我，独力难支，I NEED YOUR HELP.

.. image:: https://ooo.0o0.ooo/2017/04/16/58f30ae346d96.png

谢谢阅读！
