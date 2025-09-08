from __future__ import annotations

from app.interfaces.gateways import MattermostGateway
from app.loader import mm_driver


class MattermostClient(MattermostGateway):
    def send_dm(self, user_id: str, message: str) -> tuple[str, str]:
        me = mm_driver.users.get_user("me")
        bot_user_id = me["id"]
        dm_channel = mm_driver.channels.create_direct_message_channel(
            [bot_user_id, user_id]
        )
        post = mm_driver.posts.create_post(
            options={"channel_id": dm_channel["id"], "message": message}
        )
        return post["id"], dm_channel["id"]

    def get_user_by_email(self, email: str) -> dict:
        return mm_driver.users.get_user_by_email(email)

    def reply_in_thread(self, root_post_id: str, channel_id: str, message: str) -> str:
        root_post = mm_driver.posts.get_post(root_post_id)
        channel_id = root_post.get("channel_id") or channel_id
        post = mm_driver.posts.create_post(
            options={
                "channel_id": channel_id,
                "root_id": root_post_id,
                "message": message,
            }
        )
        return post["id"]
