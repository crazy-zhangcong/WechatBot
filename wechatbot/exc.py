# -*- coding:utf-8 -*-
from enum import Enum


class BotErrorCode(Enum):

    MISSING_PARAMETER = 0
    UNKNOWN_COMMAND = 1
    RESERVED_COMMAND = 2
    DUPLICATED_COMMAND = 3
    SEND_MSG_ERROR = 4
    LOGIN_ERROR = 5
    GET_UUID_ERROR = 6
    SYNC_ERROR = 7
    SYNC_CHECK_ERROR = 8
    SYNC_HOST_CHECK_ERROR = 9
    BOT_INIT_ERROR = 10
    SNAPSHOT_EXPIRED = 11


TRANSLATIONS = {
    BotErrorCode.MISSING_PARAMETER: '参数不全',
    BotErrorCode.UNKNOWN_COMMAND: '对不起，您的命令不能识别。',
    BotErrorCode.RESERVED_COMMAND: '对不起，这是一个保留关键字。',
    BotErrorCode.DUPLICATED_COMMAND: '已经存在相同命令',
    BotErrorCode.SEND_MSG_ERROR: '发送消息失败',
    BotErrorCode.LOGIN_ERROR: '登录失败',
    BotErrorCode.GET_UUID_ERROR: '获取uuid失败',
    BotErrorCode.SYNC_CHECK_ERROR: '同步检查失败',
    BotErrorCode.SYNC_HOST_CHECK_ERROR: '同步HOST失败',
    BotErrorCode.BOT_INIT_ERROR: '初始化失败',
    BotErrorCode.SYNC_ERROR: '同步失败',
    BotErrorCode.SNAPSHOT_EXPIRED: '对话已经过期，需要重新登录'
}


class BotException(Exception):

    def __init__(self, err_code, err_msg=None):
        self.err_code = err_code
        self.err_msg = err_msg

    def __str__(self):
        return repr(self.err_msg if self.err_msg else
                    TRANSLATIONS[self.err_code])


class BotUserExceptioin(BotException):
    pass


class BotSystemException(BotException):
    pass


class BotServerException(BotException):
    pass
