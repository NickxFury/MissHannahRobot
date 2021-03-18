# Module to blacklist users and prevent them from using commands by @TheRealPhoenix
import html
import MissHannahRobot.modules.sql.blacklistusers_sql as sql
from MissHannahRobot import (
    DEV_USERS,
    OWNER_ID,
    DRAGONS,
    DEMONS,
    TIGERS,
    WOLVES,
    dispatcher,
)
from MissHannahRobot.modules.helpo_hannah.chat_status import dev_plus
from MissHannahRobot.modules.helpo_hannah.extraction import (
    extract_user,
    extract_user_and_text,
)
from MissHannahRobot.modules.log_channel import gloggable
from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html

BLACKLISTWHITELIST = [OWNER_ID] + DEV_USERS + DRAGONS + WOLVES + DEMONS
BLABLEUSERS = [OWNER_ID] + DEV_USERS


@run_async
@dev_plus
@gloggable
def bl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("നിങ്ങൾ പറഞ്ഞ ആളെ എന്നിക്ക് സംശയം ഉണ്ട്!.")
        return ""

    if user_id == bot.id:
        message.reply_text("നീ എന്ത് തേങ്ങയ ഈ പറയണത്?")
        return ""

    if user_id in BLACKLISTWHITELIST:
        message.reply_text("ഇദ്ദേഹം പാവം ആണ്.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("നീ പറഞ്ഞ ആളെ ഞാൻ കണ്ടിട്ടുപോലും ഇല്ല!.")
            return ""
        else:
            raise

    sql.blacklist_user(user_id, reason)
    message.reply_text("ഈ ഉപയോക്താവിന്റെ നിലനിൽപ്പിനെ ഞാൻ അവഗണിക്കും!")
    log_message = (
        f"#BLACKLIST\n"
        f"<b>അഡ്മിൻ:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>യൂസർ:</b> {mention_html(target_user.id, html.escape(target_user.first_name))}"
    )
    if reason:
        log_message += f"\n<b>കാരണം:</b> {reason}"

    return log_message


@run_async
@dev_plus
@gloggable
def unbl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text("നിങ്ങൾ പറഞ്ഞ ആളെ എന്നിക്ക് സംശയം ഉണ്ട്.")
        return ""

    if user_id == bot.id:
        message.reply_text("ഞാൻ എപ്പോഴും എന്നെ സ്വയം ശ്രദ്ധിക്കുന്നു.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "ഉപയോക്താവിനെ കണ്ടെത്തിയില്ല":
            message.reply_text("എനിക്ക് ഈ ഉപയോക്താവിനെ കണ്ടെത്താൻ കഴിയില്ല.")
            return ""
        else:
            raise

    if sql.is_user_blacklisted(user_id):

        sql.unblacklist_user(user_id)
        message.reply_text("*ഉപയോക്താവിനെ ശ്രദ്ധിക്കുന്നു*")
        log_message = (
            f"#UNBLACKLIST\n"
            f"<b>അഡ്മിൻ:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>യൂസർ:</b> {mention_html(target_user.id, html.escape(target_user.first_name))}"
        )

        return log_message

    else:
        message.reply_text("ഞാൻ അവരെ അവഗണിക്കുന്നില്ല!")
        return ""


@run_async
@dev_plus
def bl_users(update: Update, context: CallbackContext):
    users = []
    bot = context.bot
    for each_user in sql.BLACKLIST_USERS:
        user = bot.get_chat(each_user)
        reason = sql.get_reason(each_user)

        if reason:
            users.append(
                f"• {mention_html(user.id, html.escape(user.first_name))} :- {reason}"
            )
        else:
            users.append(f"• {mention_html(user.id, html.escape(user.first_name))}")

    message = "<b>ബ്ലാക്ക്ലിസ്റ്ററ്റിൽ ഉൾപ്പെട്ടവർ</b>\n"
    if not users:
        message += "ഇതുവരെ ആരും അവഗണിക്കുന്നില്ല"
    else:
        message += "\n".join(users)

    update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)


def __user_info__(user_id):
    is_blacklisted = sql.is_user_blacklisted(user_id)

    text = "Blacklisted: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in DRAGONS + TIGERS + WOLVES:
        return ""
    if is_blacklisted:
        text = text.format("Yes")
        reason = sql.get_reason(user_id)
        if reason:
            text += f"\n കാരണം: <code>{reason}</code>"
    else:
        text = text.format("No")

    return text


BL_HANDLER = CommandHandler("ignore", bl_user)
UNBL_HANDLER = CommandHandler("notice", unbl_user)
BLUSERS_HANDLER = CommandHandler("ignoredlist", bl_users)

dispatcher.add_handler(BL_HANDLER)
dispatcher.add_handler(UNBL_HANDLER)
dispatcher.add_handler(BLUSERS_HANDLER)

__mod_name__ = "Blacklisting Users"
__handlers__ = [BL_HANDLER, UNBL_HANDLER, BLUSERS_HANDLER]
