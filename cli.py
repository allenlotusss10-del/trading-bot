#!/usr/bin/env python3
"""
cli.py – Command-line interface for the Binance Futures Testnet Trading Bot.

Usage examples:
    # Market BUY
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

    # Limit SELL
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000

    # Stop-Market BUY (bonus order type)
    python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 68000
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from bot import BinanceClient, BinanceClientError, format_order_response, place_order, setup_logger

# ---------------------------------------------------------------------------
# Initialise
# ---------------------------------------------------------------------------

load_dotenv()
logger = setup_logger("cli")

BANNER = r"""
  ____  _                            ____        _
 | __ )(_)_ __   __ _ _ __   ___ __|  _ \  ___ | |_
 |  _ \| | '_ \ / _` | '_ \ / __/ _ \ |_) |/ _ \| __|
 | |_) | | | | | (_| | | | | (_|  __/  _ <| (_) | |_
 |____/|_|_| |_|\__,_|_| |_|\___\___|_| \_\\___/ \__|
  Futures Testnet Trading Bot  |  primetrade.ai task
"""


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

def get_credentials() -> tuple[str, str]:
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        logger.error(
            "API credentials missing. "
            "Set BINANCE_API_KEY and BINANCE_API_SECRET in your .env file."
        )
        print(
            "\n[ERROR] API credentials not found.\n"
            "  1. Copy .env.example to .env\n"
            "  2. Fill in BINANCE_API_KEY and BINANCE_API_SECRET\n"
        )
        sys.exit(1)
    return api_key, api_secret


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Market BUY
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit SELL
  python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000

  # Stop-Market (bonus)
  python cli.py --symbol ETHUSDT --side BUY --type STOP_MARKET --quantity 0.01 --stop-price 3200
        """,
    )

    parser.add_argument(
        "--symbol", "-s",
        required=True,
        metavar="SYMBOL",
        help="Trading pair symbol, e.g. BTCUSDT, ETHUSDT",
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        metavar="SIDE",
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type", "-t",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        metavar="TYPE",
        help="Order type: MARKET | LIMIT | STOP_MARKET",
    )
    parser.add_argument(
        "--quantity", "-q",
        required=True,
        metavar="QTY",
        help="Order quantity (e.g. 0.001 for BTC)",
    )
    parser.add_argument(
        "--price", "-p",
        default=None,
        metavar="PRICE",
        help="Limit price in USDT (required for LIMIT orders)",
    )
    parser.add_argument(
        "--stop-price",
        dest="stop_price",
        default=None,
        metavar="STOP_PRICE",
        help="Trigger price in USDT (required for STOP_MARKET orders)",
    )

    return parser


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_request_summary(args: argparse.Namespace) -> None:
    print("\n┌─────────────────────────────────────────────┐")
    print("│              ORDER REQUEST                  │")
    print("├─────────────────────────────────────────────┤")
    print(f"│  Symbol      : {args.symbol.upper():<29}│")
    print(f"│  Side        : {args.side.upper():<29}│")
    print(f"│  Order Type  : {args.order_type.upper():<29}│")
    print(f"│  Quantity    : {args.quantity:<29}│")
    if args.price:
        print(f"│  Price       : {args.price:<29}│")
    if args.stop_price:
        print(f"│  Stop Price  : {args.stop_price:<29}│")
    print("└─────────────────────────────────────────────┘")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    print(BANNER)
    print_request_summary(args)

    # --- Credentials & client ---
    api_key, api_secret = get_credentials()
    client = BinanceClient(api_key, api_secret)

    # --- Connectivity check ---
    logger.info("Checking connectivity to Binance Futures Testnet …")
    if not client.ping():
        print("\n[ERROR] Cannot reach Binance Futures Testnet. Check your network.\n")
        sys.exit(1)

    # --- Place order ---
    try:
        response = place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
        print(format_order_response(response))
        print("\n✅  Order placed successfully!\n")
        logger.info("Session complete – order placed successfully.")

    except ValueError as exc:
        print(f"\n❌  Validation Error: {exc}\n")
        logger.error(f"Validation error: {exc}")
        sys.exit(1)

    except BinanceClientError as exc:
        print(f"\n❌  Binance API Error [{exc.code}]: {exc.message}\n")
        logger.error(f"API error: {exc}")
        sys.exit(1)

    except (ConnectionError, TimeoutError) as exc:
        print(f"\n❌  Network Error: {exc}\n")
        logger.error(f"Network error: {exc}")
        sys.exit(1)

    except Exception as exc:
        print(f"\n❌  Unexpected error: {exc}\n")
        logger.exception("Unexpected error occurred.")
        sys.exit(1)


if __name__ == "__main__":
    main()
