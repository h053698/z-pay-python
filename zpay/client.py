"""ZPay async API client.

Usage::

    async with ZPayClient(pid="your_pid", key="your_key") as client:
        # 1. Generate a redirect payment URL (no HTTP request)
        url = client.create_payment_url(
            name="iPhone 17",
            money="599.00",
            out_trade_no="ORDER_001",
            notify_url="https://yoursite.com/notify",
            return_url="https://yoursite.com/return",
            type="alipay",
        )

        # 2. API payment (returns payurl / qrcode / img)
        resp = await client.create_payment(
            name="iPhone 17",
            money="599.00",
            out_trade_no="ORDER_002",
            notify_url="https://yoursite.com/notify",
            clientip="1.2.3.4",
            type="alipay",
        )

        # 3. Query order status
        order = await client.query_order(out_trade_no="ORDER_002")

        # 4. Refund
        refund = await client.refund(out_trade_no="ORDER_002", money="599.00")

        # 5. Verify notification callback
        payload = client.verify_notification(request_params)
        if payload.is_paid:
            ...
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import aiohttp

from .exceptions import ZPayAPIError, ZPaySignatureError
from .models import (
    NotificationPayload,
    OrderResponse,
    PaymentResponse,
    RefundResponse,
)
from .signature import generate_sign, verify_sign


class ZPayClient:
    """Asynchronous client for the ZPay payment gateway.

    Args:
        pid: Merchant unique identifier.
        key: Merchant secret key used for MD5 signing.
        base_url: ZPay API base URL (default: ``https://zpayz.cn``).
        session: Optional existing ``aiohttp.ClientSession``. If not provided,
            a new session is created and managed internally.
    """

    DEFAULT_BASE_URL = "https://zpayz.cn"

    def __init__(
        self,
        pid: str,
        key: str,
        base_url: str = DEFAULT_BASE_URL,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.pid = pid
        self.key = key
        self.base_url = base_url.rstrip("/")
        self._session = session
        self._owned_session = session is None  # True if we should close it

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "ZPayClient":
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._owned_session and self._session is not None:
            await self._session.close()
            self._session = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _active_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError(
                "ZPayClient must be used as an async context manager "
                "(async with ZPayClient(...) as client)"
            )
        return self._session

    def _sign(self, params: dict[str, Any]) -> dict[str, Any]:
        """Attach signature fields to *params* and return the updated dict."""
        params["sign"] = generate_sign(params, self.key)
        params["sign_type"] = "MD5"
        return params

    async def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with self._active_session.post(url, data=data) as resp:
            resp.raise_for_status()
            result: dict[str, Any] = await resp.json(content_type=None)
        return result

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with self._active_session.get(url, params=params) as resp:
            resp.raise_for_status()
            result: dict[str, Any] = await resp.json(content_type=None)
        return result

    @staticmethod
    def _check_response(data: dict[str, Any]) -> None:
        """Raise ZPayAPIError if the response indicates failure."""
        code = data.get("code")
        if str(code) != "1":
            raise ZPayAPIError(
                message=data.get("msg", "Unknown error"),
                code=str(code) if code is not None else None,
            )

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def create_payment_url(
        self,
        *,
        name: str,
        money: str,
        out_trade_no: str,
        notify_url: str,
        return_url: str,
        type: str,
        cid: str = "",
        param: str = "",
    ) -> str:
        """Build a signed redirect URL for front-end payment (submit.php).

        No HTTP request is made; the returned URL can be used directly in a
        browser redirect or ``<form action="...">`` submission.

        Args:
            name: Product name.
            money: Order amount (max 2 decimal places).
            out_trade_no: Unique merchant order number (max 32 chars).
            notify_url: Server async callback URL.
            return_url: Browser redirect URL after payment.
            type: Payment method (``"alipay"`` or ``"wxpay"``).
            cid: Optional payment channel ID(s), comma-separated.
            param: Optional extra parameter returned as-is in callback.

        Returns:
            Fully signed URL string.
        """
        params: dict[str, Any] = {
            "pid": self.pid,
            "name": name,
            "money": money,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "return_url": return_url,
            "type": type,
        }
        if cid:
            params["cid"] = cid
        if param:
            params["param"] = param

        self._sign(params)
        return f"{self.base_url}/submit.php?{urlencode(params)}"

    async def create_payment(
        self,
        *,
        name: str,
        money: str,
        out_trade_no: str,
        notify_url: str,
        clientip: str,
        type: str,
        cid: str = "",
        device: str = "PC",
        param: str = "",
    ) -> PaymentResponse:
        """Create a payment via the server-to-server API (mapi.php).

        Args:
            name: Product name.
            money: Order amount (max 2 decimal places, unit: CNY).
            out_trade_no: Unique merchant order number (max 32 chars).
            notify_url: Server async notification URL.
            clientip: IP address of the end-user initiating payment.
            type: Payment method (``"alipay"`` or ``"wxpay"``).
            cid: Optional payment channel ID(s), comma-separated.
            device: Device type (e.g. ``"PC"``, ``"H5"``).
            param: Optional extra parameter returned as-is in callback.

        Returns:
            :class:`PaymentResponse` with order and redirect/QR information.

        Raises:
            ZPayAPIError: If the API returns a non-success response.
        """
        data: dict[str, Any] = {
            "pid": self.pid,
            "name": name,
            "money": money,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "clientip": clientip,
            "type": type,
            "device": device,
        }
        if cid:
            data["cid"] = cid
        if param:
            data["param"] = param

        self._sign(data)
        result = await self._post("/mapi.php", data)
        self._check_response(result)

        return PaymentResponse(
            trade_no=result.get("trade_no", ""),
            O_id=result.get("O_id", ""),
            payurl=result.get("payurl", ""),
            qrcode=result.get("qrcode", ""),
            img=result.get("img", ""),
        )

    async def query_order(
        self,
        *,
        out_trade_no: str = "",
        trade_no: str = "",
    ) -> OrderResponse:
        """Query the status of a single order.

        At least one of *out_trade_no* or *trade_no* must be provided.

        Args:
            out_trade_no: Merchant order number.
            trade_no: ZPay system order number.

        Returns:
            :class:`OrderResponse` with full order details.

        Raises:
            ValueError: If neither identifier is supplied.
            ZPayAPIError: If the API returns a non-success response.
        """
        if not out_trade_no and not trade_no:
            raise ValueError("Provide at least one of: out_trade_no, trade_no")

        params: dict[str, Any] = {
            "act": "order",
            "pid": self.pid,
            "key": self.key,
        }
        if out_trade_no:
            params["out_trade_no"] = out_trade_no
        if trade_no:
            params["trade_no"] = trade_no

        result = await self._get("/api.php", params)
        self._check_response(result)

        return OrderResponse(
            trade_no=result.get("trade_no", ""),
            out_trade_no=result.get("out_trade_no", ""),
            type=result.get("type", ""),
            pid=result.get("pid", ""),
            name=result.get("name", ""),
            money=result.get("money", ""),
            status=int(result.get("status", 0)),
            addtime=result.get("addtime", ""),
            endtime=result.get("endtime", ""),
            param=result.get("param", ""),
            buyer=result.get("buyer", ""),
        )

    async def refund(
        self,
        *,
        money: str,
        out_trade_no: str = "",
        trade_no: str = "",
    ) -> RefundResponse:
        """Submit a refund request.

        At least one of *out_trade_no* or *trade_no* must be provided.

        Args:
            money: Refund amount (must match original order amount for most channels).
            out_trade_no: Merchant order number.
            trade_no: ZPay order number.

        Returns:
            :class:`RefundResponse` confirming the refund result.

        Raises:
            ValueError: If neither order identifier is supplied.
            ZPayAPIError: If the API returns a non-success response.
        """
        if not out_trade_no and not trade_no:
            raise ValueError("Provide at least one of: out_trade_no, trade_no")

        data: dict[str, Any] = {
            "act": "refund",
            "pid": self.pid,
            "key": self.key,
            "money": money,
        }
        if out_trade_no:
            data["out_trade_no"] = out_trade_no
        if trade_no:
            data["trade_no"] = trade_no

        result = await self._post("/api.php?act=refund", data)
        self._check_response(result)

        return RefundResponse(msg=result.get("msg", "Refund successful"))

    def verify_notification(
        self, params: dict[str, Any]
    ) -> NotificationPayload:
        """Verify and parse a payment callback notification.

        Call this method with the raw GET parameters received on your
        ``notify_url`` endpoint. Signature validation is performed
        automatically before the payload is returned.

        Args:
            params: Raw dict of query parameters from the callback request.

        Returns:
            :class:`NotificationPayload` if signature is valid.

        Raises:
            ZPaySignatureError: If the signature does not match.
        """
        if not verify_sign(params, self.key):
            raise ZPaySignatureError(
                "Notification signature verification failed. "
                "The request may have been tampered with."
            )

        return NotificationPayload(
            pid=str(params.get("pid", "")),
            name=str(params.get("name", "")),
            money=str(params.get("money", "")),
            out_trade_no=str(params.get("out_trade_no", "")),
            trade_no=str(params.get("trade_no", "")),
            trade_status=str(params.get("trade_status", "")),
            type=str(params.get("type", "")),
            sign=str(params.get("sign", "")),
            param=str(params.get("param", "")),
        )
