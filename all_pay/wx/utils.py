#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2019/1/17

import socket
import string
import random

from ..compat import b


def get_external_ip():
    """
    外部ip
    :return:
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        wechat_ip = socket.gethostbyname('api.mch.weixin.qq.com')
        sock.connect((wechat_ip, 80))
        addr, port = sock.getsockname()
        sock.close()
        return addr
    except socket.error:
        return '127.0.0.1'


def nonce_str(length=32):
    """
    随机字符串
    :param length:
    :return:
    """
    char = string.ascii_letters + string.digits
    return "".join(random.choice(char) for _ in range(length))


def random_num(length):
    """
    随机数字
    :param length:
    :return:
    """
    digit_list = list(string.digits)
    random.shuffle(digit_list)
    return ''.join(digit_list[:length])


def dict_to_xml(raw):
    s = ""
    for k, v in raw.iteritems():
        s += '<{0}>{1}</{0}>'.format(k, b(v), k)
    return '<xml>{0}</xml>'.format(s)
