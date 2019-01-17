#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/12/18

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from ..compat import quote_plus, urlopen, decodebytes, encodebytes, b
from Crypto.Hash import SHA, SHA256
import json
from datetime import datetime
from ..pay_error import PayError, PayValidationError, AliPayError


class AliPay(object):

    def __init__(self, config):
        self._appid = str(config['app_id'])
        self._app_notify_url = config['notify_url']
        self._app_private_key_path = config['private_key_path']
        self._app_public_key_path = config['public_key_path']
        self._sign_type = config.setdefault('sign_type', 'RSA2')
        self.debug = config.setdefault('debug', False)
        self._app_private_key = None
        self._alipay_public_key = None

        if self.debug:
            self._gateway = 'https://openapi.alipaydev.com/gateway.do'
        else:
            self._gateway = 'https://openapi.alipay.com/gateway.do'

        self._load_key()

    def __repr__(self):
        return 'ALI_PAY'

    def __unicode__(self):
        return 'ALI_PAY'

    def _load_key(self):
        # load private key
        with open(self._app_private_key_path) as fp:
            content = fp.read()
        self._app_private_key = RSA.importKey(content)

        # load public key
        with open(self._app_public_key_path) as fp:
            content = fp.read()
        self._alipay_public_key = RSA.importKey(content)

    def _sign(self, unsigned_string):
        """
        通过如下方法调试签名
        方法1
            key = rsa.PrivateKey.load_pkcs1(open(self._app_private_key_path).read())
            sign = rsa.sign(unsigned_string.encode('utf8'), key, 'SHA-1')
            # base64 编码，转换为unicode表示并移除回车
            sign = base64.encodebytes(sign).decode('utf8').replace('\n', "")
        方法2
            key = RSA.importKey(open(self._app_private_key_path).read())
            signer = PKCS1_v1_5.new(key)
            signature = signer.sign(SHA.new(unsigned_string.encode('utf8')))
            # base64 编码，转换为unicode表示并移除回车
            sign = base64.encodebytes(signature).decode('utf8').replace('\n', "")
        方法3
            echo 'abc' | openssl sha1 -sign alipay.key | openssl base64

        """
        # 开始计算签名
        key = self._app_private_key
        signer = PKCS1_v1_5.new(key)
        if self._sign_type == 'RSA':
            signature = signer.sign(SHA.new(b(unsigned_string)))
        else:
            signature = signer.sign(SHA256.new(b(unsigned_string)))
        # base64 编码，转换为unicode表示并移除回车
        sign = encodebytes(signature).decode('utf8').replace('\n', "")
        return sign

    def _ordered_data(self, data):
        complex_keys = [k for k, v in data.items() if isinstance(v, dict)]

        # 将字典类型的数据dump出来
        for key in complex_keys:
            data[key] = json.dumps(data[key], separators=(',', ':'))

        return sorted([(k, v) for k, v in data.items()])

    def build_body(
            self, method, biz_content, return_url=None, notify_url=None, append_auth_token=False
    ):
        data = {
            'app_id': self._appid,
            'method': method,
            'charset': 'utf-8',
            'sign_type': self._sign_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0',
            'biz_content': biz_content
        }
        if append_auth_token:
            data['app_auth_token'] = self.app_auth_token

        if return_url is not None:
            data['return_url'] = return_url

        if method in (
                'alipay.trade.app.pay', 'alipay.trade.wap.pay', 'alipay.trade.page.pay',
                'alipay.trade.pay', 'alipay.trade.precreate'
        ) and (notify_url or self._app_notify_url):
            data['notify_url'] = notify_url or self._app_notify_url

        return data

    def sign_data(self, data):
        data.pop('sign', None)
        # 排序后的字符串
        ordered_items = self._ordered_data(data)
        unsigned_string = '&'.join('{}={}'.format(k, v) for k, v in ordered_items)
        sign = self._sign(unsigned_string)
        quoted_string = '&'.join('{}={}'.format(k, quote_plus(v)) for k, v in ordered_items)

        # 获得最终的订单信息字符串
        signed_string = quoted_string + '&sign=' + quote_plus(sign)
        return signed_string

    def _verify(self, raw_content, signature):
        # 开始计算签名
        key = self._alipay_public_key
        signer = PKCS1_v1_5.new(key)
        if self._sign_type == 'RSA':
            digest = SHA.new()
        else:
            digest = SHA256.new()
        digest.update(raw_content.encode('utf8'))
        if signer.verify(digest, decodebytes(signature.encode('utf8'))):
            return True
        return False

    def verify(self, data):
        """
        验证签名是否正确
        """
        sign = data.pop('sign')
        if 'sign_type' in data:
            sign_type = data.pop('sign_type')
            if sign_type != self._sign_type:
                raise PayError('Unknown sign type: {}'.format(sign_type))
        # 排序后的字符串
        unsigned_items = self._ordered_data(data)
        message = '&'.join(u'{}={}'.format(k, v) for k, v in unsigned_items)
        res = self._verify(message, sign)
        if res:
            return data

    def trade_wap_pay(self, return_url=None, **kwargs):
        biz_content = {
            'subject': kwargs['subject'],
            'out_trade_no': kwargs['out_trade_no'],
            'total_amount': kwargs['total_fee'],
            'product_code': 'QUICK_WAP_PAY'
        }
        biz_content.update(kwargs)
        data = self.build_body(
            'alipay.trade.wap.pay',
            biz_content,
            return_url=return_url,
            notify_url=kwargs['notify_url'] if 'notify_url' in kwargs.keys()
            else self._app_notify_url
        )
        return self._gateway + '?' + self.sign_data(data)

    def trade_app_pay(self, **kwargs):
        biz_content = {
            'subject': kwargs['subject'],
            'out_trade_no': kwargs['out_trade_no'],
            'total_amount': kwargs['total_fee'],
            'product_code': 'QUICK_MSECURITY_PAY'
        }
        biz_content.update(kwargs)
        data = self.build_body('alipay.trade.app.pay', biz_content,
                               notify_url=kwargs['notify_url'] if 'notify_url' in kwargs.keys()
                               else self._app_notify_url)
        return self.sign_data(data)

    def trade_pc_pay(self, return_url=None, **kwargs):
        biz_content = {
            'subject': kwargs['subject'],
            'out_trade_no': kwargs['out_trade_no'],
            'total_amount': kwargs['total_fee'],
            'product_code': 'FAST_INSTANT_TRADE_PAY'
        }

        biz_content.update(kwargs)
        data = self.build_body(
            'alipay.trade.page.pay',
            biz_content,
            return_url=return_url,
            notify_url=kwargs['notify_url'] if 'notify_url' in kwargs.keys()
            else self._app_notify_url
        )
        return self._gateway + '?' +self.sign_data(data)

    def trade_query(self, **kwargs):
        """
        交易查询
        response = {
          'alipay_trade_query_response': {
            'trade_no': '2017032121001004070200176844',
            'code': '10000',
            'invoice_amount': '20.00',
            'open_id': '20880072506750308812798160715407',
            'fund_bill_list': [
              {
                'amount': '20.00',
                'fund_channel': 'ALIPAYACCOUNT'
              }
            ],
            'buyer_logon_id': 'csq***@sandbox.com',
            'send_pay_date': '2017-03-21 13:29:17',
            'receipt_amount': '20.00',
            'out_trade_no': 'out_trade_no15',
            'buyer_pay_amount': '20.00',
            'buyer_user_id': '2088102169481075',
            'msg': 'Success',
            'point_amount': '0.00',
            'trade_status': 'TRADE_SUCCESS',
            'total_amount': '20.00'
          },
          'sign': ""
        }
        """
        out_trade_no = kwargs.pop('out_trade_no', None)
        trade_no = kwargs.pop('trade_no', None)
        assert (out_trade_no is not None) or (trade_no is not None), \
            'Both trade_no and out_trade_no are None'

        biz_content = {}
        if out_trade_no:
            biz_content['out_trade_no'] = out_trade_no
        if trade_no:
            biz_content['trade_no'] = trade_no
        data = self.build_body('alipay.trade.query', biz_content)

        url = self._gateway + '?' + self.sign_data(data)
        raw_string = urlopen(url, timeout=15).read().decode('utf-8')
        return self._verify_and_return_sync_response(raw_string, 'alipay_trade_query_response')

    def trade_refund(self, **kwargs):
        out_trade_no = kwargs.pop('out_trade_no', None)
        trade_no = kwargs.pop('trade_no', None)
        refund_amount = kwargs.pop('refund_amount', 0)
        biz_content = {
            'refund_amount': refund_amount
        }
        biz_content.update(**kwargs)
        if out_trade_no:
            biz_content['out_trade_no'] = out_trade_no
        if trade_no:
            biz_content['trade_no'] = trade_no

        data = self.build_body('alipay.trade.refund', biz_content)

        url = self._gateway + '?' + self.sign_data(data)
        raw_string = urlopen(url, timeout=15).read().decode('utf-8')
        return self._verify_and_return_sync_response(raw_string, 'alipay_trade_refund_response')

    def trade_refund_query(self, **kwargs):
        out_trade_no = kwargs.pop('out_trade_no', None)
        trade_no = kwargs.pop('trade_no', None)
        out_request_no = kwargs.pop('trade_no', None)
        kwargs.setdefault('out_request_no', out_trade_no)
        assert (out_trade_no is not None) or (trade_no is not None), \
            'Both trade_no and out_trade_no are None'

        biz_content = {'out_request_no': out_request_no}
        if trade_no:
            biz_content['trade_no'] = trade_no
        else:
            biz_content['out_trade_no'] = out_trade_no

        data = self.build_body('alipay.trade.fastpay.refund.query', biz_content)

        url = self._gateway + '?' + self.sign_data(data)
        raw_string = urlopen(url, timeout=15).read().decode('utf-8')
        return self._verify_and_return_sync_response(
            raw_string, 'alipay_trade_fastpay_refund_query_response'
        )

    def trade_cancel(self, **kwargs):
        """
        response = {
        'alipay_trade_cancel_response': {
            'msg': 'Success',
            'out_trade_no': 'out_trade_no15',
            'code': '10000',
            'retry_flag': 'N'
          }
        }
        """
        out_trade_no = kwargs.pop('out_trade_no', None)
        trade_no = kwargs.pop('trade_no', None)
        assert (out_trade_no is not None) or (trade_no is not None), \
            'Both trade_no and out_trade_no are None'

        biz_content = {}
        if out_trade_no:
            biz_content['out_trade_no'] = out_trade_no
        if trade_no:
            biz_content['trade_no'] = trade_no

        data = self.build_body('alipay.trade.cancel', biz_content)

        url = self._gateway + '?' + self.sign_data(data)
        raw_string = urlopen(url, timeout=15).read().decode('utf-8')
        return self._verify_and_return_sync_response(raw_string, 'alipay_trade_cancel_response')

    def _verify_and_return_sync_response(self, raw_string, response_type):
        """
        return data if verification succeeded, else raise exception

        failed response is like
        {
          'alipay_trade_query_response': {
            'sub_code': 'isv.invalid-app-id',
            'code': '40002',
            'sub_msg': '无效的AppID参数',
            'msg': 'Invalid Arguments'
          }
        }
        """

        response = json.loads(raw_string)
        result = response[response_type]
        # raise exceptions
        if 'sign' not in response.keys():
            raise AliPayError(
                code=result.get('code', '0'),
                message=response
            )

        sign = response['sign']

        # locate string to be signed
        raw_string = self._get_string_to_be_signed(raw_string, response_type)

        if not self._verify(raw_string, sign):
            raise PayValidationError
        return result

    def _verify_and_return_sync_response(self, raw_string, response_type):
        """
        return data if verification succeeded, else raise exception

        failed response is like
        {
          'alipay_trade_query_response': {
            'sub_code': 'isv.invalid-app-id',
            'code': '40002',
            'sub_msg': '无效的AppID参数',
            'msg': 'Invalid Arguments'
          }
        }
        """

        response = json.loads(raw_string)
        result = response[response_type]
        # raise exceptions
        if 'sign' not in response.keys():
            raise PayError(
                code=result.get('code', '0'),
                message=response
            )

        sign = response['sign']

        # locate string to be signed
        raw_string = self._get_string_to_be_signed(raw_string, response_type)

        if not self._verify(raw_string, sign):
            raise PayValidationError
        return result

    def _get_string_to_be_signed(self, raw_string, response_type):
        """
        https://docs.open.alipay.com/200/106120
        从同步返回的接口里面找到待签名的字符串
        """
        balance = 0
        start = end = raw_string.find('{', raw_string.find(response_type))
        # 从response_type之后的第一个｛的下一位开始匹配，
        # 如果是｛则balance加1; 如果是｝而且balance=0，就是待验签字符串的终点
        for i, c in enumerate(raw_string[start + 1:], start + 1):
            if c == '{':
                balance += 1
            elif c == '}':
                if balance == 0:
                    end = i + 1
                    break
                balance -= 1
        return raw_string[start:end]
