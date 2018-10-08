import os
import pickle
import random
import shutil
import uuid
import zipfile
from functools import wraps

import secret_settings
import telebot
from telebot import types
from classes.user import User
from classes.group import Group
from classes import action

bot = telebot.TeleBot(secret_settings.TOKEN)

users = {}
groups = []

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


back_to_menu = types.InlineKeyboardMarkup()
back_to_menu.add(types.InlineKeyboardButton("Return to menu", callback_data=action.return_to_menu))


def generate_menu_markup(user: User):
    markup = types.InlineKeyboardMarkup()
    markup.row_width = len(user.groups) + len(user.created_groups) + 1
    markup.add(types.InlineKeyboardButton("Join to new group", callback_data=action.join_group),
               types.InlineKeyboardButton("Create a group", callback_data=action.create_a_group))
    for group_id in user.groups:
        g = groups[group_id]
        markup.add(types.InlineKeyboardButton('send to ' + g.name, callback_data=action.send_to_group + str(g.id)))
    for group_id in user.created_groups:
        g = groups[group_id]
        markup.add(types.InlineKeyboardButton('get files from ' + g.name, callback_data=action.download_files_from_group + str(g.id)))
    return markup


def is_valid_uuid(uuid_to_test: str, version: int=4):
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except:
        return False
    return str(uuid_obj) == uuid_to_test


def start_invite_key(text: str):
    return len(text.split()) == 2 and is_valid_uuid(text.split()[1])


def generate_invite_link(invite_key):
    return 'https://t.me/' + secret_settings.LOGIN + '?start=' + invite_key


@bot.message_handler(commands=['start'])
@save_data_decorator
def action_start(message):
    uid = message.from_user.id

    if uid not in users:  # if it's new user, create User()
        users[uid] = User(message.from_user.username, uid)
        bot.reply_to(message, 'Hello!')

    if start_invite_key(message.text):
        invite_key = message.text.split()[1]
        for group in groups:
            if group.invite_key == invite_key:
                users[uid].groups.append(group.id)
                bot.send_message(message.chat.id, 'You have been successfully added to the ' + group.name + ' group.')
    users[uid].last_markup = bot.send_message(message.chat.id, "select an action", reply_markup=generate_menu_markup(users[uid]))


@bot.message_handler(content_types=['document'])
@save_data_decorator
def get_document(message):
    print(message.document.file_id)
    print(message.from_user.username)

    uid = message.from_user.id
    if users[uid].selected_group is None:
        bot.reply_to(message, 'Can\'t understand you')
    else:
        group_id = users[uid].selected_group
        groups[group_id].insert(uid, message.document.file_id)
        users[uid].last_markup = bot.send_message(message.chat.id,
                                                  'Ok, I received your file for group ' + groups[group_id].name,
                                                  reply_markup=back_to_menu)
        users[uid].selected_group = None


@bot.callback_query_handler(func=lambda call: action.check(action.return_to_menu, call.data))
@save_data_decorator
def show_menu(call):
    uid = call.from_user.id
    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=users[uid].last_markup.message_id,
                                  reply_markup=generate_menu_markup(users[uid]))


@bot.callback_query_handler(func=lambda call: action.check(action.create_a_group, call.data))
@save_data_decorator
def show_create_a_group_name(call):
    uid = call.from_user.id
    users[uid].status = 'creating_group_name'
    bot.send_message(chat_id=call.message.chat.id, text='Create and enter group name')


@bot.callback_query_handler(func=lambda call: action.check(action.send_file, call.data))
@save_data_decorator
def show_groups_to_send(call):
    print(call.from_user.username, call.message.text, call.data)

    uid = call.from_user.id

    markup = types.InlineKeyboardMarkup()
    if len(users[uid].groups) == 0:
        markup.row_width = 1
        markup.add(types.InlineKeyboardButton('You are not a member of any groups, return to menu',
                                              callback_data=action.return_to_menu))
    else:
        markup.row_width = len(users[uid].groups) + 1
        for group in users[uid].groups:
            group_name = groups[group].name
            markup.add(types.InlineKeyboardButton(group_name, callback_data=action.send_to_group + groups[group].name))

        markup.add(types.InlineKeyboardButton('Return to menu',
                                              callback_data=action.return_to_menu))

    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=users[uid].last_markup.message_id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: action.check(action.send_to_group, call.data))
