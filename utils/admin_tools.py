import os
import sys

import config
from utils.common_utils import my_bot, user_action_log, value_to_file


def kill_bot(message):
    if not hasattr(kill_bot, 'check_sure'):
        kill_bot.check_sure = True
        return
    value_to_file(config.FileLocation.bot_killed, 1)
    my_bot.send_document(message.chat.id, 'https://t.me/rfd_life_bot',
                         caption='Ухожу на отдых!', reply_to_message_id=message.message_id)
    user_action_log(message, 'remotely killed bot.')
    sys.exit(0)


def update_bot(message):
    if not hasattr(update_bot, 'check_sure'):
        update_bot.check_sure = True
        return

    my_bot.reply_to(message, 'Ух, ухожу на обновление...')
    user_action_log(message, 'remotely ran update script.')
    os.execl('/bin/bash', 'bash', 'utils/__bot_update.sh')
