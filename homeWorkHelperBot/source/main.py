import os
import shutil
import zipfile

import bottoken
import telebot
from telebot import types
from actions import download_pdf
from classes.user import User
from classes.group import Group
from classes import action


bot = telebot.TeleBot(bottoken.TOKEN)

# need to store it somewhere
users = {}
groups = []

markup_menu = types.InlineKeyboardMarkup()
markup_menu.row_width = 2
markup_menu.add(types.InlineKeyboardButton("Send file", callback_data=action.send_file),
                types.InlineKeyboardButton("Create a group", callback_data=action.create_a_group),
                types.InlineKeyboardButton("Get files", callback_data=action.get_files))

back_to_menu = types.InlineKeyboardMarkup()
back_to_menu.add(types.InlineKeyboardButton("Return to menu", callback_data=action.return_to_menu))


@bot.message_handler(commands=['start'])
def action_start(message):
    bot.reply_to(message, 'Hello!')
    uid = message.from_user.id
    name = message.from_user.username
    user = User(name, uid)
    user.groups = []
    users[uid] = user
    users[uid].last_markup = bot.send_message(message.chat.id, "select an action", reply_markup=markup_menu)


# bad_func
@bot.message_handler(commands=['get_files'])
def action_get(message):
    uid = message.from_user.id
    for group in users[uid].created_groups:
        for uid, file_id in groups[group].files.items():
            bot.send_document(message.chat.id, str(file_id))


@bot.message_handler(content_types=['document'])
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
def show_menu(call):
    uid = call.from_user.id
    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=users[uid].last_markup.message_id,
                                  reply_markup=markup_menu)


@bot.callback_query_handler(func=lambda call: action.check(action.create_a_group, call.data))
def show_create_a_group_name(call):
    uid = call.from_user.id
    bot.send_message(chat_id=call.message.chat.id, text='Create and enter group name')
    users[uid].status = 'creating_group_name'


@bot.callback_query_handler(func=lambda call: action.check(action.send_file, call.data))
def show_groups_to_send(call):
    print(call.from_user.username, call.message.text, call.data)

    uid = call.from_user.id

    markup = types.InlineKeyboardMarkup()
    if len(users[uid].groups) == 0:
        markup.row_width = 1
        markup.add(types.InlineKeyboardButton('You are not a member of any groups, return to menu',
                                              callback_data=action.return_to_menu))
    else:
        markup.row_width = len(users[uid].groups)
        for group in users[uid].groups:
            group_name = groups[group].name
            markup.add(types.InlineKeyboardButton(group_name, callback_data=action.send_to_group + groups[group].name))

    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=users[uid].last_markup.message_id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: action.check(action.send_to_group, call.data))
def parse_group_id_to_send(call):
    print(call.from_user)

    uid = call.from_user.id
    user = users[uid]
    group_name = call.data[len(action.send_to_group):]
    for group in groups:
        if group.name == group_name:
            user.selected_group = group.id
    print(group_name, users[uid].selected_group)

    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=users[uid].last_markup.message_id,
                                  reply_markup=types.InlineKeyboardMarkup())
    bot.send_message(chat_id=call.message.chat.id, text='Now send your file, please')


@bot.callback_query_handler(func=lambda call: action.check(action.get_files, call.data))
def show_groups_to_get_files(call):
    print(call.from_user.username, call.message.text, call.data)

    uid = call.from_user.id

    markup = types.InlineKeyboardMarkup()
    if len(users[uid].groups) == 0:
        markup.row_width = 1
        markup.add(types.InlineKeyboardButton('You didn\'t create any group, return to menu',
                                              callback_data=action.return_to_menu))
    else:
        markup.row_width = len(users[uid].groups)
        for group in users[uid].groups:
            group_name = groups[group].name
            markup.add(types.InlineKeyboardButton(group_name, callback_data=action.download_files_from_group + groups[group].name))
    print(call.data, users[uid].last_markup.message_id)
    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=users[uid].last_markup.message_id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: action.check(action.download_files_from_group, call.data))
def send_zip_file_with_files(call):
    creator_uid = call.from_user.id
    user = users[creator_uid]
    group_name = call.data[len(action.download_files_from_group):]
    for group in groups:
        if group.name == group_name:
            user.selected_group = group.id

    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    print('created tmp')

    for uid, file_id in groups[user.selected_group].files.items():
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        full_file_name = os.path.join('tmp', users[uid].username + '_' + file_info.file_path.replace('/', '_'))
        with open(full_file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

    zip_filename = group_name + '.zip'
    zf = zipfile.ZipFile(zip_filename, 'w')
    for dirname, subdirs, files in os.walk('tmp'):
        zf.write(dirname)
        for filename in files:
            zf.write(os.path.join(dirname, filename))
    zf.close()
    bot.send_document(call.message.chat.id, open(zip_filename, 'rb'))
    print('start deleting tmp')
    os.remove(zip_filename)
    shutil.rmtree('tmp', ignore_errors=True)
    print('deleted tmp')


@bot.message_handler(func=lambda m: True)
def text_messages(message):
    uid = message.from_user.id
    print(users[uid].username, users[uid].status)
    if users[uid].status == 'creating_group_name':
        create_group(uid, message.text)
        users[uid].status = 'entering_participants_nicknames'
        bot.send_message(chat_id=message.chat.id, text='group ' + message.text + ' has been created. Now send send '
                                                                                 'user nicknames separated by a space')
    elif users[uid].status == 'entering_participants_nicknames':
        nicknames = message.text.split()
        group_id = users[uid].created_groups[-1]
        for nick in nicknames:
            if nick[0] == '@':
                user_nick = nick[1:]
                for user_id, user in users.items():
                    if user.username.lower() == user_nick.lower():
                        user.groups.append(group_id)
        users[uid].status = ""
        bot.send_message(chat_id=message.chat.id, text='group ' + message.text + 'Ok, got it!')
        users[uid].last_markup = bot.send_message(message.chat.id, "select an action", reply_markup=markup_menu)


def create_group(uid, name):
    group_id = len(groups)
    groups.append(Group(group_id, uid, name))
    users[uid].created_groups.append(group_id)


bot.polling()
