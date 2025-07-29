class HandlerList(list):
    PRIORITY_KEY = "_priority"
    DEFAULT_PRIORITY = 50

    def append(self, __object):
        _, callback = __object
        priority = getattr(callback, self.PRIORITY_KEY, self.DEFAULT_PRIORITY)
        index = 0
        for i, _object in enumerate(self):
            _, _callback = _object
            _priority = getattr(_callback, self.PRIORITY_KEY, self.DEFAULT_PRIORITY)
            if priority < _priority:
                index = i
                break
            index = i + 1
        super().insert(index, __object)
