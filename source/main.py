import os
import pickle
import random
import shutil
import uuid
import zipfile

import telebot
from telebot import types

import secret_settings
from classes import action
from classes.group import (Group, create_group, get_group,
                           get_group_by_invite_key)
from classes.user import User, add_user, get_user
from data import save_data, save_data_decorator, upload_data

bot = telebot.TeleBot(secret_settings.TOKEN)

upload_data()

back_to_menu = types.InlineKeyboardMarkup()
back_to_menu.add(types.InlineKeyboardButton("Return to menu", callback_data=action.return_to_menu))


def generate_menu_markup(user: User):
    markup = types.InlineKeyboardMarkup()
    markup.row_width = len(user.groups) + len(user.created_groups) + 1
    markup.add(types.InlineKeyboardButton("Join to new group", callback_data=action.join_group),
               types.InlineKeyboardButton("Create a group", callback_data=action.create_a_group))
    for group_id in user.groups:
        g = get_group(group_id)
        markup.add(types.InlineKeyboardButton('send to ' + g.name, callback_data=action.send_to_group + str(g.id)))
    for group_id in user.created_groups:
        g = get_group(group_id)
        markup.add(types.InlineKeyboardButton('get files from ' + g.name,
                                              callback_data=action.download_files_from_group + str(g.id)))
    return markup


def is_valid_uuid(uuid_to_test: str, version: int = 4):
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except:
        return False
    return str(uuid_obj) == uuid_to_test


def have_invite_key(text: str):
    return len(text.split()) == 2 and is_valid_uuid(text.split()[1])


def generate_invite_link(invite_key):
    return 't.me/' + secret_settings.LOGIN + '?start=' + invite_key


def update_user(message):
    uid = message.from_user.id
    user = get_user(uid)
    if user is None:  # if it's new user, create User()
        user = add_user(message.from_user.username, uid)
        bot.reply_to(message, 'Hello!')
    return user


def add_user_to_group_by_invite_key(user, message):
    group = user.add_group_by_invite_key(message.text.split()[1])
    if group is not None:
        bot.send_message(message.chat.id, 'You have been successfully added to the ' + group.name + ' group.')


@bot.message_handler(commands=['start'])
@save_data_decorator
def action_start(message):
    user = update_user(message)
    if have_invite_key(message.text):
        add_user_to_group_by_invite_key(user, message)
    user.last_markup = bot.send_message(message.chat.id, "select an action", reply_markup=generate_menu_markup(user))


@bot.message_handler(content_types=['document'])
@save_data_decorator
def get_document(message):
    print(message.document.file_id)
    print(message.from_user.username)

    uid = message.from_user.id
    user = get_user(uid)
    if user.selected_group is None:
        bot.reply_to(message, 'Can\'t understand you')
    else:
        group = get_group(user.selected_group)
        group.insert(uid, message.document.file_id)
        user.last_markup = bot.send_message(message.chat.id, 'Ok, I received your file for group ' + group.name,
                                            reply_markup=back_to_menu)
        user.selected_group = None


@bot.callback_query_handler(func=lambda call: action.check(action.return_to_menu, call.data))
@save_data_decorator
def show_menu(call):
    user = get_user(call.from_user.id)
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=user.last_markup.message_id,
                                  reply_markup=generate_menu_markup(user))


@bot.callback_query_handler(func=lambda call: action.check(action.create_a_group, call.data))
@save_data_decorator
def show_create_a_group_name(call):
    user = get_user(call.from_user.id)
    user.status = 'creating_group_name'
    bot.send_message(chat_id=call.message.chat.id, text='Create and enter group name')


