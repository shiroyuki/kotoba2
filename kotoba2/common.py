class MapCollection(object):
    def __init__(self, initial_data = None):
        self._data = initial_data or {}

    def get(self, name):
        return self._data[name]

    def set(self, name, value):
        self._data[name] = value
    
    def __len__(self):
        return len(self._data)
    
    def __iter__(self):
        for name in self._data:
            yield self._data[name]
    
    def __dict__(self):
        return self._data