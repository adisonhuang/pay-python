#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/12/18


def _get_pay(config):
    import_me = config['pay_type']
    from . import pay_type
    try:
        pay_obj = getattr(pay_type, import_me)
    except AttributeError:
        raise ImportError("%s is not a valid PAY TYPE" % (
            import_me))

    return pay_obj(config)


class Pay(object):

    def __init__(self, config):
        self.pay = _get_pay(config)

    def trade_wap_pay(self, pay_order, **kwargs):
        """
        wap支付
        :param pay_order:
        :param kwargs:
        :return:
        """
        kwargs = dict(pay_order.data, **kwargs)
        return self.pay.trade_wap_pay(**kwargs)

    def trade_app_pay(self, pay_order, **kwargs):
        """
        app支付
        :param pay_order:
        :param kwargs:
        :return:
        """
        kwargs = dict(pay_order.data, **kwargs)
        return self.pay.trade_app_pay(**kwargs)

    def trade_pc_pay(self, pay_order, **kwargs):
        """
        pc支付
        :param pay_order:
        :param kwargs:
        :return:
        """
        kwargs = dict(pay_order.data, **kwargs)
        return self.pay.trade_pc_pay(**kwargs)

    def trade_js_pay(self, pay_order, **kwargs):
        """
        js支付
        :param pay_order:
        :param kwargs:
        :return:
        """
        from wx import WxPay
        from pay_error import PayError
        if not isinstance(self.pay, WxPay):
            raise PayError('%s have not a valid method'.format(self.pay))
        kwargs = dict(pay_order.data, **kwargs)
        return self.pay.trade_js_pay(**kwargs)

    def parse_and_verify_result(self, args):
        """
        异步通知校验
        :param args: 对应平台返回的原始数据
        :return:
        """
        return self.pay.verify(args)

    def trade_query(self, pay_response, **kwargs):
        """
        订单查询
        :param pay_response:
        :param kwargs:
        :return:
        """
        kwargs = dict(pay_response.data, **kwargs)
        return self.pay.trade_query(**kwargs)

    def trade_refund(self, pay_response, **kwargs):
        """
        退款
        :param pay_response:
        :param kwargs:
        :return:
        """
        kwargs = dict(pay_response.data, **kwargs)
        return self.pay.trade_refund(**kwargs)

    def trade_refund_query(self, pay_response, **kwargs):
        """
        退款查询
        :param pay_response:
        :param kwargs:
        :return:
        """
        kwargs = dict(pay_response.data, **kwargs)
        return self.pay.trade_refund_query(**kwargs)

    def trade_cancel(self, pay_response, **kwargs):
        """
        订单取消
        :param pay_response:
        :param kwargs:
        :return:
        """
        kwargs = dict(pay_response.data, **kwargs)
        return self.pay.trade_cancel(**kwargs)

    def enterprise_payment(self, pay_order, **kwargs):
        kwargs = dict(pay_order.data, **kwargs)
        from wx import WxPay
        from pay_error import PayError
        if not isinstance(self.pay, WxPay):
            raise PayError('%s have not a valid method'.format(self.pay))
        return self.pay.enterprise_payment(**kwargs)
