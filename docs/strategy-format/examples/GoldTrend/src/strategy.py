class Strategy:
    def __init__(self, context, params):
        self.context = context
        self.params = params

    def initialize(self):
        pass

    def on_bar(self, bar):
        pass

    def on_finish(self, summary):
        pass
