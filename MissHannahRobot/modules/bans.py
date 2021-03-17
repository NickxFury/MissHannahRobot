import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from MissHannahRobot import (
    DEV_USERS,
    LOGGER,
    OWNER_ID,
    DRAGONS,
    DEMONS,
    TIGERS,
    WOLVES,
    dispatcher,
)
from MissHannahRobot.modules.disable import DisableAbleCommandHandler
from MissHannahRobot.modules.helpo_hannah.chat_status import (
    bot_admin,
    can_restrict,
    connection_status,
    is_user_admin,
    is_user_ban_protected,
    is_user_in_chat,
    user_admin,
    user_can_ban,
    can_delete,
)
from MissHannahRobot.modules.helpo_hannah.extraction import extract_user_and_text
from MissHannahRobot.modules.helpo_hannah.string_handling import extract_time
from MissHannahRobot.modules.log_channel import gloggable, loggable


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot = context.bot
    args = context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ബാൻ ചെയ്യാൻ പറഞ്ഞ ആളെ എനിക്ക് ഒരു സംശയം😜. ആരെയാണ് ബാൻ ചെയ്യേണ്ടത് മിസ്റ്റർ 🙄")
        return log_message
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "ഇയാളെ കണ്ടെത്താൻ പറ്റുന്നില്ല🥺.":
            raise
        message.reply_text("ഇയാളെ ഞാൻ ഇതുവരെ കണ്ടിട്ടില്ല അതു എന്നക്ക് ബാൻ ചെയ്യാൻ കഴിയില്ല🤪.")
        return log_message
    if user_id == bot.id:
        message.reply_text("ഭാ... ഞാൻ എന്നെ തന്നെ ബാൻ ചെയ്യണം എന്നോ😏")
        return log_message

    if is_user_ban_protected(chat, user_id, member) and user not in DEV_USERS:
        if user_id == OWNER_ID:
            message.reply_text("ഇദ്ദേഹം എൻ്റെ മുതലാളി ആണ്. അതുകൊണ്ട് എന്നിക്ക് ബാൻ ചെയ്യാൻ കഴിയില്ല.")
        elif user_id in DEV_USERS:
            message.reply_text(" ഇയാളെ ബാൻ ആക്കാൻ എന്നക്ക് കഴിയില്ല.")
        elif user_id in DRAGONS:
            message.reply_text(
                " ആഹാ! ഇയാളെ ബാൻ ആക്കണം അല്ലെ? ഒരിക്കിലും നടക്കാത്ത മനോഹരമായ സ്വപനം."
            )
        elif user_id in DEMONS:
            message.reply_text(
                "വിട്ടോ വിട്ടോ ഇതൊന്നും നടക്കില്ല."
            )
        elif user_id in TIGERS:
            message.reply_text(
                "നഹി! നഹി എന്ന് പറഞ്ഞാൽ നഹി ഹേ പോടോ ഹേ!."
            )
        elif user_id in WOLVES:
            message.reply_text("ഇത് എൻ്റെ അടുത്ത സുഹൃത്ത് ആണ്. ഇയാളെ ബാൻ ചെയ്യാൻ കഴിയില്ല.")
        else:
            message.reply_text("ഇദ്ദേഹം എൻ്റെ ഏറ്റവു അടുത്ത നല്ല സൂഹൃത്ത് ആണ്! ഇയാളെ ബാൻ ചെയ്യാൻ എന്നിക്ക് ഒരികില്ലും സാധിക്കില്ല.")
        return log_message
    if message.text.startswith("/s"):
        silent = True
        if not can_delete(chat, context.bot.id):
            return ""
    else:
        silent = False
    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#{'S' if silent else ''}BANNED\n"
        f"<b>അഡ്മിൻ:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>യൂസർ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += "\n<b>കാരണം:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)

        if silent:
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.delete()
            return log

        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        reply = (
            f"<code>⚠️</code><b> പുതിയ ബാൻ</b>\n"
            f"<code> </code><b> 👤User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            reply += f"\n<code> </code><b>•  കാരണം:</b> \n{html.escape(reason)}"
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML, quote=False)
        return log

    except BadRequest as excp:
        if excp.message == "റിപ്ലേ സന്ദേശം കണ്ടെത്താൻ കഴിയുന്നില്ല":
            # Do not reply
            if silent:
                return log
            message.reply_text("ബാൻ ചെയ്തു!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text(" ഇത്... ഒരു വാക്കാണ് എന്ന് തോന്നുന്നില്ല...")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("നിങ്ങൾ പറഞ്ഞ ആളെ കുറിച്ച് എന്നിക്ക് ഒരു സംശയം.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "നിങ്ങൾ പറഞ്ഞആളെ കണ്ടെത്താൻ കഴിയുന്നില്ല":
            raise
        message.reply_text("നിങ്ങൾ പറഞ്ഞ ആളെ ഞാൻ ഇതുവരെ കണ്ടിട്ടില്ല.")
        return log_message
    if user_id == bot.id:
        message.reply_text("ഭ... നിനക്ക് ഭ്രാന്ത് ആണോ? ഞാൻ എന്നെ തന്നെ ബാൻ ചെയ്യണം എന്നോ?")
        return log_message

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("എന്തോ? എങ്ങനെ?.")
        return log_message

    if not reason:
        message.reply_text("നിങ്ങൾ വ്യക്കമായ ഒരു സമയം പറഞ്ഞാലെ നിങ്ങൾ പറഞ്ഞത് പോലെ എന്നിക്ക് ചെയ്യാൻ കഴിയു!")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#TEMP BANNED\n"
        f"<b>അഡ്മിൻ:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>യൂസർ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
        f"<b>സമയം:</b> {time_val}"
    )
    if reason:
        log += "\n<b>കാരണം:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        bot.sendMessage(
            chat.id,
            f"Banned! User {mention_html(member.user.id, html.escape(member.user.first_name))} "
            f"will be banned for {time_val}.",
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                f"ബാൻ ചെയ്തു! ഇയാൾ {time_val} വരെ ഇവിടെ ബാൻ ആണ്.", quote=False
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Well damn, I can't ban that user.")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def punch(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("എന്നിക്ക് ഇയാളെ ഒരു സംശയം.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "നിങ്ങൾ പറഞ്ഞ ആളെ കണ്ടെത്താൻ കഴിയുന്നില്ല":
            raise

        message.reply_text("നിങ്ങൾ പറഞ്ഞ ആളെ ഞാൻ ഇതുവരെ കണ്ടിട്ടില്ല.")
        return log_message
    if user_id == bot.id:
        message.reply_text("ഹ! ശരി നിങ്ങൾ പറഞ്ഞത് ഞാൻ ചെയ്യാം..")
        return log_message

    if is_user_ban_protected(chat, user_id):
        message.reply_text("ഇദ്ദേഹത്തെ കിക്ക് ചെയ്യാൻ എന്നിക്ക് അതിയായ ആഗ്രഹം ഉണ്ട്....")
        return log_message

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        bot.sendMessage(
            chat.id,
            f"One Punched! {mention_html(member.user.id, html.escape(member.user.first_name))}.",
            parse_mode=ParseMode.HTML,
        )
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            f"<b>അഡ്മിൻ:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>യൂസർ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            log += f"\n<b>Reason:</b> {reason}"

        return log

    else:
        message.reply_text("കോപ്പ് ഇയ്യാള കിക്ക് ചെയ്യാൻ എന്നിക്ക് സാധിക്കൂല്ല.")

    return log_message


