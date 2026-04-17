import os
import logging
import urllib.request
import urllib.error
import json


def send_slack(message: str, config: dict, logger: logging.Logger) -> None:
    """SlackのIncoming WebhookにメッセージをPOSTする"""
    slack_cfg = config.get("slack", {})

    # Slack通知が無効な場合はスキップ
    if not slack_cfg.get("enabled", False):
        return

    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL が設定されていないため通知をスキップします")
        return

    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            if res.status == 200:
                logger.debug("Slack通知を送信しました")
            else:
                logger.warning(f"Slack通知に失敗しました: HTTP {res.status}")
    except urllib.error.URLError as e:
        logger.warning(f"Slack通知に失敗しました: {e}")
