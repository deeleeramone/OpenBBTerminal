# IMPORTATION STANDARD
import pandas as pd

# IMPORTATION THIRDPARTY
import pytest

# IMPORTATION INTERNAL
from openbb_terminal.stocks.options import yfinance_model


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [("User-Agent", None)],
        "filter_query_parameters": [
            ("period1", "MOCK_PERIOD_1"),
            ("period2", "MOCK_PERIOD_2"),
            ("date", "MOCK_DATE"),
        ],
    }


@pytest.mark.vcr(record_mode="none")
@pytest.mark.record_stdout
def test_option_expirations_no_dates(mocker):
    # MOCK TICKER
    mocker.patch(
        target="openbb_terminal.stocks.options.yfinance_model.yf.Ticker",
    )

    # MOCK OPTION
    mocker.patch(
        target="openbb_terminal.stocks.options.yfinance_model.yf.Ticker.option",
        return_value=(),
    )

    yfinance_model.option_expirations(symbol="PM")


@pytest.mark.vcr
def test_get_option_chain(mocker, recorder):
    # FORCE SINGLE THREADING
    yf_download = yfinance_model.yf.download

    def mock_yf_download(*args, **kwargs):
        kwargs["threads"] = False
        return yf_download(*args, **kwargs)

    mocker.patch("yfinance.download", side_effect=mock_yf_download)

    result_tuple = yfinance_model.get_option_chain(symbol="AAPL", expiry="2023-07-21")
    result_tuple = (result_tuple.calls, result_tuple.puts)

    recorder.capture_list(result_tuple)


@pytest.mark.vcr
@pytest.mark.parametrize(
    "func",
    [
        "option_expirations",
        "get_dividend",
        "get_price",
        "get_closing",
        "get_iv_surface",
    ],
)
def test_call_func(func, mocker, recorder):
    # FORCE SINGLE THREADING
    yf_download = yfinance_model.yf.download

    def mock_yf_download(*args, **kwargs):
        kwargs["threads"] = False
        return yf_download(*args, **kwargs)

    mocker.patch("yfinance.download", side_effect=mock_yf_download)

    # MOCK OPTION
    mocker.patch(
        target="openbb_terminal.stocks.options.yfinance_model.get_dte",
        return_value=1,
    )

    result = getattr(yfinance_model, func)(symbol="PM")

    recorder.capture(result)


@pytest.mark.vcr
def test_load_options(recorder):
    data = yfinance_model.load_options(symbol="OXY")
    assert isinstance(data.chains, pd.DataFrame)
    assert isinstance(data.last_price, float)
    assert isinstance(data.underlying_price, pd.Series)
    assert data.hasIV
    df1 = data.chains
    data = yfinance_model.load_options(symbol="OXY", pydantic=True)
    assert isinstance(data.chains, dict)
    assert isinstance(data.underlying_price, dict)
    assert data.hasIV
    assert isinstance(data.expirations, list)
    assert isinstance(data.strikes, list)
    df2 = pd.DataFrame(data.chains)
    assert df1.equals(df2)
    recorder.capture(data.chains)
    recorder.capture(data.underlying_price)
    recorder.capture(data.last_price)