@save_data_decorator
def parse_group_id_to_send(call):
    print(call.from_user)

    uid = call.from_user.id
    user = users[uid]
    user.selected_group = int(call.data[len(action.send_to_group):])
    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=user.last_markup.message_id,
                                  reply_markup=types.InlineKeyboardMarkup())
    bot.send_message(chat_id=call.message.chat.id, text='Now send your file, please')


@bot.callback_query_handler(func=lambda call: action.check(action.get_files, call.data))
@save_data_decorator
def show_groups_to_get_files(call):
    print(call.from_user.username, call.message.text, call.data)

    uid = call.from_user.id

    markup = types.InlineKeyboardMarkup()
    if len(users[uid].groups) == 0:
        markup.row_width = 1
        markup.add(types.InlineKeyboardButton('You didn\'t create any group, return to menu',
                                              callback_data=action.return_to_menu))
    else:
        markup.row_width = len(users[uid].groups) + 1
        for group in users[uid].groups:
            group_name = groups[group].name
            markup.add(types.InlineKeyboardButton(group_name,
                                                  callback_data=action.download_files_from_group + groups[group].name))
        markup.add(types.InlineKeyboardButton('Return to menu', callback_data=action.return_to_menu))

    print(call.data, users[uid].last_markup.message_id)
    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=users[uid].last_markup.message_id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: action.check(action.join_group, call.data))
@save_data_decorator
def join_group_via_invite_key(call):
    uid = call.from_user.id
    users[uid].status = 'entering_invite_key'
    bot.send_message(uid, 'Enter invite key')


@bot.callback_query_handler(func=lambda call: action.check(action.download_files_from_group, call.data))
@save_data_decorator
def send_zip_file_with_files(call):
    creator_uid = call.from_user.id
    user = users[creator_uid]
    user.selected_group = int(call.data[len(action.download_files_from_group):])
    group_name = groups[user.selected_group].name

    tmpdir = 'files' + str(uuid.uuid4())
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    print('created dir', tmpdir)

    for uid, file_id in groups[user.selected_group].files.items():
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        full_file_name = os.path.join(tmpdir, users[uid].username + '_' + file_info.file_path.replace('/', '_'))
        with open(full_file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

    zip_filename = group_name + '.zip'
    with zipfile.ZipFile(zip_filename, 'w') as zf:
        for dirname, subdirs, files in os.walk(tmpdir):
            zf.write(dirname)
            for filename in files:
                zf.write(os.path.join(dirname, filename))
    bot.send_document(call.message.chat.id, open(zip_filename, 'rb'))

    print('start deleting dir', tmpdir)
    os.remove(zip_filename)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print('deleted dir', tmpdir)
    users[creator_uid].last_markup = bot.send_message(call.message.chat.id, "select an action",
                                                      reply_markup=generate_menu_markup(users[creator_uid]))


@bot.message_handler(func=lambda m: True)
@save_data_decorator
def text_messages(message):
    uid = message.from_user.id
    print(users[uid].username, users[uid].status)
    if users[uid].status == 'creating_group_name':
        group_id = create_group(uid, message.text)
        users[uid].status = ''
        bot.send_message(chat_id=message.chat.id, text='group ' + message.text + ' has been created. Group invite key:')
        bot.send_message(chat_id=message.chat.id, text=groups[group_id].invite_key)
        bot.send_message(chat_id=message.chat.id, text='Or you can just share group invite link:')
        bot.send_message(chat_id=message.chat.id, text=generate_invite_link(groups[group_id].invite_key))
        users[uid].last_markup = bot.send_message(message.chat.id, "select an action",
                                                  reply_markup=generate_menu_markup(users[uid]))

    elif users[uid].status == 'entering_invite_key':
        users[uid].status = ''
        invite_key = message.text
        for group in groups:
            if group.invite_key == invite_key:
                users[uid].groups.append(group.id)
                bot.send_message(message.chat.id, 'You have been successfully added to the ' + group.name + ' group.')
        users[uid].last_markup = bot.send_message(message.chat.id, "select an action",
                                                  reply_markup=generate_menu_markup(users[uid]))


def create_group(uid, name):
    group_id = len(groups)
    groups.append(Group(group_id, uid, name, str(uuid.uuid4())))
    users[uid].created_groups.append(group_id)
    return group_id


bot.polling()
