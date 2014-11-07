class Definition(object):
    def __init__(self, single):
        self._single = single

    @property
    def single(self):
        return self._single

d = Definition

HTML = {
    'br': d(single = True),
    'hr': d(single = True),
    'img': d(single = True),
    'meta': d(single = True),
    'link': d(single = True)
}
