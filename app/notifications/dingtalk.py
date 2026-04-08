class DingTalkNotifier:
    def send(self, message: str) -> dict[str, str]:
        return {"channel": "dingtalk", "message": message, "status": "mocked"}

