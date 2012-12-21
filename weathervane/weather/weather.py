class Weather(object):
    def __init__(self, data):
        self.data = data

    def get(self, keyword):
        return self.data.get(keyword)
