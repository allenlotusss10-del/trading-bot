from typing import Optional

from .logging_config import setup_logger

logger = setup_logger("validators")

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


# ---------------------------------------------------------------------------
# Individual field validators
# ---------------------------------------------------------------------------

def validate_symbol(symbol: str) -> str:
    """Normalise and validate a trading pair symbol."""
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty.")
    symbol = symbol.strip().upper()
    if len(symbol) < 3:
        raise ValueError(f"Symbol '{symbol}' is too short to be a valid trading pair.")
    if not symbol.endswith("USDT"):
        logger.warning(
            f"Symbol '{symbol}' does not end with 'USDT'. "
            "Only USDT-margined perpetuals are supported on this testnet endpoint."
        )
    logger.debug(f"Symbol validated: {symbol}")
    return symbol


def validate_side(side: str) -> str:
    """Validate order side (BUY or SELL)."""
    if not side:
        raise ValueError("Side cannot be empty.")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Allowed values: {', '.join(sorted(VALID_SIDES))}."
        )
    logger.debug(f"Side validated: {side}")
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type."""
    if not order_type:
        raise ValueError("Order type cannot be empty.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Allowed values: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    logger.debug(f"Order type validated: {order_type}")
    return order_type


def validate_quantity(quantity: str) -> float:
    """Validate and parse order quantity."""
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than 0 (got {qty}).")
    logger.debug(f"Quantity validated: {qty}")
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate limit price.
    - Required for LIMIT orders.
    - Ignored (returns None) for MARKET orders.
    """
    if order_type == "MARKET":
        if price is not None:
            logger.warning("Price argument is ignored for MARKET orders.")
        return None

    if order_type == "LIMIT":
        if price is None or str(price).strip() == "":
            raise ValueError("Price is required for LIMIT orders. Use --price <value>.")
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValueError(f"Price '{price}' is not a valid number.")
        if p <= 0:
            raise ValueError(f"Price must be greater than 0 (got {p}).")
        logger.debug(f"Limit price validated: {p}")
        return p

    return None  # other types handled by stop_price validator


def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate stop price.
    - Required for STOP_MARKET orders.
    - Ignored for all other order types.
    """
    if order_type != "STOP_MARKET":
        if stop_price is not None:
            logger.warning(f"--stop-price is ignored for {order_type} orders.")
        return None

    if stop_price is None or str(stop_price).strip() == "":
        raise ValueError(
            "Stop price is required for STOP_MARKET orders. Use --stop-price <value>."
        )
    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(f"Stop price '{stop_price}' is not a valid number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be greater than 0 (got {sp}).")
    logger.debug(f"Stop price validated: {sp}")
    return sp
