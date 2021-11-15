import os

# Set your api tokens and keys through environmental variables
# (add lines to your .bashrc and restart terminal):
# export RFDLIFE_BOT_TOKEN='XXXXX:XXXXXXXXXXX'
# export RFDLIFE_BOT_AUTH_LOGIN='first_name.second_name'
# export RFDLIFE_BOT_AUTH_PSWD='corp_password'
# export RFDLIFE_BOT_ACCESS_PSWD='registration_password'
#
# OR
#
# Вручную, используя значения по умолчанию в этом файле.
# Важно: отменить отслеживание файла, чтобы предотвратить случайное нажатие на частный токен:
# 'git update-index --assume-unchanged tokens.py'

# [ Required ]

default_bot = ''
bot = os.getenv('RFDLIFE_BOT_TOKEN', default_bot)

default_auth_login = ''
auth_login = os.getenv('RFDLIFE_BOT_AUTH_LOGIN', default_auth_login)

default_auth_pswd = ''
auth_pswd = os.getenv('RFDLIFE_BOT_AUTH_PSWD', default_auth_pswd)

default_access_pswd = ''
access_pswd = os.getenv('RFDLIFE_BOT_ACCESS_PSWD', default_access_pswd)

# [ Optional ]

default_provider_token = ''
provider_token = os.getenv('RFDLIFE_BOT_PROVIDER_TOKEN', default_provider_token)

default_chatbase_token = ''
chatbase_token = os.getenv('RFDLIFE_BOT_CHATBASE_TOKEN', default_chatbase_token)

default_dumping_channel = ''
dumping_channel_id = os.getenv('RFDLIFE_BOT_DUMPING_CHANNEL', default_dumping_channel)
