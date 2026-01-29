import json
import os

class JSONStorage:
    def __init__(self, path):
        self._path = path
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump({}, f)

    def read(self):
        with open(self._path, 'r') as f:
            return json.load(f)

    def write(self, data):
        with open(self._path, 'w') as f:
            json.dump(data, f, indent=4)

    def update_table(self, table_name, records):
        data = self.read()
        data[table_name] = records
        self.write(data)

    def close(self):
        pass