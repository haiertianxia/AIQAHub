from app.notifications.dingtalk import DingTalkNotifier


class Notifier:
    def __init__(self) -> None:
        self.dingtalk = DingTalkNotifier()

    def notify(self, message: str) -> dict[str, str]:
        return self.dingtalk.send(message)

