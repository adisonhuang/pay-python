#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/12/18

import string
import random
import urllib2
import hashlib
import requests
import time
from ..pay_error import PayError, PayValidationError, WxPayError

import xmltodict
from xml.parsers.expat import ExpatError
from .. import logger
from .utils import nonce_str, random_num, dict_to_xml, get_external_ip
from ..compat import b


class WxPay(object):
    API_BASE_URL = 'https://api.mch.weixin.qq.com'

    def __init__(self, config):
        self.opener = urllib2.build_opener(urllib2.HTTPSHandler())
        self._appid = str(config['app_id'])
        self._app_notify_url = config['notify_url']
        self._mch_id = config['mch_id']
        self._mch_key = config['mch_key']
        self._appsecret = config['app_secret']
        # 证书pem格式
        self._api_cert_path = config['api_cert_path']
        # 证书密钥pem格式
        self._api_key_path = config['api_key_path']

    def __repr__(self):
        return 'WX_PAY'

    def __unicode__(self):
        return 'WX_PAY'

    def verify(self, data):
        """
        验证签名是否正确
        """
        return self._parse_pay_result(data)

    def _parse_pay_result(self, xml):
        """解析微信支付结果通知"""
        try:
            data = xmltodict.parse(xml)
        except (xmltodict.ParsingInterrupted, ExpatError):
            raise PayValidationError()

        if not data or 'xml' not in data:
            raise PayValidationError()

        data = data['xml']
        sign = data.pop('sign', None)
        real_sign = self._sign(data)
        if sign != real_sign:
            raise PayValidationError()
        return data

    def _sign(self, raw):
        """
        生成签名
        参考微信签名生成算法
        https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=4_3
        """
        raw = [(k, str(raw[k]) if isinstance(raw[k], (int, float)) else raw[k]) for k in sorted(raw.keys())]
        s = '&'.join('='.join(kv) for kv in raw if kv[1])
        s += '&key={0}'.format(self._mch_key)
        return hashlib.md5(b(s)).hexdigest().upper()

    def _fetch(self, url, data):
        req = urllib2.Request(url, data=dict_to_xml(data))
        try:
            resp = self.opener.open(req, timeout=20)
        except urllib2.HTTPError, e:
            resp = e
        re_info = resp.read()
        return self._handle_result(re_info)

    def _fetch_with_ssl(self, url, data, api_client_cert_path, api_client_key_path):
        req = requests.post(url, data=dict_to_xml(data),
                            cert=(api_client_cert_path, api_client_key_path))
        return self._handle_result(req.content)

    def _unified_order(self, **data):
        """
        统一下单接口
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_1
        :param trade_type: 交易类型，取值如下：JSAPI，NATIVE，APP，WAP, MWEB
        :param body: 商品描述
        :param total_fee: 总金额，单位分
        :param notify_url: 接收微信支付异步通知回调地址
        :param client_ip: 可选，APP和网页支付提交用户端ip，Native支付填调用微信支付API的机器IP
        :param user_id: 可选，用户在商户appid下的唯一标识。trade_type=JSAPI和appid已设定，此参数必传
        :param sub_user_id: 可选，小程序appid下的唯一标识。trade_type=JSAPI和sub_appid已设定，此参数必传
        :param out_trade_no: 可选，商户订单号，默认自动生成
        :param detail: 可选，商品详情
        :param attach: 可选，附加数据，在查询API和支付通知中原样返回，该字段主要用于商户携带订单的自定义数据
        :param fee_type: 可选，符合ISO 4217标准的三位字母代码，默认人民币：CNY
        :param time_start: 可选，订单生成时间，默认为当前时间
        :param time_expire: 可选，订单失效时间，默认为订单生成时间后两小时
        :param goods_tag: 可选，商品标记，代金券或立减优惠功能的参数
        :param product_id: 可选，trade_type=NATIVE，此参数必传。此id为二维码中包含的商品ID，商户自行定义
        :param device_info: 可选，终端设备号(门店号或收银设备ID)，注意：PC网页或公众号内支付请传"WEB"
        :param limit_pay: 可选，指定支付方式，no_credit--指定不能使用信用卡支付
        :param scene_info: 可选，上报支付的场景信息
        :type scene_info: dict
        :return: 返回的结果数据
        """
        url = '{url}/pay/unifiedorder'.format(url=self.API_BASE_URL)

        # 必填参数
        if 'out_trade_no' not in data:
            raise PayError(message='miss parameter out_trade_no')
        if 'body' not in data:
            raise PayError(message='miss parameter body')
        if 'total_fee' not in data:
            raise PayError(message='miss parameter total_fee')
        if 'trade_type' not in data:
            raise PayError(message='miss parameter trade_type')

        # 关联参数
        if data['trade_type'] == 'JSAPI' and 'openid' not in data:
            raise PayError(message='miss parameter openid')
        if data['trade_type'] == 'NATIVE' and 'product_id' not in data:
            raise PayError(message='miss parameter product_id')

        data.setdefault('appid', self._appid)
        data.setdefault('mch_id', self._mch_id)
        data.setdefault('notify_url', self._app_notify_url)
        data.setdefault('nonce_str', nonce_str())
        external_ip = '127.0.0.0.1'
        if 'spbill_create_ip' not in data:
            external_ip = get_external_ip()
        data.setdefault('spbill_create_ip', external_ip)
        data.setdefault('sign', self._sign(data))

        raw = self._fetch(url, data)
        if raw['return_code'] == 'FAIL':
            raise PayError(raw['return_msg'])
        err_msg = raw.get('err_code_des')
        if err_msg:
            raise PayError(err_msg)
        return raw

    def _handle_result(self, xml):
        logger.debug('Response from WeChat API \n %s', xml)
        try:
            data = xmltodict.parse(xml)['xml']
        except (xmltodict.ParsingInterrupted, ExpatError):
            # 解析 XML 失败
            logger.debug('WeChat payment result xml parsing error', exc_info=True)
            return xml

        return_code = data['return_code']
        return_msg = data.get('return_msg')
        result_code = data.get('result_code')
        errcode = data.get('err_code')
        errmsg = data.get('err_code_des')
        if return_code != 'SUCCESS' or result_code != 'SUCCESS':
            # 返回状态码不为成功
            raise WxPayError(
                return_code,
                result_code,
                return_msg,
                errcode,
                errmsg,
            )
        return data

    def _verify_return_data(self, data):
        return_code = data['return_code']
        return_msg = data.get('return_msg')
        result_code = data.get('result_code')
        errcode = data.get('err_code')
        errmsg = data.get('err_code_des')
        if return_code != 'SUCCESS' or result_code != 'SUCCESS':
            # 返回状态码不为成功
            raise WxPayError(
                return_code,
                result_code,
                return_msg,
                errcode,
                errmsg,
            )
        return data

    def trade_app_pay(self, **kwargs):
        """
        生成给app调用的数据
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/app/app.php?chapter=9_12&index=2

        :param kwargs:  body, total_fee
            body: 商品名称
            total_fee: 标价金额, 整数, 单位 分
            out_trade_no: 商户订单号, 若未传入则自动生成
        :return: 生成微信app接口支付所需的信息
        """
        kwargs.setdefault('trade_type', 'APP')
        subject = kwargs.pop('subject')
        kwargs['body'] = subject
        if 'out_trade_no' not in kwargs:
            kwargs.setdefault('out_trade_no', nonce_str())
        raw = self._unified_order(**kwargs)
        timestamp = int(time.time())
        # 返回参数列表，参考https://pay.weixin.qq.com/wiki/doc/api/app/app.php?chapter=9_12&index=2
        res = dict(appid=self._appid, partnerid=self._mch_id, prepayid=raw['prepay_id'],
                   package='Sign=WXPay', noncestr=nonce_str(), timestamp=str(timestamp))
        sign = self._sign(res)
        res['sign'] = sign
        return res

    def trade_wap_pay(self, return_url=None, **kwargs):
        subject = kwargs.pop('subject')
        kwargs['body'] = subject
        kwargs.setdefault('trade_type', 'MWEB')
        if 'out_trade_no' not in kwargs:
            kwargs.setdefault('out_trade_no', nonce_str())
        raw = self._unified_order(**kwargs)
        return raw['mweb_url'] + '&redirect_url=' + return_url

    def trade_page_pay(self, **kwargs):
        subject = kwargs.pop('subject')
        kwargs['body'] = subject
        kwargs.setdefault('trade_type', 'NATIVE')
        if 'out_trade_no' not in kwargs:
            kwargs.setdefault('out_trade_no', nonce_str())
        raw = self._unified_order(**kwargs)
        return raw['code_url']

    def trade_js_pay(self, **kwargs):
        """
        生成给JavaScript调用的数据
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=7_7&index=6

        :param kwargs: openid, body, total_fee
            openid: 用户openid
            body: 商品名称
            total_fee: 标价金额, 整数, 单位 分
            out_trade_no: 商户订单号, 若未传入则自动生成
        :return: 生成微信JS接口支付所需的信息
        """
        nonce = nonce_str()
        subject = kwargs.pop('subject')
        kwargs['body'] = subject
        kwargs.setdefault("trade_type", "JSAPI")
        if "out_trade_no" not in kwargs:
            kwargs.setdefault("out_trade_no", nonce)
        raw = self._unified_order(**kwargs)
        package = "prepay_id={0}".format(raw["prepay_id"])
        timestamp = int(time.time())
        raw = dict(appId=self._appid, timeStamp=timestamp,
                   nonceStr=nonce, package=package, signType="MD5")
        sign = self._sign(raw)
        return dict(package=package, appId=self._appid,
                    timeStamp=timestamp, nonceStr=nonce, sign=sign)

    def trade_query(self, **kwargs):
        """
        订单查询
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/app/app.php?chapter=9_2&index=4

        :return: 订单查询结果
        """
        url = '{url}/pay/orderquery'.format(url=self.API_BASE_URL)
        trade_no = kwargs.pop('trade_no', None)
        kwargs['transaction_id'] = trade_no
        kwargs.setdefault('appid', self._appid)
        kwargs.setdefault('mch_id', self._mch_id)
        kwargs.setdefault('nonce_str', nonce_str())
        kwargs.setdefault('sign', self._sign(kwargs))

        data = self._fetch(url, kwargs)
        return self._verify_return_data(data)

    def trade_cancel(self, **kwargs):
        """
        关闭订单
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_3

        :param out_trade_no: 商户订单号
        :return: 申请关闭订单结果
        """
        url = '{url}/pay/closeorder'.format(url=self.API_BASE_URL)
        out_trade_no = kwargs.pop('out_trade_no', None)
        data = {
            'out_trade_no': out_trade_no,
            'appid': self._appid,
            'mch_id': self._mch_id,
            'nonce_str': nonce_str(),
        }
        data['sign'] = self._sign(data)
        res = self._fetch(url, data)
        return self._verify_return_data(res)

    def trade_refund(self, api_cert_path, api_key_path, **kwargs):
        """
        申请退款
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_4

        :param api_cert_path: 微信支付商户证书路径，此证书(apiclient_cert.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        :param api_key_path: 微信支付商户证书路径，此证书(apiclient_key.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        :param data: out_trade_no、transaction_id至少填一个, out_refund_no, total_fee, refund_fee
            out_trade_no: 商户订单号
            transaction_id: 微信订单号
            out_refund_no: 商户退款单号（若未传入则自动生成）
            total_fee: 订单金额
            refund_fee: 退款金额
        :return: 退款申请返回结果
        """
        url = '{url}/secapi/pay/refund'.format(url=self.API_BASE_URL)
        trade_no = kwargs.pop('trade_no', None)
        kwargs['transaction_id'] = trade_no
        kwargs.setdefault('appid', self._appid)
        kwargs.setdefault('mch_id', self._mch_id)
        kwargs.setdefault('op_user_id', self._mch_id)
        kwargs.setdefault('nonce_str', nonce_str())
        kwargs.setdefault('sign', self._sign(kwargs))

        data = self._fetch_with_ssl(url, kwargs, api_cert_path, api_key_path)
        return self._verify_return_data(data)

    def trade_refund_query(self, **kwargs):
        """
        查询退款
        提交退款申请后，通过调用该接口查询退款状态。退款有一定延时，
        用零钱支付的退款20分钟内到账，银行卡支付的退款3个工作日后重新查询退款状态。
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_5

        :param data: out_refund_no、out_trade_no、transaction_id、refund_id四个参数必填一个
            out_refund_no: 商户退款单号
            out_trade_no: 商户订单号
            transaction_id: 微信订单号
            refund_id: 微信退款单号

        :return: 退款查询结果
        """
        url = '{url}/secapi/pay/refundquery'.format(url=self.API_BASE_URL)
        trade_no = kwargs.pop('trade_no', None)
        kwargs['transaction_id'] = trade_no
        kwargs.setdefault('appid', self._appid)
        kwargs.setdefault('mch_id', self._mch_id)
        kwargs.setdefault('nonce_str', nonce_str())
        kwargs.setdefault('sign', self._sign(kwargs))

        data = self._fetch(url, kwargs)
        return self._verify_return_data(data)

    def enterprise_pay(self, **kwargs):
        """
        使用企业对个人付款功能
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/tools/mch_pay.php?chapter=14_2

        :param api_cert_path: 微信支付商户证书路径，此证书(apiclient_cert.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        :param api_key_path: 微信支付商户证书路径，此证书(apiclient_key.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        :param data: openid, check_name, re_user_name, amount, desc, spbill_create_ip
            openid: 用户openid
            check_name: 是否校验用户姓名
            re_user_name: 如果 check_name 为True，则填写，否则不带此参数
            amount: 金额: 企业付款金额，单位为分
            desc: 企业付款描述信息
            spbill_create_ip: 调用接口的机器Ip地址
        :return: 企业转账结果
        """
        url = '{url}/mmpaymkttransfers/promotion/transfers'.format(url=self.API_BASE_URL)
        kwargs.setdefault('mch_appid', self._appid)
        kwargs.setdefault('mchid', self._mch_id)
        kwargs.setdefault('nonce_str', nonce_str())
        kwargs.setdefault('check_name', False)
        total_fee = kwargs.pop('total_fee', None)
        kwargs['amount'] = total_fee
        out_trade_no = kwargs.pop('out_trade_no', None)
        kwargs['partner_trade_no'] = out_trade_no
        kwargs.setdefault('partner_trade_no', u'{0}{1}{2}'.format(
            self._mch_id, time.strftime('%Y%m%d', time.localtime(time.time())), random_num(10)
        ))
        kwargs['check_name'] = 'FORCE_CHECK' if kwargs['check_name'] else 'NO_CHECK'
        kwargs.setdefault('sign', self._sign(kwargs))

        data = self._fetch_with_ssl(url, kwargs, self._api_cert_path, self._api_key_path)
        return self._verify_return_data(data)
