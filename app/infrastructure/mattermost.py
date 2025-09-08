from __future__ import annotations

from app.interfaces.gateways import MattermostGateway
from app.loader import mm_driver


class MattermostClient(MattermostGateway):
    def send_dm(self, user_id: str, message: str) -> None:
        me = mm_driver.users.get_user("me")
        bot_user_id = me["id"]
        dm_channel = mm_driver.channels.create_direct_message_channel(
            [bot_user_id, user_id]
        )
        mm_driver.posts.create_post(
            options={"channel_id": dm_channel["id"], "message": message}
        )

    def get_user_by_email(self, email: str) -> dict:
        return mm_driver.users.get_user_by_email(email)
