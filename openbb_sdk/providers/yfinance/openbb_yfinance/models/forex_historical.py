"""yfinance Forex End of Day fetcher."""
# ruff: noqa: SIM105


from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dateutil.relativedelta import relativedelta
from openbb_provider.abstract.fetcher import Fetcher
from openbb_provider.standard_models.forex_historical import (
    ForexHistoricalData,
    ForexHistoricalQueryParams,
)
from openbb_provider.utils.descriptions import QUERY_DESCRIPTIONS
from openbb_yfinance.utils.helpers import yf_download
from openbb_yfinance.utils.references import INTERVALS, PERIODS
from pandas import to_datetime
from pydantic import Field


class YFinanceForexHistoricalQueryParams(ForexHistoricalQueryParams):
    """YFinance Forex End of Day Query.

    Source: https://finance.yahoo.com/currencies/
    """

    interval: INTERVALS = Field(default="1d", description="Data granularity.")
    period: PERIODS = Field(
        default="max", description=QUERY_DESCRIPTIONS.get("period", "")
    )


class YFinanceForexHistoricalData(ForexHistoricalData):
    """YFinance Forex End of Day Data."""


class YFinanceForexHistoricalFetcher(
    Fetcher[
        YFinanceForexHistoricalQueryParams,
        List[YFinanceForexHistoricalData],
    ]
):
    """Transform the query, extract and transform the data from the yfinance endpoints."""

    @staticmethod
    def transform_query(params: Dict[str, Any]) -> YFinanceForexHistoricalQueryParams:
        """Transform the query."""
        transformed_params = params
        transformed_params["symbol"] = (
            f"{transformed_params['symbol'].upper()}=X"
            if "=X" not in transformed_params["symbol"].upper()
            else transformed_params["symbol"].upper()
        )
        now = datetime.now().date()

        if params.get("start_date") is None:
            transformed_params["start_date"] = now - relativedelta(years=1)
        else:
            try:
                transformed_params["start_date"] = datetime.strptime(
                    params["start_date"], "%Y-%m-%d"
                ).date()
            except TypeError:
                pass

        if params.get("end_date") is None:
            transformed_params["end_date"] = now
        else:
            try:
                transformed_params["end_date"] = datetime.strptime(
                    params["end_date"], "%Y-%m-%d"
                ).date()
            except TypeError:
                pass

        return YFinanceForexHistoricalQueryParams(**transformed_params)

    @staticmethod
    def extract_data(
        query: YFinanceForexHistoricalQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> List[Dict]:
        """Return the raw data from the yfinance endpoint."""
        data = yf_download(
            query.symbol,
            start=query.start_date,
            end=query.end_date,
            interval=query.interval,
            period=query.period,
            auto_adjust=False,
            actions=False,
        )

        # query.end_date = (
        #     datetime.now().date() if query.end_date is None else query.end_date
        # )

        days = (
            1
            if query.interval in ["1m", "2m", "5m", "15m", "30m", "60m", "1h", "90m"]
            else 0
        )

        if query.start_date:
            data.set_index("date", inplace=True)
            data.index = to_datetime(data.index).date
            data = data[
                (data.index >= query.start_date - timedelta(days=days))
                & (data.index <= query.end_date)
            ]

        data.reset_index(inplace=True)
        data.rename(columns={"index": "date"}, inplace=True)

        return data.to_dict("records")

    @staticmethod
    def transform_data(
        data: List[Dict],
    ) -> List[YFinanceForexHistoricalData]:
        """Transform the data to the standard format."""
        return [YFinanceForexHistoricalData.parse_obj(d) for d in data]