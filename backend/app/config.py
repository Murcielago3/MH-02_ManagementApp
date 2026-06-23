from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str

    # ─── Slack notifications ───
    # Bot User OAuth token (xoxb-…) from your Slack app. Leave unset to disable
    # all Slack notifications — they no-op with a logged warning, so the app and
    # tasks keep working without Slack configured.
    SLACK_BOT_TOKEN: Optional[str] = None
    # Channel IDs (e.g. "C0123ABCDE") the bot has been invited to.
    SLACK_CHANNEL_MANAGEMENT: Optional[str] = None   # admin + accounts: monthly report, reimbursements
    SLACK_CHANNEL_COMMON: Optional[str] = None        # everyone: timesheet nudges + uploads
    # Optional text prepended to each message so Slack reliably emails people,
    # e.g. "<@U123ABCDE>" to ping a person or "<!channel>" for the whole channel.
    SLACK_MENTION_MANAGEMENT: Optional[str] = None
    SLACK_MENTION_COMMON: Optional[str] = None

    # Timezone for scheduled reminders (Celery Beat). Studio is India-based.
    TIMEZONE: str = "Asia/Kolkata"

    class Config:
        env_file = ".env"

settings = Settings()
