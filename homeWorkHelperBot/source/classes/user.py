class User:
    def __init__(self, username: str, uid: int):
        self.username = username.lower()
        self.uid = uid
        self.groups = []
        self.last_markup = None
        self.selected_group = None
        self.status = ''
        self.created_groups = []
