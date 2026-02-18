"""Order Execution Engine: 분할매수, 재시도, 슬리피지 보호"""

import logging

logger = logging.getLogger("stockagent.core.order_executor")


class OrderExecutor:
    """고도화된 주문 실행기"""

    def __init__(
        self,
        order_client,
        split_size: int = 20,
        max_retries: int = 3,
        max_slippage_pct: float = 0.005,
    ):
        self._order = order_client
        self.split_size = split_size
        self.max_retries = max_retries
        self.max_slippage_pct = max_slippage_pct

    async def execute_split_buy(self, stock_code: str, qty: int, price: int) -> list[dict]:
        """분할 매수: qty를 split_size 단위로 나누어 주문"""
        results = []
        remaining = qty
        while remaining > 0:
            batch = min(self.split_size, remaining)
            result = await self._order.buy(stock_code, qty=batch, price=price)
            results.append(result)
            remaining -= batch
        return results

    async def execute_buy(
        self, stock_code: str, qty: int, price: int, market_price: int | None = None
    ) -> dict:
        """매수 주문 (슬리피지 체크 + 재시도)"""
        if market_price is not None:
            slippage = abs(market_price - price) / price
            if slippage > self.max_slippage_pct:
                logger.warning(
                    "슬리피지 초과: price=%d, market=%d, slippage=%.4f",
                    price, market_price, slippage,
                )
                return {"status": "cancelled_slippage", "slippage": slippage}

        last_result = {"status": "failed", "message": "max retries exhausted"}
        for attempt in range(self.max_retries):
            result = await self._order.buy(stock_code, qty=qty, price=price)
            if result.get("status") != "failed":
                return result
            logger.warning("주문 실패 (시도 %d/%d): %s", attempt + 1, self.max_retries, result.get("message"))
            last_result = result
        return last_result

    async def execute_sell(
        self, stock_code: str, qty: int, price: int, market_price: int | None = None
    ) -> dict:
        """매도 주문 (슬리피지 체크 + 재시도)"""
        if market_price is not None:
            slippage = abs(market_price - price) / price
            if slippage > self.max_slippage_pct:
                return {"status": "cancelled_slippage", "slippage": slippage}

        last_result = {"status": "failed", "message": "max retries exhausted"}
        for attempt in range(self.max_retries):
            result = await self._order.sell(stock_code, qty=qty, price=price)
            if result.get("status") != "failed":
                return result
            last_result = result
        return last_result
