from mattermostdriver import Driver  # noqa

from app.core import settings

mm_driver = Driver(
    {
        "url": settings.mattermost_domain,
        "token": settings.mattermost_token,
        "scheme": "https",
        "port": 443,
        "verify": True,
        "keepalive": True,
        "keepalive_delay": 30,
    }
)


def init_mm_driver():
    mm_driver.login()
