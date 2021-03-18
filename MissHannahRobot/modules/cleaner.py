import html

from MissHannahRobot import ALLOW_EXCL, CustomCommandHandler, dispatcher
from MissHannahRobot.modules.disable import DisableAbleCommandHandler
from MissHannahRobot.modules.helpo_hannah.chat_status import (
    bot_can_delete,
    connection_status,
    dev_plus,
    user_admin,
)
from MissHannahRobot.modules.sql import cleaner_sql as sql
from telegram import ParseMode, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)

CMD_STARTERS = ("/", "!") if ALLOW_EXCL else "/"
BLUE_TEXT_CLEAN_GROUP = 13
CommandHandlerList = (CommandHandler, CustomCommandHandler, DisableAbleCommandHandler)
command_list = [
    "cleanblue",
    "ignoreblue",
    "unignoreblue",
    "listblue",
    "ungignoreblue",
    "gignoreblue" "start",
    "help",
    "settings",
    "donate",
    "stalk",
    "aka",
    "leaderboard",
]

for handler_list in dispatcher.handlers:
    for handler in dispatcher.handlers[handler_list]:
        if any(isinstance(handler, cmd_handler) for cmd_handler in CommandHandlerList):
            command_list += handler.command


@run_async
def clean_blue_text_must_click(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    if chat.get_member(bot.id).can_delete_messages and sql.is_enabled(chat.id):
        fst_word = message.text.strip().split(None, 1)[0]

        if len(fst_word) > 1 and any(
            fst_word.startswith(start) for start in CMD_STARTERS
        ):

            command = fst_word[1:].split("@")
            chat = update.effective_chat

            ignored = sql.is_command_ignored(chat.id, command[0])
            if ignored:
                return

            if command[0] not in command_list:
                message.delete()


@run_async
@connection_status
@bot_can_delete
@user_admin
def set_blue_text_must_click(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    bot, args = context.bot, context.args
    if len(args) >= 1:
        val = args[0].lower()
        if val in ("off", "no"):
            sql.set_cleanbt(chat.id, False)
            reply = "<b>{}</b> ഈ ചാറ്റിൽ ബ്യൂ-ടെക്സറ്റ് ക്ലിനിങ്ങ്‌ നിർജ്ജീവമാക്കി".format(
                html.escape(chat.title)
            )
            message.reply_text(reply, parse_mode=ParseMode.HTML)

        elif val in ("yes", "on"):
            sql.set_cleanbt(chat.id, True)
            reply = "<b>{}</b> ഈ ചാറ്റിൽ ബ്യൂ-ടെക്സറ്റ് ക്ലിനിങ്ങ്‌ സജീവമാക്കി".format(
                html.escape(chat.title)
            )
            message.reply_text(reply, parse_mode=ParseMode.HTML)

        else:
            reply = "അസാധുവായ ആർഗ്യുമെന്റ് സ്വീകരിക്കുന്ന മൂല്യങ്ങൾ 'yes', 'on', 'no', 'off'"
            message.reply_text(reply)
    else:
        clean_status = sql.is_enabled(chat.id)
        clean_status = "Enabled" if clean_status else "Disabled"
        reply = "<b>{}</b> ഇതിനായി ബുള്ളെടെക്സ്റ്റ് ക്ലീനിംഗ് : <b>{}</b>".format(
            html.escape(chat.title), clean_status
        )
        message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@user_admin
def add_bluetext_ignore(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        added = sql.chat_ignore_command(chat.id, val)
        if added:
            reply = "ബ്ലൂടെക്സ്റ്റ് ക്ലീനർ അവഗണിക്കൽ പട്ടികയിലേക്ക് ചേർത്തു <b>{}</b>".format(
                args[0]
            )
        else:
            reply = "കമാൻഡ് ഇതിനകം അവഗണിച്ചു."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "അവഗണിക്കാൻ ഒരു കമാൻഡും നൽകിയിട്ടില്ല."
        message.reply_text(reply)


@run_async
@user_admin
def remove_bluetext_ignore(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        removed = sql.chat_unignore_command(chat.id, val)
        if removed:
            reply = (
                "<b>{}</b> നെ ബ്ലൂടെക്സ്റ്റ് ക്ലീനർ അവഗണിക്കൽ പട്ടികയിൽ നിന്ന് നീക്കംചെയ്തു".format(
                    args[0]
                )
            )
        else:
            reply = "കമാൻഡ് നിലവിൽ അവഗണിച്ചിട്ടില്ല"
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "ഒപ്പിടാൻ ഒരു കമാൻഡും നൽകിയിട്ടില്ല."
        message.reply_text(reply)


@run_async
@user_admin
def add_bluetext_ignore_global(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        added = sql.global_ignore_command(val)
        if added:
            reply = "<b>{}</b> നെ ആഗോള ബ്ലൂടെക്സ്റ്റ് ക്ലീനർ അവഗണിച്ച പട്ടികയിൽ ചേർത്തു".format(
                args[0]
            )
        else:
            reply = "കമാൻഡ് ഇതിനകം അവഗണിച്ചു."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "അവഗണിക്കാൻ ഒരു കമാൻഡും നൽകിയിട്ടില്ല."
        message.reply_text(reply)


@run_async
@dev_plus
def remove_bluetext_ignore_global(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        removed = sql.global_unignore_command(val)
        if removed:
            reply = "ഈ കമാൻഡ്<b>{}</b> ആഗോള അവഗണന പട്ടികയിൽ നിന്ന് ബ്ലൂടെക്സ്റ്റിൽ നിന്ന് നീക്കംചെയ്തു.".format(
                args[0]
            )
        else:
            reply = "കമാൻഡ് നിലവിൽ അവഗണിച്ചിട്ടില്ല."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "അജ്ഞാതമാക്കാൻ ഒരു കമാൻഡും നൽകിയിട്ടില്ല."
        message.reply_text(reply)


@run_async
@dev_plus
def bluetext_ignore_list(update: Update, context: CallbackContext):

    message = update.effective_message
    chat = update.effective_chat

    global_ignored_list, local_ignore_list = sql.get_all_ignored(chat.id)
    text = ""

    if global_ignored_list:
        text = "ഇനിപ്പറയുന്ന കമാൻഡുകൾ നിലവിൽ ആഗോളതലത്തിൽ ബ്ലൂടെക്സ്റ്റ് ക്ലീനിംഗിൽ നിന്ന് അവഗണിക്കപ്പെടുന്നു :\n"

        for x in global_ignored_list:
            text += f" - <code>{x}</code>\n"

    if local_ignore_list:
        text += "ഇനിപ്പറയുന്ന കമാൻഡുകൾ നിലവിൽ ബ്ലൂടെക്സ്റ്റ് ക്ലീൻ‌ജനിൽ നിന്ന് പ്രാദേശികമായി അവഗണിക്കപ്പെടുന്നു :\n"

        for x in local_ignore_list:
            text += f" - <code>{x}</code>\n"

    if text == "":
        text = " ബ്ലൂ ടെക്സ്റ്റ് ക്ലീനിംഗിൽ നിന്ന് കമാൻഡുകളൊന്നും അവഗണിക്കുന്നില്ല."
        message.reply_text(text)
        return

    message.reply_text(text, parse_mode=ParseMode.HTML)
    return


__help__ = """
Blue text cleaner removed any made up commands that people send in your chat.
 • `/cleanblue <on/off/yes/no>`*:* clean commands after sending
 • `/ignoreblue <word>`*:* prevent auto cleaning of the command
 • `/unignoreblue <word>`*:* remove prevent auto cleaning of the command
 • `/listblue`*:* list currently whitelisted commands
 
 *Following are Disasters only commands, admins cannot use these:*
 • `/gignoreblue <word>`*:* globally ignorea bluetext cleaning of saved word across Hannah.
 • `/ungignoreblue <word>`*:* remove said command from global cleaning list
"""

SET_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("cleanblue", set_blue_text_must_click)
ADD_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("ignoreblue", add_bluetext_ignore)
REMOVE_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("unignoreblue", remove_bluetext_ignore)
ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER = CommandHandler(
    "gignoreblue", add_bluetext_ignore_global
)
REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER = CommandHandler(
    "ungignoreblue", remove_bluetext_ignore_global
)
LIST_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("listblue", bluetext_ignore_list)
CLEAN_BLUE_TEXT_HANDLER = MessageHandler(
    Filters.command & Filters.group, clean_blue_text_must_click
)

dispatcher.add_handler(SET_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(ADD_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(REMOVE_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER)
dispatcher.add_handler(REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER)
dispatcher.add_handler(LIST_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP)

__mod_name__ = "Bluetext Cleaning"
__handlers__ = [
    SET_CLEAN_BLUE_TEXT_HANDLER,
    ADD_CLEAN_BLUE_TEXT_HANDLER,
    REMOVE_CLEAN_BLUE_TEXT_HANDLER,
    ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER,
    REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER,
    LIST_CLEAN_BLUE_TEXT_HANDLER,
    (CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP),
]
