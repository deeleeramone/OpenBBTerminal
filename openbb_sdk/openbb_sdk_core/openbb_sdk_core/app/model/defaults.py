from typing import Dict

from pydantic import BaseModel


class Defaults(BaseModel):
    """Defaults."""

    # TODO: Understand if this is good to sync with the hub
    endpoints: Dict[str, Dict[str, str]] = {
        "/stocks/load": {"provider": "polygon"},
        "/stocks/news": {"provider": "fmp"},
    }

    def __repr__(self) -> str:
        return (
            self.__class__.__name__
            + "\n\n"
            + "\n".join([f"{k}: {v}" for k, v in self.dict().items()])
        )