@run_async
@bot_admin
@can_restrict
def punchme(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("നിങ്ങൾ ഇവിടെ അഡ്മിൻ ആണ്.. എന്നിക്ക് അത് കഴിയില്ല..")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("*നീ പുറത്ത് പോ.*")
    else:
        update.effective_message.reply_text("എന്നെകൊണ്ട് ഒന്നും വയ്യ!' :/")


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def unban(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("നിങ്ങൾ പറഞ്ഞ ആളെ എന്നിക്ക് സംശയം ഉണ്ട്.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "നിങ്ങൾ പറഞ്ഞ ആളെ കണ്ടെത്താൻ കഴിയുന്നില്ല":
            raise
        message.reply_text("ഞാൻ നിങ്ങൾ പറഞ്ഞ ആളെ ഇതുവരെ കണ്ടിട്ടില്ല.")
        return log_message
    if user_id == bot.id:
        message.reply_text("നീ എന്ത് തേങ്ങയാ ഈ പറയുന്നത്")
        return log_message

    if is_user_in_chat(chat, user_id):
        message.reply_text("നിങ്ങൾ പറഞ്ഞ ആൾ ഇവിടെ ഉണ്ടല്ലേ?")
        return log_message

    chat.unban_member(user_id)
    message.reply_text("ശരി. ഇയാൾക്ക് വീണ്ടും ഇവിടെ ജോയിൻ ചെയ്യാം!")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>അഡ്മിൻ:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>യൂസർ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += f"\n<b>കാരണം:</b> {reason}"

    return log


@run_async
@connection_status
@bot_admin
@can_restrict
@gloggable
def selfunban(context: CallbackContext, update: Update) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in DRAGONS or user.id not in TIGERS:
        return

    try:
        chat_id = int(args[0])
    except:
        message.reply_text("ശരിയായ ചാറ്റ് ഐഡി തരു.")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "നിങ്ങൾ പറഞ്ഞ ആളെ കണ്ടെത്താൻ കഴിയുന്നില്ല":
            message.reply_text("നിങ്ങൾ പറഞ്ഞ ആളെ ഞാൻ ഇതുവരെ കണ്ടിട്ടില്ല.")
            return
        else:
            raise

    if is_user_in_chat(chat, user.id):
        message.reply_text("ഇദ്ദേഹം ഈ ഗ്രൂപ്പിൽ ഇല്ലെ??")
        return

    chat.unban_member(user.id)
    message.reply_text("ശരി നിങ്ങളെ ഞാൻ അൺ ബാൻ ചെയ്യാം.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>യൂസർ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )

    return log


__help__ = """
 • `/punchme`*:* punchs the user who issued the command

*Admins only:*
 • `/ban <userhandle>`*:* bans a user. (via handle, or reply)
 • `/sban <userhandle>`*:* Silently ban a user. Deletes command, Replied message and doesn't reply. (via handle, or reply)
 • `/tban <userhandle> x(m/h/d)`*:* bans a user for `x` time. (via handle, or reply). `m` = `minutes`, `h` = `hours`, `d` = `days`.
 • `/unban <userhandle>`*:* unbans a user. (via handle, or reply)
 • `/punch <userhandle>`*:* Punches a user out of the group, (via handle, or reply)
"""

BAN_HANDLER = CommandHandler(["ban", "sban"], ban)
TEMPBAN_HANDLER = CommandHandler(["tban"], temp_ban)
PUNCH_HANDLER = CommandHandler("punch", punch)
UNBAN_HANDLER = CommandHandler("unban", unban)
ROAR_HANDLER = CommandHandler("roar", selfunban)
PUNCHME_HANDLER = DisableAbleCommandHandler("punchme", punchme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(PUNCH_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(ROAR_HANDLER)
dispatcher.add_handler(PUNCHME_HANDLER)

__mod_name__ = "Bans"
__handlers__ = [
    BAN_HANDLER,
    TEMPBAN_HANDLER,
    PUNCH_HANDLER,
    UNBAN_HANDLER,
    ROAR_HANDLER,
    PUNCHME_HANDLER,
]
