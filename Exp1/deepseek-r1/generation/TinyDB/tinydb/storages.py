import json
import os

class JSONStorage:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def read(self):
        try:
            with open(self.path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def write(self, data):
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)

    def close(self):
        pass