# zpay — ZPay Python SDK

> **English** | [中文](#zpay--zpay-python-sdk-中文)

Async Python client for the [ZPay](https://zpayz.cn) payment gateway. Supports Alipay and WeChat Pay via redirect URLs, server-to-server API calls, order queries, refunds, and callback verification.

---

## Installation

```bash
pip install zpay
```

**Requirements:** Python ≥ 3.10, `aiohttp`

---

## Quick Start

```python
import asyncio
from zpay import ZPayClient

async def main():
    async with ZPayClient(pid="your_pid", key="your_key") as client:

        # 1. Redirect URL (no HTTP request)
        url = client.create_payment_url(
            name="iPhone 17",
            money="599.00",
            out_trade_no="ORDER_001",
            notify_url="https://yoursite.com/notify",
            return_url="https://yoursite.com/return",
            type="alipay",
        )
        print("Pay URL:", url)

        # 2. API payment — returns payurl / qrcode / img
        resp = await client.create_payment(
            name="iPhone 17",
            money="599.00",
            out_trade_no="ORDER_002",
            notify_url="https://yoursite.com/notify",
            clientip="1.2.3.4",
            type="wxpay",
        )
        print("QR Code:", resp.qrcode)

        # 3. Query order
        order = await client.query_order(out_trade_no="ORDER_002")
        print("Status:", order.status)

        # 4. Refund
        refund = await client.refund(out_trade_no="ORDER_002", money="599.00")
        print(refund.msg)

        # 5. Verify callback notification
        payload = client.verify_notification(request_params)
        if payload.is_paid:
            print("Payment confirmed!")

asyncio.run(main())
```

---

## API Reference

### `ZPayClient(pid, key, base_url?, session?)`

| Parameter  | Type  | Description |
|------------|-------|-------------|
| `pid`      | `str` | Merchant ID |
| `key`      | `str` | Merchant secret key |
| `base_url` | `str` | API base URL (default: `https://zpayz.cn`) |
| `session`  | `aiohttp.ClientSession` | Optional existing session |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `create_payment_url(...)` | `str` | Build a signed redirect URL (no HTTP) |
| `create_payment(...)` | `PaymentResponse` | Server-to-server payment API |
| `query_order(...)` | `OrderResponse` | Query order status |
| `refund(...)` | `RefundResponse` | Submit refund request |
| `verify_notification(params)` | `NotificationPayload` | Validate and parse callback |

### Payment Types

| Value | Channel |
|-------|---------|
| `"alipay"` | Alipay |
| `"wxpay"` | WeChat Pay |

---

## License

MIT

---
---

# zpay — ZPay Python SDK 中文

> [English](#zpay--zpay-python-sdk) | **中文**

ZPay 支付网关的异步 Python 客户端，支持支付宝、微信支付的跳转收款、服务端 API 下单、订单查询、退款以及回调验签。

---

## 安装

```bash
pip install zpay
```

**环境要求：** Python ≥ 3.10，依赖 `aiohttp`

---

## 快速开始

```python
import asyncio
from zpay import ZPayClient

async def main():
    async with ZPayClient(pid="your_pid", key="your_key") as client:

        # 1. 生成跳转收款 URL（不发起 HTTP 请求）
        url = client.create_payment_url(
            name="iPhone 17",
            money="599.00",
            out_trade_no="ORDER_001",
            notify_url="https://yoursite.com/notify",
            return_url="https://yoursite.com/return",
            type="alipay",
        )
        print("支付链接：", url)

        # 2. 服务端 API 下单（返回 payurl / qrcode / img）
        resp = await client.create_payment(
            name="iPhone 17",
            money="599.00",
            out_trade_no="ORDER_002",
            notify_url="https://yoursite.com/notify",
            clientip="1.2.3.4",
            type="wxpay",
        )
        print("二维码：", resp.qrcode)

        # 3. 查询订单
        order = await client.query_order(out_trade_no="ORDER_002")
        print("订单状态：", order.status)

        # 4. 退款
        refund = await client.refund(out_trade_no="ORDER_002", money="599.00")
        print(refund.msg)

        # 5. 验证异步回调通知
        payload = client.verify_notification(request_params)
        if payload.is_paid:
            print("支付成功！")

asyncio.run(main())
```

---

## API 说明

### `ZPayClient(pid, key, base_url?, session?)`

| 参数 | 类型 | 说明 |
|------|------|------|
| `pid` | `str` | 商户 ID |
| `key` | `str` | 商户密钥 |
| `base_url` | `str` | API 基础地址（默认：`https://zpayz.cn`） |
| `session` | `aiohttp.ClientSession` | 可选，传入已有的 Session |

### 方法列表

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `create_payment_url(...)` | `str` | 生成带签名的跳转收款 URL（不请求网络） |
| `create_payment(...)` | `PaymentResponse` | 服务端 API 下单 |
| `query_order(...)` | `OrderResponse` | 查询订单状态 |
| `refund(...)` | `RefundResponse` | 发起退款 |
| `verify_notification(params)` | `NotificationPayload` | 验签并解析回调参数 |

### 支付方式

| 值 | 渠道 |
|----|------|
| `"alipay"` | 支付宝 |
| `"wxpay"` | 微信支付 |

---

## 开源协议

MIT
