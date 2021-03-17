import html
import re

from telegram import ParseMode, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async
from telegram.utils.helpers import mention_html

import MissHannahRobot.modules.sql.blacklist_sql as sql
from MissHannahRobot import dispatcher, LOGGER
from MissHannahRobot.modules.disable import DisableAbleCommandHandler
from MissHannahRobot.modules.helpo_hannah.chat_status import user_admin, user_not_admin
from MissHannahRobot.modules.helpo_hannah.extraction import extract_text
from MissHannahRobot.modules.helpo_hannah.misc import split_message
from MissHannahRobot.modules.log_channel import loggable
from MissHannahRobot.modules.warns import warn
from MissHannahRobot.modules.helpo_hannah.string_handling import extract_time
from MissHannahRobot.modules.connection import connected
from MissHannahRobot.modules.sql.approve_sql import is_approved
from MissHannahRobot.modules.helpo_hannah.alternate import send_message, typing_action

BLACKLIST_GROUP = 11


@run_async
@user_admin
@typing_action
def blacklist(update, context):
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if chat.type == "private":
            return
        chat_id = update.effective_chat.id
        chat_name = chat.title

    filter_list = "<b>{}</b> ഗ്രൂപ്പിലെ ബ്ലാക്ക്ലിസ്റ്റ് പദങ്ങൾ:\n".format(chat_name)

    all_blacklisted = sql.get_chat_blacklist(chat_id)

    if len(args) > 0 and args[0].lower() == "copy":
        for trigger in all_blacklisted:
            filter_list += "<code>{}</code>\n".format(html.escape(trigger))
    else:
        for trigger in all_blacklisted:
            filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    # for trigger in all_blacklisted:
    #     filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(filter_list)
    for text in split_text:
        if filter_list == "<b>{}</b> ഗ്രൂപ്പിൽ ഇപ്പോൾ ഉള്ള ബ്ലാക്ക്ലിസ്റ്റ് പദങ്ങൾ:\n".format(
            html.escape(chat_name)
        ):
            send_message(
                update.effective_message,
                "No blacklisted words in <b>{}</b>!".format(html.escape(chat_name)),
                parse_mode=ParseMode.HTML,
            )
            return
        send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@run_async
