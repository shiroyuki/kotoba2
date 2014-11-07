class MapCollection(dict):
    def get(self, name):
        return self[name]

    def set(self, name, value):
        self[name] = value
