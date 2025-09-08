from __future__ import annotations

from typing import Protocol


class MattermostGateway(Protocol):
    def send_dm(self, user_id: str, message: str) -> None: ...

    def get_user_by_email(self, email: str) -> dict: ...
