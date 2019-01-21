#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/12/18

"""
 支付返回业务信息，主要用于支付查询
"""


class PayResponse(object):

    def __init__(self, builder):
        self.data = {}
        for key, value in builder.__dict__.items():
            setattr(self, key, value)
            self.data[key] = value

    class Builder(object):

        def out_trade_no(self, value):
            """
            商户订单号
            :param value:
            :return:
            """
            self.out_trade_no = value
            return self

        def trade_no(self, value):
            """
            平台订单号
            :param value:
            :return:
            """
            self.trade_no = value
            return self

        def refund_amount(self, value):
            """
            退款金额
            :param value:
            :return:
            """
            self.refund_amount = value
            return self

        def out_request_no(self, value):
            """
            请求退款接口时，传入的退款请求号(支付宝)
            :param value:
            :return:
            """
            self.out_request_no = value
            return self

        def build(self):
            return PayResponse(self)
