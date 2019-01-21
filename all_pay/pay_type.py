#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/12/18

from .ali import AliPay
from .wx import WxPay

__all__ = ('ali_pay', 'wx_pay')


def ali_pay(config):
    return AliPay(config)


def wx_pay(config):
    return WxPay(config)
