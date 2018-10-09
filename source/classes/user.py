from data import users, groups


class User:
    def __init__(self, username: str, uid: int):
        self.username = username.lower()
        self.uid = uid
        self.groups = []
        self.last_markup = None
        self.selected_group = None
        self.status = ''
        self.created_groups = []

    def add_group_by_group_id(self, group_id):
        self.groups.append(group_id)

    def add_group_by_invite_key(self, invite_key):
        """
        return None if there is no group with this invite key
        :param invite_key:
        :return: Group or None
        """
        for group in groups:
            if group.invite_key == invite_key:
                self.groups.append(group.id)
                return group
        return None


def get_user(uid):
    if uid in users:
        return users[uid]
    return None


def add_user(username, uid):
    users[uid] = User(username, uid)
    return users[uid]
