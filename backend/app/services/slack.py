"""Slack notifications for MH-02.

Every Slack message in the app flows through this module. Event notifications
(reimbursement submitted, timesheet uploaded) are dispatched from FastAPI routes
via ``BackgroundTasks``; scheduled reminders (monthly report, weekly timesheet
nudge) are sent from Celery tasks. Both call the same synchronous sender:

  * FastAPI runs sync ``BackgroundTasks`` in a threadpool, so the event loop is
    never blocked.
  * Celery workers are already synchronous, so they call it directly.

Posting uses Slack's Web API ``chat.postMessage`` with a bot token — free on
Slack's plan. Failures never raise: a Slack outage must not break a user action
or a scheduled task.

Adding a new reminder type? Add one line to ``EVENT_CHANNELS`` below.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SLACK_POST_URL = "https://slack.com/api/chat.postMessage"
SLACK_LOOKUP_URL = "https://slack.com/api/users.lookupByEmail"

# Logical event key -> channel group. The single place routing lives.
EVENT_CHANNELS = {
    "monthly_report": "management",         # 1st-of-month admin summary
    "reimbursement": "management",          # employee submitted a reimbursement
    "reimbursement_decision": "management", # admin approved/rejected a reimbursement
    "timesheet_reminder": "common",         # Sunday-noon nudge to submit timesheets
    "timesheet_uploaded": "common",         # employee submitted a weekly timesheet
    "timesheet_decision": "common",         # admin approved/rejected a timesheet
    "daily_task_reminder": "common",        # daily morning nudge: today's assigned tasks
}

# Events that ping the channel's mention target (so people get a Slack email).
# Everything else posts silently. `timesheet_reminder` is intentionally absent:
# it tags the specific people who are behind (individual <@ID> mentions already
# notify + email them), so a blanket @channel would be redundant noise.
MENTION_EVENTS = {"monthly_report", "reimbursement"}


def _resolve(channel_group: str):
    """Return (channel_id, mention_prefix) for a channel group."""
    if channel_group == "management":
        return settings.SLACK_CHANNEL_MANAGEMENT, settings.SLACK_MENTION_MANAGEMENT
    return settings.SLACK_CHANNEL_COMMON, settings.SLACK_MENTION_COMMON


def send_slack_message(text: str, *, channel: str | None, blocks: list | None = None) -> bool:
    """Post a message to Slack. Returns True on success, False otherwise.

    No-ops (returns False) if the bot token or channel is missing, so the app
    runs fine without Slack configured.
    """
    if not settings.SLACK_BOT_TOKEN:
        logger.warning("SLACK_BOT_TOKEN not set — skipping Slack message.")
        return False
    if not channel:
        logger.warning("No Slack channel configured for this message — skipping.")
        return False

    payload: dict = {"channel": channel, "text": text}
    if blocks:
        payload["blocks"] = blocks

    try:
        resp = httpx.post(
            SLACK_POST_URL,
            headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
            json=payload,
            timeout=10.0,
        )
        data = resp.json()
        if not data.get("ok"):
            # Common errors: channel_not_found, not_in_channel, invalid_auth.
            logger.error("Slack API error: %s", data.get("error"))
            return False
        return True
    except Exception:
        logger.exception("Failed to post message to Slack.")
        return False


def lookup_user_id(email: str | None) -> str | None:
    """Resolve a Slack user ID from an email, or None.

    Needs the bot scope ``users:read.email``. Returns None (logged) if the scope
    is missing or no Slack user has that email, so callers can fall back to a
    plain name.
    """
    if not settings.SLACK_BOT_TOKEN or not email:
        return None
    try:
        resp = httpx.get(
            SLACK_LOOKUP_URL,
            headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
            params={"email": email},
            timeout=10.0,
        )
        data = resp.json()
        if data.get("ok"):
            return data["user"]["id"]
        # e.g. missing_scope, users_not_found
        logger.warning("Slack user lookup for %s failed: %s", email, data.get("error"))
        return None
    except Exception:
        logger.exception("Slack user lookup failed for %s.", email)
        return None


def notify_event(event_key: str, text: str, blocks: list | None = None) -> bool:
    """Route a message to the right channel for ``event_key`` and send it.

    Prepends the channel's optional mention prefix (e.g. ``<@U123>`` or
    ``<!channel>``) so Slack reliably emails the right people.
    """
    group = EVENT_CHANNELS.get(event_key)
    if group is None:
        logger.error("Unknown Slack event key: %s", event_key)
        return False

    channel, mention = _resolve(group)
    if mention and event_key in MENTION_EVENTS:
        text = f"{mention} {text}"
        if blocks:
            # Keep the mention visible (and notifying) even when blocks render.
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": mention}}] + blocks

    return send_slack_message(text, channel=channel, blocks=blocks)
