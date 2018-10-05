class Group:
    def __init__(self, id: int, creator_id: int, name: str):
        self.id = id
        self.creator_id = creator_id
        self.name = name
        self.files = {}

    def insert(self, uid, file_id):
        self.files[uid] = file_id
