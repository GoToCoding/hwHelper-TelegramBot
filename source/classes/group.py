import uuid
from data import groups
from classes.user import get_user


class Group:
    def __init__(self, id: int, creator_id: int, name: str, invite_key: str):
        self.id = id
        self.creator_id = creator_id
        self.name = name
        self.invite_key = invite_key
        self.files = {}

    def insert(self, uid, file_id):
        self.files[uid] = file_id


def get_group(group_id):
    return groups[group_id]


def get_group_by_invite_key(invite_key):
    for group in groups:
        if group.invite_key == invite_key:
            return group
    return None


def create_group(creator_uid, name):
    group_id = len(groups)
    groups.append(Group(group_id, creator_uid, name, str(uuid.uuid4())))
    get_user(creator_uid).created_groups.append(group_id)
    return group_id