@bot.callback_query_handler(func=lambda call: action.check(action.send_file, call.data))
@save_data_decorator
def show_groups_to_send(call):
    print(call.from_user.username, call.message.text, call.data)

    user = get_user(call.from_user.id)

    markup = types.InlineKeyboardMarkup()
    if len(user.groups) == 0:
        markup.row_width = 1
        markup.add(types.InlineKeyboardButton('You are not a member of any groups, return to menu',
                                              callback_data=action.return_to_menu))
    else:
        markup.row_width = len(user.groups) + 1
        for group in user.groups:
            group_name = user.name
            markup.add(types.InlineKeyboardButton(group_name, callback_data=action.send_to_group + groups[group].name))

        markup.add(types.InlineKeyboardButton('Return to menu',
                                              callback_data=action.return_to_menu))

    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=user.last_markup.message_id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: action.check(action.send_to_group, call.data))
@save_data_decorator
def parse_group_id_to_send(call):
    print(call.from_user)

    user = get_user(call.from_user.id)
    user.selected_group = int(call.data[len(action.send_to_group):])
    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=user.last_markup.message_id,
                                  reply_markup=types.InlineKeyboardMarkup())
    bot.send_message(chat_id=call.message.chat.id, text='Now send your file, please')


@bot.callback_query_handler(func=lambda call: action.check(action.get_files, call.data))
@save_data_decorator
def show_groups_to_get_files(call):
    print(call.from_user.username, call.message.text, call.data)

    user = get_user(call.from_user.id)

    markup = types.InlineKeyboardMarkup()
    if len(user.groups) == 0:
        markup.row_width = 1
        markup.add(types.InlineKeyboardButton('You didn\'t create any group, return to menu',
                                              callback_data=action.return_to_menu))
    else:
        markup.row_width = len(user.groups) + 1
        for group_id in user.groups:
            group = get_group(group_id)
            markup.add(types.InlineKeyboardButton(group.name,
                                                  callback_data=action.download_files_from_group + group_id))
        markup.add(types.InlineKeyboardButton('Return to menu', callback_data=action.return_to_menu))

    print(call.data, user.last_markup.message_id)
    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=user.last_markup.message_id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: action.check(action.join_group, call.data))
@save_data_decorator
def join_group_via_invite_key(call):
    user = get_user(call.from_user.id)
    user.status = 'entering_invite_key'
    bot.send_message(user.uid, 'Enter invite key')


@bot.callback_query_handler(func=lambda call: action.check(action.download_files_from_group, call.data))
@save_data_decorator
def send_zip_file_with_files(call):
    creator_uid = call.from_user.id
    user = get_user(creator_uid)
    user.selected_group = int(call.data[len(action.download_files_from_group):])
    group = get_group(user.selected_group)

    tmpdir = 'files' + str(uuid.uuid4())
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    print('created dir', tmpdir)

    for uid, file_id in group.files.items():
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        full_file_name = os.path.join(tmpdir, get_user(uid).username + '_' + file_info.file_path.replace('/', '_'))
        with open(full_file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

    zip_filename = group.name + '.zip'
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
    user.last_markup = bot.send_message(call.message.chat.id, "select an action",
                                        reply_markup=generate_menu_markup(user))


@bot.message_handler(func=lambda m: True)
@save_data_decorator
def text_messages(message):
    user = get_user(message.from_user.id)
    print(user.username, user.status)
    if user.status == 'creating_group_name':
        group_id = create_group(user.uid, message.text)
        user.status = ''
        bot.send_message(chat_id=message.chat.id, text='group ' + message.text + ' has been created. Group invite key:')
        bot.send_message(chat_id=message.chat.id, text=get_group(group_id).invite_key)
        bot.send_message(chat_id=message.chat.id, text='Or you can just share group invite link:')
        bot.send_message(chat_id=message.chat.id, text=generate_invite_link(get_group(group_id).invite_key))
        user.last_markup = bot.send_message(message.chat.id, "select an action",
                                            reply_markup=generate_menu_markup(user))

    elif user.status == 'entering_invite_key':
        user.status = ''
        invite_key = message.text
        group = get_group_by_invite_key(invite_key)
        if group is not None:
            user.groups.append(group.id)
            bot.send_message(message.chat.id, 'You have been successfully added to the ' + group.name + ' group.')
        user.last_markup = bot.send_message(message.chat.id, 'select an action',
                                            reply_markup=generate_menu_markup(user))


bot.polling()
