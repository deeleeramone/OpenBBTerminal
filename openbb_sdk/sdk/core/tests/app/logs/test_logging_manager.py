import json
from typing import Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from openbb_core.app.logs.logging_manager import LoggingManager
from pydantic import BaseModel


class MockLoggingSettings:
    def __init__(self, system_settings, user_settings):
        self.system_settings = system_settings
        self.user_settings = user_settings


class MockCommandOutput(BaseModel):
    output: Optional[str]
    error: Optional[str]


@pytest.fixture(scope="function")
def logging_manager():
    mock_system_settings = Mock()
    mock_system_settings = "mock_system_settings"
    mock_user_settings = Mock()
    mock_user_settings = "mock_user_settings"
    mock_setup_handlers = Mock()
    mock_log_startup = Mock()

    with patch(
        "openbb_core.app.logs.logging_manager.LoggingSettings",
        MockLoggingSettings,
    ), patch(
        "openbb_core.app.logs.logging_manager.LoggingManager._setup_handlers",
        mock_setup_handlers,
    ), patch(
        "openbb_core.app.logs.logging_manager.LoggingManager._log_startup",
        mock_log_startup,
    ):
        logging_manager = LoggingManager(
            system_settings=mock_system_settings,
            user_settings=mock_user_settings,
        )

        assert mock_setup_handlers.assert_called_once
        assert mock_log_startup.assert_called_once

        return logging_manager


def test_correctly_initialized(logging_manager):
    assert logging_manager


def test_logging_settings_property(logging_manager):
    assert logging_manager.logging_settings.system_settings == "mock_system_settings"
    assert logging_manager.logging_settings.user_settings == "mock_user_settings"


def test_logging_settings_setter(logging_manager):
    custom_user_settings = "custom_user_settings"
    custom_system_settings = "custom_system_settings"

    with patch(
        "openbb_core.app.logs.logging_manager.LoggingSettings",
        MockLoggingSettings,
    ):
        logging_manager.logging_settings = (
            custom_system_settings,
            custom_user_settings,
        )

    assert logging_manager.logging_settings.system_settings == "custom_system_settings"
    assert logging_manager.logging_settings.user_settings == "custom_user_settings"


def test_log_startup(logging_manager):
    with patch("logging.getLogger") as mock_get_logger:
        mock_info = mock_get_logger.return_value.info

        class MockCredentials(BaseModel):
            username: str
            password: str

        logging_manager._user_settings = MagicMock(
            preferences="your_preferences",
            credentials=MockCredentials(username="username", password="password"),
        )
        logging_manager._system_settings = "your_system_settings"

        logging_manager._log_startup()

        expected_log_data = {
            "PREFERENCES": "your_preferences",
            "KEYS": {"username": "defined", "password": "defined"},
            "SYSTEM": "your_system_settings",
        }
        mock_info.assert_called_once_with(
            "STARTUP: %s ",
            json.dumps(expected_log_data),
        )
        mock_get_logger.assert_called_once


@pytest.mark.parametrize(
    "user_settings, system_settings, command_output, route, func, kwargs",
    [
        (
            "mock_settings",
            "mock_system",
            MockCommandOutput(output="mock_output"),
            "mock_route",
            "mock_func",
            {},
        ),
        (
            "mock_settings",
            "mock_system",
            MockCommandOutput(error="mock_error"),
            "mock_route",
            "mock_func",
            {},
        ),
        (
            "mock_settings",
            "mock_system",
            MockCommandOutput(error="mock_error"),
            "login",
            "mock_func",
            {},
        ),
    ],
)
def test_log(
    logging_manager, user_settings, system_settings, command_output, route, func, kwargs
):
    with patch(
        "openbb_core.app.logs.logging_manager.LoggingSettings",
        MockLoggingSettings,
    ), patch("logging.getLogger") as mock_get_logger:
        if route == "login":
            with patch(
                "openbb_core.app.logs.logging_manager.LoggingManager._log_startup"
            ) as mock_log_startup:
                logging_manager.log(
                    user_settings=user_settings,
                    system_settings=system_settings,
                    command_output=command_output,
                    route=route,
                    func=func,
                    kwargs=kwargs,
                )
                assert mock_log_startup.assert_called_once

        else:
            mock_info = mock_get_logger.return_value.info
            mock_error = mock_get_logger.return_value.error

            mock_callable = Mock()
            mock_callable.__name__ = func

            logging_manager.log(
                user_settings=user_settings,
                system_settings=system_settings,
                command_output=command_output,
                route=route,
                func=mock_callable,
                kwargs=kwargs,
            )

            expected_log_data = {
                "route": route,
                "input": kwargs,
                "error": command_output.error,
            }

            if command_output.error:
                mock_error.assert_called_once_with(
                    "ERROR: %s",
                    json.dumps(expected_log_data),
                    extra={"func_name_override": func},
                )
            else:
                mock_info.assert_called_once_with(
                    "CMD: %s",
                    json.dumps(expected_log_data),
                    extra={"func_name_override": func},
                )