"""Response and notification data models for the ZPay API."""

from dataclasses import dataclass, field


@dataclass
class PaymentResponse:
    """Successful response from the API interface payment (mapi.php)."""

    trade_no: str
    """ZPay internal order number (O_id alias)."""

    O_id: str
    """ZPay internal numeric order ID."""

    payurl: str = ""
    """Direct payment redirect URL (if provided)."""

    qrcode: str = ""
    """QR code content URL (if provided)."""

    img: str = ""
    """QR code image URL (if provided)."""


@dataclass
class OrderResponse:
    """Response from a single-order query (api.php?act=order)."""

    trade_no: str
    """ZPay order number."""

    out_trade_no: str
    """Merchant order number."""

    type: str
    """Payment method (e.g. alipay, wxpay)."""

    pid: str
    """Merchant ID."""

    name: str
    """Product name."""

    money: str
    """Order amount."""

    status: int
    """Payment status: 1 = paid, 0 = unpaid."""

    addtime: str = ""
    """Order creation time."""

    endtime: str = ""
    """Transaction completion time."""

    param: str = ""
    """Business extension parameters."""

    buyer: str = ""
    """Payer account (may be blank)."""


@dataclass
class RefundResponse:
    """Response from a refund submission (api.php?act=refund)."""

    msg: str
    """Human-readable result message."""


@dataclass
class NotificationPayload:
    """Parsed and verified payment callback notification."""

    pid: str
    """Merchant ID."""

    name: str
    """Product name."""

    money: str
    """Order amount."""

    out_trade_no: str
    """Merchant order number."""

    trade_no: str
    """ZPay order number."""

    trade_status: str
    """Payment status string; 'TRADE_SUCCESS' means success."""

    type: str
    """Payment method."""

    sign: str
    """Original signature from ZPay."""

    param: str = ""
    """Business extension parameters (returned as-is)."""

    @property
    def is_paid(self) -> bool:
        """Returns True if the transaction was successfully completed."""
        return self.trade_status == "TRADE_SUCCESS"
