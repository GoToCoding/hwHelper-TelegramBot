import os
import pickle
from functools import wraps

users = {}
groups = []


def upload_data():
    if os.path.isfile('users.pickle'):
        with open('users.pickle', 'rb') as f:
            users = pickle.load(f)
        print('used users.pickle backup')
    else:
        print('no users.pickle backup')

    if os.path.isfile('groups.pickle'):
        with open('groups.pickle', 'rb') as f:
            groups = pickle.load(f)
        print('used groups.pickle backup')
    else:
        print('no groups.pickle backup')


def save_data():
    with open('users.pickle', 'wb') as f:
        pickle.dump(users, f)
    with open('groups.pickle', 'wb') as f:
        pickle.dump(groups, f)


def save_data_decorator(function_to_decorate):
    @wraps(function_to_decorate)
    def wrapper(*args, **kwargs):
        save_data()
        function_to_decorate(*args, **kwargs)
        save_data()

    return wrapper