@user_admin
@typing_action
def add_blacklist(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)

    conn = connected(context.bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_blacklist = list(
            {trigger.strip() for trigger in text.split("\n") if trigger.strip()}
        )
        for trigger in to_blacklist:
            sql.add_to_blacklist(chat_id, trigger.lower())

        if len(to_blacklist) == 1:
            send_message(
                update.effective_message,
                "Added blacklist <code>{}</code> in chat: <b>{}</b>!".format(
                    html.escape(to_blacklist[0]), html.escape(chat_name)
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                update.effective_message,
                "Added blacklist trigger: <code>{}</code> in <b>{}</b>!".format(
                    len(to_blacklist), html.escape(chat_name)
                ),
                parse_mode=ParseMode.HTML,
            )

    else:
        send_message(
            update.effective_message,
            "ബ്ലാക്ക്ലിസ്റ്റ് ചേർക്കേണ്ട പദങ്ങൾ അയ്ക്കു.",
        )


@run_async
@user_admin
@typing_action
def unblacklist(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)

    conn = connected(context.bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(
            {trigger.strip() for trigger in text.split("\n") if trigger.strip()}
        )
        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                send_message(
                    update.effective_message,
                    "<code>{}</code>ഈ പദം <b>{}</b> ഗ്രൂപ്പിലെ ബ്ലാക്ക്ലിസ്റ്റ് നിന്ന് ഒഴിവാക്കി!".format(
                        html.escape(to_unblacklist[0]), html.escape(chat_name)
                    ),
                    parse_mode=ParseMode.HTML,
                )
            else:
                send_message(
                    update.effective_message, "ഇത് ഒരു ബ്ലാക്ക്ലിസ്റ്റ് പദം അല്ല!"
                )

        elif successful == len(to_unblacklist):
            send_message(
                update.effective_message,
                "<code>{}</code> ഈ പദം <b>{}</b> ലെ ബ്ലാക്ക്ലിസ്റ്റ്ൽ നിന്ന് ഒഴിവാക്കി!".format(
                    successful, html.escape(chat_name)
                ),
                parse_mode=ParseMode.HTML,
            )

        elif not successful:
            send_message(
                update.effective_message,
                "നിങ്ങൾ ഇപ്പോൾ പറഞ്ഞ ട്രിഗേർസ് ഈ ചാറ്റിൽ ഇതുവരെ അഡ് ചെയിതിട്ടില്ല!.",
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                update.effective_message,
                "<code>{}</code> ഈ ട്രിഗർ ഇതുവരെ {} ആഡ് ആക്കിട്ടില്ല!"
                "so were not removed.".format(
                    successful, len(to_unblacklist) - successful
                ),
                parse_mode=ParseMode.HTML,
            )
    else:
        send_message(
            update.effective_message,
            "ഏത്ഒക്കെ ട്രിഗേർസ് ആണ് ഈ ചാറ്റിൽ നിന്ന് റീമൂവ് ആകേണ്ടത് എന്ന പറയു!",
        )


@run_async
@loggable
@user_admin
@typing_action
def blacklist_mode(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "ഈ കമാൻഡ് പി.എം അല്ല ഗ്രൂപ്പിൽ ആണ് ഉപയോഗിക്കേണ്ടത്.",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() in ["off", "nothing", "no"]:
            settypeblacklist = "do nothing"
            sql.set_blacklist_strength(chat_id, 0, "0")
        elif args[0].lower() in ["del", "delete"]:
            settypeblacklist = "delete blacklisted message"
            sql.set_blacklist_strength(chat_id, 1, "0")
        elif args[0].lower() == "warn":
            settypeblacklist = "warn the sender"
            sql.set_blacklist_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeblacklist = "mute the sender"
            sql.set_blacklist_strength(chat_id, 3, "0")
        elif args[0].lower() == "kick":
            settypeblacklist = "kick the sender"
            sql.set_blacklist_strength(chat_id, 4, "0")
        elif args[0].lower() == "ban":
            settypeblacklist = "ban the sender"
            sql.set_blacklist_strength(chat_id, 5, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """ നിങ്ങൾക്ക് ബ്ലാക്ക്ലിസ്റ്റ് മോഡ് തന്നിരിക്കുന്ന രീതിയിൽ സെറ്റ് ചെയു;Try, `/blacklistmode tban <timevalue>`.
				
Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """Invalid time value!
Example of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            settypeblacklist = "temporarily ban for {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for blacklist but you didn't specified  time; try, `/blacklistmode tmute <timevalue>`.

Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """Invalid time value!
Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            settypeblacklist = "temporarily mute for {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            send_message(
                update.effective_message,
                "നിങ്ങൾ പറഞ്ഞത് എന്നിക്ക് മനസ്സിലായില്ല: off/del/warn/ban/kick/mute/tban/tmute!",
            )
            return ""
        if conn:
            text = "ബ്ലാക്ക്ലിസ്റ്റ് മോഡ് ചെയ്ഞ്ച് ആക്കി: `{}` ടൂ' *{}*!".format(
                settypeblacklist, chat_name
            )
        else:
            text = "ബ്ലാക്ക്ലിസ്റ്റ് മോഡ് ചെയ്ഞ്ച് ആക്കി: `{}`!".format(settypeblacklist)
        send_message(update.effective_message, text, parse_mode="markdown")
        return (
            "<b>{}:</b>\n"
            "<b> അഡ്മിൻ:</b> {}\n"
            "ബ്ലാക്ക്ലിസ്റ്റ് മോഡ് മാറ്റി. ഇപ്പോൾ നിലവിലുള്ള മോഡ്{}.".format(
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
                settypeblacklist,
            )
        )
    else:
        getmode, getvalue = sql.get_blacklist_setting(chat.id)
        if getmode == 0:
            settypeblacklist = "do nothing"
        elif getmode == 1:
            settypeblacklist = "delete"
        elif getmode == 2:
            settypeblacklist = "warn"
        elif getmode == 3:
            settypeblacklist = "mute"
        elif getmode == 4:
            settypeblacklist = "kick"
        elif getmode == 5:
            settypeblacklist = "ban"
        elif getmode == 6:
            settypeblacklist = "temporarily ban for {}".format(getvalue)
        elif getmode == 7:
            settypeblacklist = "temporarily mute for {}".format(getvalue)
        if conn:
            text = "ഇപ്പോഴത്തെ ബ്ലാക്ക്ലിസ്റ്റ് മോഡ്: *{}* ടൂ *{}*.".format(
                settypeblacklist, chat_name
            )
        else:
            text = " ഇപ്പോഴത്തെ ബ്ലാക്ക്ലിസ്റ്റ് മോഡ്: *{}*.".format(settypeblacklist)
        send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
    return ""


def findall(p, s):
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i + 1)


@run_async
@user_not_admin
def del_blacklist(update, context):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    bot = context.bot
    to_match = extract_text(message)
    if not to_match:
        return
    if is_approved(chat.id, user.id):
        return
    getmode, value = sql.get_blacklist_setting(chat.id)

    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                if getmode == 0:
                    return
                elif getmode == 1:
                    try:
                        message.delete()
                    except BadRequest:
                        pass
                elif getmode == 2:
                    try:
                        message.delete()
                    except BadRequest:
                        pass
                    warn(
                        update.effective_user,
                        chat,
                        ("Using blacklisted trigger: {}".format(trigger)),
                        message,
                        update.effective_user,
                    )
                    return
                elif getmode == 3:
                    message.delete()
                    bot.restrict_chat_member(
                        chat.id,
                        update.effective_user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    bot.sendMessage(
                        chat.id,
                        f"Muted {user.first_name} for using Blacklisted word: {trigger}!",
                    )
                    return
                elif getmode == 4:
                    message.delete()
                    res = chat.unban_member(update.effective_user.id)
                    if res:
                        bot.sendMessage(
                            chat.id,
                            f"Kicked {user.first_name} for using Blacklisted word: {trigger}!",
                        )
                    return
                elif getmode == 5:
                    message.delete()
                    chat.kick_member(user.id)
                    bot.sendMessage(
                        chat.id,
                        f"Banned {user.first_name} for using Blacklisted word: {trigger}",
                    )
                    return
                elif getmode == 6:
                    message.delete()
                    bantime = extract_time(message, value)
                    chat.kick_member(user.id, until_date=bantime)
                    bot.sendMessage(
                        chat.id,
                        f"Banned {user.first_name} until '{value}' for using Blacklisted word: {trigger}!",
                    )
                    return
                elif getmode == 7:
                    message.delete()
                    mutetime = extract_time(message, value)
                    bot.restrict_chat_member(
                        chat.id,
                        user.id,
                        until_date=mutetime,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    bot.sendMessage(
                        chat.id,
                        f"Muted {user.first_name} until '{value}' for using Blacklisted word: {trigger}!",
                    )
                    return
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    LOGGER.exception("Error while deleting blacklist message.")
            break


def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get("blacklist", {})
    for trigger in blacklist:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return "There are {} blacklisted words.".format(blacklisted)


def __stats__():
    return "• {} blacklist triggers, across {} chats.".format(
        sql.num_blacklist_filters(), sql.num_blacklist_filter_chats()
    )


__mod_name__ = "Blacklists"

__help__ = """

Blacklists are used to stop certain triggers from being said in a group. Any time the trigger is mentioned, the message will immediately be deleted. A good combo is sometimes to pair this up with warn filters!

*NOTE*: Blacklists do not affect group admins.

 • `/blacklist`*:* View the current blacklisted words.

Admin only:
 • `/addblacklist <triggers>`*:* Add a trigger to the blacklist. Each line is considered one trigger, so using different lines will allow you to add multiple triggers.
 • `/unblacklist <triggers>`*:* Remove triggers from the blacklist. Same newline logic applies here, so you can remove multiple triggers at once.
 • `/blacklistmode <off/del/warn/ban/kick/mute/tban/tmute>`*:* Action to perform when someone sends blacklisted words.

"""
BLACKLIST_HANDLER = DisableAbleCommandHandler(
    "blacklist", blacklist, pass_args=True, admin_ok=True
)
ADD_BLACKLIST_HANDLER = CommandHandler("addblacklist", add_blacklist)
UNBLACKLIST_HANDLER = CommandHandler("unblacklist", unblacklist)
BLACKLISTMODE_HANDLER = CommandHandler("blacklistmode", blacklist_mode, pass_args=True)
BLACKLIST_DEL_HANDLER = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.group,
    del_blacklist,
    allow_edit=True,
)

dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLISTMODE_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)

__handlers__ = [
    BLACKLIST_HANDLER,
    ADD_BLACKLIST_HANDLER,
    UNBLACKLIST_HANDLER,
    BLACKLISTMODE_HANDLER,
    (BLACKLIST_DEL_HANDLER, BLACKLIST_GROUP),
]
