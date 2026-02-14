class IntegrationNotConfigured(Exception):
    def __init__(self, key: str):
        super().__init__(f"Missing {key}")
        self.key = key
