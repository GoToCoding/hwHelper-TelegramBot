class User:
    def __init__(self, name, uid):
        self.name = name
        self.uid = uid
        self.groups = []
        self.last_markup = None
        self.selected_group = None
