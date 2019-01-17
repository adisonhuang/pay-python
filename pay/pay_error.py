#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/12/18


class PayError(Exception):
    def __int__(self, code=-9001, message=None):
        self.__code = code
        self.__message = message

    def __repr__(self):
        return self.error_str()

    def __unicode__(self):
        return self.error_str()

    def error_str(self):
        return 'PayError: Error code: {code}, message: {msg}'.format(
            code=self.__code,
            msg=self.__message)


class PayValidationError(Exception):
    pass


class AliPayError(PayError):
    """支付宝支付异常"""

    def __init__(self, errcode, errmsg):
        super(AliPayError, self).__init__(errcode, errmsg)

    def __repr__(self):
        return self.error_str()

    def __unicode__(self):
        return self.error_str()

    def __str__(self):
        return self.error_str()

    def error_str(self):
        return 'AliPayError: Error code: {code}, message: {msg}'.format(
            code=self.__code,
            msg=self.__message)


class WxPayError(PayError):
    """微信支付异常"""

    def __init__(self, return_code, result_code=None, return_msg=None,
                 errcode=None, errmsg=None):
        """
        :param return_code: 返回状态码
        :param result_code: 业务结果
        :param return_msg: 返回信息
        :param errcode: 错误代码
        :param errmsg: 错误代码描述
        """
        super(WxPayError, self).__init__(errcode, errmsg)
        self.return_code = return_code
        self.result_code = result_code
        self.return_msg = return_msg

    def __repr__(self):
        return self.error_str()

    def __unicode__(self):
        return self.error_str()

    def __str__(self):
        return self.error_str()

    def error_str(self):
        return 'WeChatPayError: Error code: {code}, message: {msg}. Pay Error code: {pay_code}, message: {pay_msg}'.format(
            code=self.return_code,
            msg=self.return_msg,
            pay_code=self.errcode,
            pay_msg=self.errmsg)
