class EmailNotifier:
    def send(self, message: str) -> dict[str, str]:
        return {"channel": "email", "message": message, "status": "mocked"}

