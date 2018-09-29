import telebot
from telebot import types
from actions import download_pdf
from classes.user import User


TOKEN = '651457991:AAHXz_0AeCAcax2A6LbxRChFXHtE4sDLRAk'
bot = telebot.TeleBot(TOKEN)

users = {}
groups = {}

actionSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True)  # create the image selection keyboard
actionSelect.add(u'Отправить файл', u'Создать группу')

markup_menu = types.InlineKeyboardMarkup()
markup_menu.row_width = 2
markup_menu.add(types.InlineKeyboardButton("Send file", callback_data="cb_send_file"),
                types.InlineKeyboardButton("Create a group", callback_data="cb_create_group"))


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, u'Привет!')
    uid = message.from_user.id
    name = message.from_user.username
    user = User(name, uid)
    user.groups = ['group_1', 'group_2', 'group_N']
    users[uid] = user
    users[uid].last_markup = bot.send_message(message.chat.id, "select an action", reply_markup=markup_menu)


@bot.message_handler(commands=['check'])
def check(message):
    bot.send_document(message.chat.id, open('/home/ruzal/Workspace/projects/pythonProj1/homeWorkHelperBot'
                                            '/homeWorkHelperBot/files/GoToCoding_documents_file_11.log', 'rb'))


@bot.message_handler(content_types=['document'])
def handle_docs_audio(message):
    print(bot.get_file(message.document.file_id).file_path)
    url = 'https://api.telegram.org/file/bot' + TOKEN + '/' + bot.get_file(message.document.file_id).file_path
    print(url)
    filename = message.from_user.username + '_' + bot.get_file(message.document.file_id).file_path.replace('/', '_')
    res = download_pdf.download_file(url, filename)
    print(res)


@bot.callback_query_handler(func=lambda call: 'cb_send_file' in call.data)
def callback_query(call):
    uid = call.from_user.id
    print(call.from_user.username, call.message.text, call.data)
    markup = types.InlineKeyboardMarkup()
    markup.row_width = len(users[uid].groups)
    for group in users[uid].groups:
        markup.add(types.InlineKeyboardButton(group, callback_data='cb_send_to_group_' + group))

    if len(users[uid].groups) == 0:
        markup.add(types.InlineKeyboardButton('You are not a member of any groups', callback_data='cb_no_groups' + group))

    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=users[uid].last_markup.message_id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: 'cb_send_to_group_' in call.data)
def callback_query(call):
    uid = call.from_user.id
    print(call.from_user)
    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=users[uid].last_markup.message_id,
                                  reply_markup=types.InlineKeyboardMarkup())
    bot.send_message(chat_id=call.message.chat.id, text='Now send your file, please')
    user = users[uid]
    user.selected_group = call.data[len('cb_send_to_group_'):]
    print(users[uid].selected_group)


@bot.message_handler(func=lambda m: True)
def echo_all(message):
    print(message.text)


bot.polling()
