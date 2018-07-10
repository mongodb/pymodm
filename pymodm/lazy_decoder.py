class LazyDecoder(object):
    def __init__(self):
        self._mongo_data = {}
        self._python_data = {}
        self._members = set()

    def __contains__(self, item):
        return item in self._members

    def __iter__(self):
        return iter(self._members)

    def __eq__(self, other):
        return (self._mongo_data == other._mongo_data and
                self._python_data == other._python_data)

    def clear(self):
        self._mongo_data.clear()
        self._python_data.clear()
        self._members.clear()

    def get_mongo_value(self, key, to_mongo):
        try:
            return self._mongo_data[key]
        except KeyError:
            pvalue = self._python_data.get(key)
        if pvalue is None:
            raise KeyError
        return to_mongo(pvalue)

    def set_mongo_value(self, key, value):
        self._python_data.pop(key, None)
        self._mongo_data[key] = value
        self._members.add(key)

    def get_python_value(self, key, to_python):
        try:
            return self._python_data[key]
        except KeyError:
            mvalue = self._mongo_data.pop(key, None)
        if mvalue is None:
            raise KeyError
        pvalue = to_python(mvalue)
        self._python_data[key] = pvalue
        return pvalue

    def set_python_value(self, key, value):
        self._mongo_data.pop(key, None)
        self._python_data[key] = value
        self._members.add(key)