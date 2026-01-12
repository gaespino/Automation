

class CallForwarder(object):
    def __init__(self, inner):
        self.adapted_object = inner

    def __getattr__(self, item):
        return getattr(self.adapted_object, item)
