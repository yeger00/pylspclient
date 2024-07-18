import json


class config:
    data = {}

    def __init__(self) -> None:
        try:
            with open("config.json", "r") as fp:
                self.data = json.load(fp)
        except:
            pass
        pass

    def set(self, key, value):
        self.data[key] = value
        with open("config.json", "w") as fp:
            json.dump(self.data, fp=fp)

    def get(self, key,default):
        try:
            return self.data[key]
        except:
            return  default

    @staticmethod
    def load():
        return config()
