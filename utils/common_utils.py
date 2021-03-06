import functools
import re
import threading
from datetime import datetime
from os import path

import config
import tokens
from utils.bot_analytics import BotAnalytics
from utils.telebot_wrapper import TelebotWrapper

my_bot = TelebotWrapper(tokens.bot, threaded=False)
my_analytics = BotAnalytics(api_key=tokens.chatbase_token)

global_lock = threading.Lock()


def commands_handler(cmnds):
    def wrapped(message):
        if not message.text:
            return False
        split_message = re.split(r'[^\w@/]', message.text.lower())

        s = split_message[0]
        return (s in cmnds) or (s.endswith(my_bot.name) and s.split('@')[0] in cmnds)

    return wrapped


def user_name(user):
    first_name = user.first_name
    last_name = ' ' + user.last_name if isinstance(user.last_name, str) else ''
    return first_name + last_name


def user_info(user):
    # Required fields
    user_id = str(user.id)
    first_name = user.first_name
    # Optional fields
    last_name = ' ' + user.last_name if isinstance(user.last_name, str) else ''
    username = ', @' + user.username if isinstance(user.username, str) else ''
    language_code = ', ' + user.language_code if isinstance(user.language_code, str) else ''
    # Output
    return user_id + ' (' + first_name + last_name + username + language_code + ')'


def chat_info(chat):
    if chat.type == 'private':
        return 'private'
    else:
        return chat.type + ': ' + chat.title + ' (' + str(chat.id) + ')'


def curr_time():
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


def action_log(text):
    print('{}\n{}\n'.format(curr_time(), text))


def user_action_log(message, text):
    if hasattr(message, 'chat'):
        print('{}, {}\nUser {} {}\n'.format(curr_time(), chat_info(message.chat), user_info(message.from_user), text))
    else:
        print('{}\nUser {} {}\n'.format(curr_time(), user_info(message.from_user), text))


def is_command():
    def wrapped(message):
        if not message.text or not message.text.startswith('/'):
            return False
        return True

    return wrapped


def not_command():
    def wrapped(message):
        if message.text and not message.text.startswith('/'):
            return True
        return False

    return wrapped


def command_with_delay(delay=10):
    def decorator(func):
        def wrapped(message):
            now = datetime.now().timestamp()
            diff = now - func.last_call if hasattr(func, 'last_call') else now
            if diff < delay:
                user_action_log(message, 'called {} after {} sec, delay is {}'.format(func, round(diff), delay))
                return
            func.last_call = now

            return func(message)

        return wrapped

    return decorator


def bot_admin_command(func):
    def wrapped(message):
        if message.from_user.id in config.admin_ids:
            return func(message)
        return

    return wrapped


def chai_user_command(func):
    def wrapped(message):
        if message.from_user.id in config.chai_subscribers:
            return func(message)
        return

    return wrapped


def skip_exception(exception):
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception:
                pass

        return wrapped

    return decorator


def check_outdated_callback(delay, cmd):
    def decorator(func):
        def wrapped(call):
            message = call.message
            if datetime.now().timestamp() - message.date > delay:
                my_bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id,
                                         text='{}\n\n?????? ?????????????????? ????????????????! ?????????????????? {}.'.format(message.text, cmd))
                my_bot.answer_callback_query(callback_query_id=call.id, text='?????? ?????????????????? ????????????????!')
                return

            return func(call)

        return wrapped

    return decorator


def is_non_zero_file(file_path):
    return path.isfile(file_path) and path.getsize(file_path) > 0


def value_from_file(file_name, default=0):
    value = default
    if path.isfile(file_name):
        global_lock.acquire()
        with open(file_name, 'r', encoding='utf-8') as file:
            file_data = file.read()
            if file_data.isdigit():
                value = int(file_data)
        global_lock.release()
    return value


def value_to_file(file_name, value):
    global_lock.acquire()
    with open(file_name, 'w+', encoding='utf-8') as file:
        file.write(str(value))
    global_lock.release()


def send_file(chat_id, file_name, **kwargs):
    if is_non_zero_file(file_name):
        with open(file_name, 'r', encoding='utf-8') as file:
            return my_bot.send_document(chat_id, file, **kwargs)


