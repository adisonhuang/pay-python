#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/12/18

"""
 支付订单信息，主要用于支付下单
"""


class PayOrder(object):

    def __init__(self, builder):
        self.data = {}
        for key, value in builder.__dict__.items():
            setattr(self, key, value)
            self.data[key] = value

    class Builder(object):

        def subject(self, value):
            """
            商品名称
            :param value:
            :return:
            """
            self.subject = value
            return self

        def total_fee(self, value):
            """
            价格
            :param value:
            :return:
            """
            self.total_fee = value
            return self

        def out_trade_no(self, value):
            """
            商户订单号
            :param value:
            :return:
            """
            self.out_trade_no = value
            return self

        def openid(self, value):
            """
            微信专用 唯一标识
            :param value:
            :return:
            """
            self.openid = value
            return self

        def product_id(self, value):
            """
            微信专用 商品ID
            :param value:
            :return:
            """
            self.product_id = value
            return self

        def return_url(self, value):
            """
            同步通知页面
            :param value:
            :return:
            """
            self.return_url = value
            return self

        def notify_url(self, value):
            """
            异步通知页面，也可以从config中配置，如果同时存在，会使用在这里设置的值
            :param value:
            :return:
            """
            self.notify_url = value
            return self

        def build(self):
            return PayOrder(self)
