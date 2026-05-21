import hashlib
import hmac
import time
from typing import Any, Dict

import requests

from .logging_config import setup_logger

logger = setup_logger("client")

BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class BinanceClient:
    """
    Thin wrapper around the Binance Futures Testnet REST API.
    Handles authentication (HMAC-SHA256 signing) and HTTP session management.
    """

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret.encode("utf-8")
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: Dict[str, Any]) -> str:
        """Return HMAC-SHA256 hex signature of the query string."""
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return hmac.new(self.api_secret, query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse JSON and raise BinanceClientError on API-level errors."""
        logger.debug(f"HTTP {response.status_code} ← {response.url}")
        logger.debug(f"Response body: {response.text}")
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            raise BinanceClientError(code=data["code"], message=data.get("msg", "Unknown error"))

        response.raise_for_status()
        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """Test connectivity to the Binance Futures Testnet."""
        try:
            resp = self.session.get(f"{BASE_URL}/fapi/v1/ping", timeout=10)
            resp.raise_for_status()
            logger.info("Connectivity check passed ✓")
            return True
        except requests.RequestException as exc:
            logger.error(f"Connectivity check failed: {exc}")
            return False

    def place_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign and submit a new order to /fapi/v1/order or /fapi/v1/algoOrder.
        Returns the parsed JSON response dict.
        """
        endpoint = "/fapi/v1/order"
        conditional_types = ["STOP_MARKET", "TAKE_PROFIT_MARKET", "STOP", "TAKE_PROFIT", "TRAILING_STOP_MARKET"]
        
        if params.get("type") in conditional_types:
            endpoint = "/fapi/v1/algoOrder"
            params["algoType"] = "CONDITIONAL"

        params["timestamp"] = self._timestamp()
        params["signature"] = self._sign(params)

        logger.debug(f"POST {endpoint} → params: { {k: v for k, v in params.items() if k != 'signature'} }")

        try:
            resp = self.session.post(
                f"{BASE_URL}{endpoint}",
                params=params,
                timeout=15,
            )
            return self._handle_response(resp)

        except BinanceClientError:
            raise
        except requests.exceptions.ConnectionError as exc:
            logger.error(f"Network connection error: {exc}")
            raise ConnectionError(f"Could not reach Binance Futures Testnet: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            logger.error(f"Request timed out: {exc}")
            raise TimeoutError("Request to Binance Futures Testnet timed out.") from exc
        except requests.exceptions.HTTPError as exc:
            logger.error(f"HTTP error: {exc}")
            raise
