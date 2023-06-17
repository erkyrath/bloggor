
class Page:
    def __init__(self, ctx):
        self.ctx = ctx

class EntryPage(Page):
    def __init__(self, ctx, dirpath, filename):
        Page.__init__(self, ctx)