def russian_month_name(month, is_nominative=False, is_uppercase_starting=False):
    months_nom = ['????????????', '??????????????', '????????', '????????????',
                  '??????', '????????', '????????', '????????????',
                  '????????????????', '??????????????', '????????????', '??????????????']

    months_gen = ['????????????', '??????????????', '??????????', '????????????',
                  '??????', '????????', '????????', '??????????????',
                  '????????????????', '??????????????', '????????????', '??????????????']

    months = months_nom if is_nominative else months_gen
    return months[month].title() if is_uppercase_starting else months[month]


class TimeMemoize(object):
    """Memoize with timeout"""
    _caches = {}
    _delays = {}

    def __init__(self, delay=10):
        self.delay = delay

    def collect(self):
        """Clear cache of results which have timed out"""
        for func in self._caches:
            cache = {}
            for key in self._caches[func]:
                if (datetime.now().timestamp() - self._caches[func][key][1]) < self._delays[func]:
                    cache[key] = self._caches[func][key]
            self._caches[func] = cache

    def __call__(self, f):
        self.cache = self._caches[f] = {}
        self._delays[f] = self.delay

        def func(*args, **kwargs):
            kw = sorted(kwargs.items())
            key = (args, tuple(kw))
            time = datetime.now().timestamp()
            try:
                v = self.cache[key]
                if (time - v[1]) > self.delay:
                    raise KeyError
            except KeyError:
                v = self.cache[key] = f(*args, **kwargs), time
            return v[0]

        func.func_name = f.__name__
        return func


def cut_long_text(text, max_len=4000):
    """
    ?????????????? ?????? ?????????????? ?????????????? ?????????????????? ???? ???????????????? ?????????? ?????? ???? ?????????? ?? ?????????? ?????????????????????? ?????? ???? ??????????????
    :param text: ?????????? ?????? ??????????????
    :param max_len: ??????????, ?????????????? ???????????? ??????????????????
    :return: ???????????? ?????????????? ???????????? max_len, ???????????????? ???????????? text
    """
    last_cut = 0
    space_anchor = 0
    dot_anchor = 0
    nl_anchor = 0

    if len(text) < max_len:
        yield text[last_cut:]
        return

    for i in range(len(text)):
        if text[i] == '\n':
            nl_anchor = i + 1
        if text[i] == '.' and text[i + 1] == ' ':
            dot_anchor = i + 2
        if text[i] == ' ':
            space_anchor = i

        if i - last_cut > max_len:
            if nl_anchor > last_cut:
                yield text[last_cut:nl_anchor]
                last_cut = nl_anchor
            elif dot_anchor > last_cut:
                yield text[last_cut:dot_anchor]
                last_cut = dot_anchor
            elif space_anchor > last_cut:
                yield text[last_cut:space_anchor]
                last_cut = space_anchor
            else:
                yield text[last_cut:i]
                last_cut = i

            if len(text) - last_cut < max_len:
                yield text[last_cut:]
                return

    yield text[last_cut:]


def bold(text, mode='html'):
    if mode.lower() == 'html':
        return '<b>{}</b>'.format(text)
    if mode.lower() == 'markdown':
        return '*{}*'.format(text)


def code(text, mode='html'):
    if mode.lower() == 'html':
        return '<code>{}</code>'.format(text)
    if mode.lower() == 'markdown':
        return '`{}`'.format(text)


def link(text, user_id, mode='html'):
    if mode.lower() == 'html':
        return '<a href=\'tg://user?id={0}\'>{1}</a>'.format(user_id, text)
    if mode.lower() == 'markdown':
        return '[{1}](tg://user?id={0})'.format(user_id, text)


def link_user(user, mode='html'):
    if mode.lower() == 'html':
        return '<a href=\'tg://user?id={0}\'>{1}</a>'.format(user.id, user_name(user))
    if mode.lower() == 'markdown':
        return '[{1}](tg://user?id={0})'.format(user.id, user_name(user))


def subs_notify(subs, text, keyboard=None, me=None):
    fails = []
    for chat_id in subs:
        if chat_id != me:
            ret = my_bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
            if not ret:
                fails.append(str(chat_id))
                if me:
                    my_bot.send_message(me, '?????? ?????????????????? {} ???? ??????????????????????'.format(link('????????????????', chat_id)),
                                        parse_mode='HTML')
    if len(fails) != 0:
        action_log('Notifying failed for: [{}]'.format(', '.join(fails)))
