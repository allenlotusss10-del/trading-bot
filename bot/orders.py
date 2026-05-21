from typing import Any, Dict, Optional

from .client import BinanceClient
from .logging_config import setup_logger
from .validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = setup_logger("orders")


# ---------------------------------------------------------------------------
# Order parameter builder
# ---------------------------------------------------------------------------

def build_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Construct the parameter dict required by the Binance Futures order endpoint.
    """
    params: Dict[str, Any] = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }

    if order_type == "LIMIT":
        params["price"] = price
        params["timeInForce"] = "GTC"  # Good Till Cancelled

    elif order_type == "STOP_MARKET":
        params["stopPrice"] = stop_price
        params["triggerPrice"] = stop_price

    logger.debug(f"Built order params: {params}")
    return params


# ---------------------------------------------------------------------------
# Main order placement entry point
# ---------------------------------------------------------------------------

def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate all user inputs, build the parameter payload, and call the client.
    Returns the raw API response dict on success.
    Raises ValueError for invalid inputs, or client exceptions for API/network errors.
    """
    # --- Validate ---
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    qty = validate_quantity(quantity)
    p = validate_price(price, order_type)
    sp = validate_stop_price(stop_price, order_type)

    log_msg = (
        f"Attempting {order_type} {side} order | "
        f"symbol={symbol} qty={qty}"
        + (f" price={p}" if p is not None else "")
        + (f" stopPrice={sp}" if sp is not None else "")
    )
    logger.info(log_msg)

    # --- Build & send ---
    params = build_order_params(symbol, side, order_type, qty, p, sp)
    response = client.place_order(params)

    logger.info(
        f"Order accepted | orderId={response.get('orderId')} "
        f"status={response.get('status')} executedQty={response.get('executedQty')}"
    )
    return response


# ---------------------------------------------------------------------------
# Response formatter
# ---------------------------------------------------------------------------

def format_order_response(response: Dict[str, Any]) -> str:
    """Return a human-readable summary of the order response."""
    avg_price = response.get("avgPrice") or "N/A"
    price_val = response.get("price") or "N/A"

    lines = [
        "",
        "╔══════════════════════════════════════════════╗",
        "║            ORDER RESPONSE SUMMARY            ║",
        "╠══════════════════════════════════════════════╣",
        f"║  Order ID    : {str(response.get('orderId', 'N/A')):<30}║",
        f"║  Symbol      : {str(response.get('symbol', 'N/A')):<30}║",
        f"║  Side        : {str(response.get('side', 'N/A')):<30}║",
        f"║  Type        : {str(response.get('type', 'N/A')):<30}║",
        f"║  Status      : {str(response.get('status', 'N/A')):<30}║",
        f"║  Orig Qty    : {str(response.get('origQty', 'N/A')):<30}║",
        f"║  Executed    : {str(response.get('executedQty', 'N/A')):<30}║",
        f"║  Avg Price   : {str(avg_price):<30}║",
        f"║  Limit Price : {str(price_val):<30}║",
        "╚══════════════════════════════════════════════╝",
    ]
    return "\n".join(lines)
