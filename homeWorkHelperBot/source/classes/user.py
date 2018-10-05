class User:
    def __init__(self, username, uid):
        self.username = username
        self.uid = uid
        self.groups = []
        self.last_markup = None
        self.selected_group = None
        self.status = ""
        self.created_groups = []