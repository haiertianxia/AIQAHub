class WeComNotifier:
    def send(self, message: str) -> dict[str, str]:
        return {"channel": "wecom", "message": message, "status": "mocked"}

