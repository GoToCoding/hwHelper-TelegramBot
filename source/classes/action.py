send_to_group = 'cb_send_to_group'
send_file = 'cb_send_file'
return_to_menu = 'cb_return_to_menu'
create_a_group = 'cb_create_a_group'
get_files = 'cb_get_files'
download_files_from_group = 'cb_download_files_from_group'
join_group = 'cb_join_to_new_group'


def check(action: str, callback_data: str):
    return callback_data.startswith(action)
