"""CBOE Stock Info fetcher."""


from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from openbb_provider.abstract.fetcher import Fetcher
from openbb_provider.standard_models.stock_info import (
    StockInfoData,
    StockInfoQueryParams,
)
from pydantic import Field

from openbb_cboe.utils.helpers import (
    get_cboe_directory,
    get_cboe_index_directory,
    get_ticker_info,
    get_ticker_iv,
)


class CboeStockInfoQueryParams(StockInfoQueryParams):
    """CBOE Company Search query.

    Source: https://www.cboe.com/
    """


class CboeStockInfoData(StockInfoData):
    """CBOE Company Search Data."""

    type: Optional[str] = Field(description="Type of asset.")
    exchange_id: Optional[int] = Field(description="The Exchange ID number.")
    tick: Optional[str] = Field(
        description="Whether the last sale was an up or down tick."
    )
    bid: Optional[float] = Field(description="Current bid price.")
    bid_size: Optional[float] = Field(description="Bid lot size.")
    ask: Optional[float] = Field(description="Current ask price.")
    ask_size: Optional[float] = Field(description="Ask lot size.")
    volume: Optional[float] = Field(
        description="Stock volume for the current trading day."
    )
    iv30: Optional[float] = Field(
        description="The 30-day implied volatility of the stock."
    )
    iv30_change: Optional[float] = Field(
        description="Change in 30-day implied volatility of the stock."
    )
    last_trade_timestamp: Optional[datetime] = Field(
        description="Last trade timestamp for the stock."
    )
    iv30_annual_high: Optional[float] = Field(
        description="The 1-year high of implied volatility."
    )
    hv30_annual_high: Optional[float] = Field(
        description="The 1-year high of realized volatility."
    )
    iv30_annual_low: Optional[float] = Field(
        description="The 1-year low of implied volatility."
    )
    hv30_annual_low: Optional[float] = Field(
        description="The 1-year low of realized volatility."
    )
    iv60_annual_high: Optional[float] = Field(
        description="The 60-day high of implied volatility."
    )
    hv60_annual_high: Optional[float] = Field(
        description="The 60-day high of realized volatility."
    )
    iv60_annual_low: Optional[float] = Field(
        description="The 60-day low of implied volatility."
    )
    hv60_annual_low: Optional[float] = Field(
        description="The 60-day low of realized volatility."
    )
    iv90_annual_high: Optional[float] = Field(
        description="The 90-day high of implied volatility."
    )
    hv90_annual_high: Optional[float] = Field(
        description="The 90-day high of realized volatility."
    )


class CboeStockInfoFetcher(
    Fetcher[
        CboeStockInfoQueryParams,
        List[CboeStockInfoData],
    ]
):
    """Transform the query, extract and transform the data from the CBOE endpoints."""

    @staticmethod
    def transform_query(params: Dict[str, Any]) -> CboeStockInfoQueryParams:
        """Transform the query"""
        return CboeStockInfoQueryParams(**params)

    @staticmethod
    def extract_data(
        query: CboeStockInfoQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> dict:
        """Return the raw data from the CBOE endpoint"""

        query.symbol = query.symbol.upper()
        INDEXES = get_cboe_index_directory().index.to_list()
        SYMBOLS = get_cboe_directory()

        if query.symbol not in SYMBOLS.index and query.symbol not in INDEXES:
            raise RuntimeError(
                f"The symbol, {query.symbol}, was not found in the CBOE directory."
            )

        _info = pd.Series(get_ticker_info(query.symbol))
        _iv = pd.Series(get_ticker_iv(query.symbol))
        data = (
            pd.DataFrame(pd.concat([_info, _iv]))
            .transpose()
            .drop(columns="seqno")
            .iloc[0]
        )

        return data.to_dict()

    @staticmethod
    def transform_data(data: dict) -> List[CboeStockInfoData]:
        """Transform the data to the standard format"""
        return [CboeStockInfoData.parse_obj(data)]