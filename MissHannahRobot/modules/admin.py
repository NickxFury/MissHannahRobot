import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from MissHannahRobot import DRAGONS, dispatcher
from MissHannahRobot.modules.disable import DisableAbleCommandHandler
from MissHannahRobot.modules.helpo_hannah.chat_status import (
    bot_admin,
    can_pin,
    can_promote,
    connection_status,
    user_admin,
    ADMIN_CACHE,
)

from MissHannahRobot.modules.helpo_hannah.extraction import (
    extract_user,
    extract_user_and_text,
)
from MissHannahRobot.modules.log_channel import loggable
from MissHannahRobot.modules.helpo_hannah.alternate import send_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and user.id not in DRAGONS
    ):
        message.reply_text("🙄സോറി.. നിങ്ങൾക്കതിനുള്ള അധികാരം ഇല്ല!")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            f"⚠️പ്രൊമോട്ട് ചെയ്യേണ്ട ആളുടെ മെസ്സേജിന് മറുപടിയായി കമാൻഡ് നൽകുക. അല്ലെങ്കിൽ `/promote <username/id>` നൽകുക.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "administrator" or user_member.status == "creator":
        message.reply_text("🙄അഡ്മിൻ ആണല്ലോ?")
        return

    if user_id == bot.id:
        message.reply_text("എനിക്ക് എന്നെത്തന്നെ പ്രൊമോട്ട് ചെയ്യാൻ കഴിയില്ല! 😔 എനിക്കായി ഇത് ചെയ്യാൻ ഒരു അഡ്മിനോട്‌ പറയുക 🚶‍♀️.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            # can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("ഗ്രൂപ്പിൽ ഇല്ലാത്ത ഒരാളിനെ ഞാൻ എങ്ങനെ അഡ്മിൻ ആക്കും.")
        else:
            message.reply_text("🙄 എന്തെരോ ഒരു തകരാറ് പോല.")
        return

    bot.sendMessage(
        chat.id,
        f"അഡ്മിൻ ആക്കിയിട്ടുണ്ട് 🙇‍♀️ <b>{user_member.user.first_name or user_id}</b>!",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "നിങ്ങൾ ഒരു ഉപയോക്താവിനെ പരാമർശിക്കുന്നതായി തോന്നുന്നില്ല അല്ലെങ്കിൽ യൂസർ ഐഡി തെറ്റാണ് .."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "creator":
        message.reply_text("ഇദ്ദേഹം ആണ് ഈ ഗ്രൂപ്പിന്റെ മൊയലാളി 😁 അയാളെ അഡ്മിൻ സ്ഥാനത്ത് നിന്ന് മാറ്റാൻ എനിക്ക് കഴിയില്ല.. ഓടിക്കോ ഹംകേ..🤭?")
        return

    if not user_member.status == "administrator":
        message.reply_text("ഞാൻ പ്രൊമോട്ട് ചെയ്യാത്ത ഒരാളെ ഡിമോട്ട് ചെയ്യാൻ എനിക്ക് മനസ്സില്ല 😁")
        return

    if user_id == bot.id:
        message.reply_text("എനിക്ക് എന്നെത്തന്നെ അഡ്മിൻ സ്ഥാനത്ത് നിന്ന് മാറ്റാൻ കഴിയില്ല! എനിക്കായി ഇത് ചെയ്യാൻ ഒരു അഡ്മിന്റെ സഹായം തേടുക..")
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
        )

        bot.sendMessage(
            chat.id,
            f"അഡ്മിൻ സ്ഥാനം ഒഴിവാക്കി 🌚 <b>{user_member.user.first_name or user_id}</b>!",
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#DEMOTED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        message.reply_text(
            "അഡ്മിൻ സ്ഥാനം മാറ്റുവാൻ കഴിയില്ല..ഒന്നുകിൽ ഞാൻ അഡ്മിൻ അല്ല..അല്ലെങ്കിൽ അദ്ദേഹത്തെ അഡ്മിൻ ആക്കിയത് മറ്റാരോ ആണ്.."
            " ആയതിനാൽ എനിക്ക് ഒന്നും ചെയ്യാൻ കഴിയില്ല..!"
        )
        return


@run_async
@user_admin
def refresh_admin(update, _):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    update.effective_message.reply_text("അഡ്മിൻ ലിസ്റ്റ് അപ്ഡേറ്റ് ചെയ്തു☑️")


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text(
            "നിങ്ങൾ ഒരു ഉപയോക്താവിനെ പരാമർശിക്കുന്നതായി തോന്നുന്നില്ല അല്ലെങ്കിൽ യൂസർ ഐഡി തെറ്റാണ് .."
        )
        return

    if user_member.status == "creator":
        message.reply_text(
            "ഗ്രൂപ്പ്‌ മുതലാളിയുടെ അഡ്മിൻ നാമം മാറ്റാൻ എനിക്ക് കഴിയില്ല?"
        )
        return

    if user_member.status != "administrator":
        message.reply_text(
            "അഡ്മിൻ അല്ലാത്ത ഒരാളിന് എങ്ങനെ അഡ്മിൻ നാമം കൊടുക്കും.. പൊട്ടൻ ആണോ നീ?"
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "എനിക്ക് എന്റെ അഡ്മിൻ നാമം മാറ്റാൻ കഴിയില്ല..."
        )
        return

    if not title:
        message.reply_text("എന്ത് പേര് ആണ് കൊടുക്കേണ്ടത് മിസ്റ്റർ!")
        return

    if len(title) > 16:
        message.reply_text(
            "ഇത്രയും ദീർഘമുള്ള പേര് സെറ്റ് ചെയ്യാൻ കഴിയില്ല."
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text("ഞാൻ പ്രൊമോട്ട് ചെയ്തു അഡ്മിൻ ആക്കിയവരുടെ പേര് മാത്രമേ മാറ്റം വരുത്തുകയുള്ളു..")
        return

    bot.sendMessage(
        chat.id,
        f"അഡ്മിൻ നാമം വിജയകരമായി സെറ്റ് ചെയ്തു.. <code>{user_member.user.first_name or user_id}</code> "
        f"to <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"
    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (
            args[0].lower() == "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#📌പിൻ ചെയ്തു\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#നിലവിൽ പിൻ ചെയ്തിരുന്നു മെസ്സേജ് ഒഴിവാക്കി\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
    )

    return log_message


@run_async
@bot_admin
@user_admin
@connection_status
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(
                "ഗ്രൂപ്പ്‌ ലിങ്ക് എടുക്കുന്നതിനുള്ള പെർമിഷൻ എനിക്കില്ല..!"
            )
    else:
        update.effective_message.reply_text(
            "സൂപ്പർ ഗ്രൂപ്പുകളുടെയോ അല്ലെങ്കിൽ ചാനലുകളുടെയോ ലിങ്ക് മാത്രമേ എനിക്ക് തരുവാൻ സാധിക്കുകയുള്ളു.."
        )


@run_async
@connection_status
def adminlist(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args
    bot = context.bot

    if update.effective_message.chat.type == "private":
        send_message(update.effective_message, "ഈ കമാൻഡ് ഗ്രൂപ്പിൽ മാത്രമേ വർക്ക്‌ ആവുകയുള്ളു...")
        return

    chat = update.effective_chat
    chat_id = update.effective_chat.id
    chat_name = update.effective_message.chat.title

    try:
        msg = update.effective_message.reply_text(
            "🔎 ഗ്രൂപ്പ്‌ അഡ്മിൻസിനെ സെർച് ചെയ്യുന്നു..", parse_mode=ParseMode.HTML
        )
    except BadRequest:
        msg = update.effective_message.reply_text(
            "🔎 ഗ്രൂപ്പ്‌ അഡ്മിൻസിനെ സെർച് ചെയ്യുന്നു..", quote=False, parse_mode=ParseMode.HTML
        )

    administrators = bot.getChatAdministrators(chat_id)
    text = "😾<b>അധികാരികൾ</b>😾\n<b>{}</b>:".format(html.escape(update.effective_chat.title))

    bot_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Deleted Account"
        else:
            name = "{}".format(
                mention_html(
                    user.id, html.escape(user.first_name + " " + (user.last_name or ""))
                )
            )

        if user.is_bot:
            bot_admin_list.append(name)
            administrators.remove(admin)
            continue

        # if user.username:
        #    name = escape_markdown("@" + user.username)
        if status == "creator":
            text += "\n👑ഗ്രൂപ്പ്‌ മുതലാളി :"
            text += "\n<code> • </code>{}\n".format(name)

            if custom_title:
                text += f"<code> ┗━ {html.escape(custom_title)}</code>\n"

    text += "\n🔱 അധികാരികൾ:"

    custom_admin_list = {}
    normal_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Deleted Account"
        else:
            name = "{}".format(
                mention_html(
                    user.id, html.escape(user.first_name + " " + (user.last_name or ""))
                )
            )
        # if user.username:
        #    name = escape_markdown("@" + user.username)
        if status == "administrator":
            if custom_title:
                try:
                    custom_admin_list[custom_title].append(name)
                except KeyError:
                    custom_admin_list.update({custom_title: [name]})
            else:
                normal_admin_list.append(name)

    for admin in normal_admin_list:
        text += "\n<code> • </code>{}".format(admin)

    for admin_group in custom_admin_list.copy():
        if len(custom_admin_list[admin_group]) == 1:
            text += "\n<code> • </code>{} | <code>{}</code>".format(
                custom_admin_list[admin_group][0], html.escape(admin_group)
            )
            custom_admin_list.pop(admin_group)

    text += "\n"
    for admin_group, value in custom_admin_list.items():
        text += "\n🚨 <code>{}</code>".format(admin_group)
        for admin in value:
            text += "\n<code> • </code>{}".format(admin)
        text += "\n"

    text += "\n🤖 ബോട്ടുകൾ:"
    for each_bot in bot_admin_list:
        text += "\n<code> • </code>{}".format(each_bot)

    try:
        msg.edit_text(text, parse_mode=ParseMode.HTML)
    except BadRequest:  # if original message is deleted
        return


__help__ = """
 • `/admins`*:* list of admins in the chat

*Admins only:*
 • `/pin`*:* silently pins the message replied to - add `'loud'` or `'notify'` to give notifs to users
 • `/unpin`*:* unpins the currently pinned message
 • `/invitelink`*:* gets invitelink
 • `/promote`*:* promotes the user replied to
 • `/demote`*:* demotes the user replied to
 • `/title <title here>`*:* sets a custom title for an admin that the bot promoted
 • `/admincache`*:* force refresh the admins list
"""

ADMINLIST_HANDLER = DisableAbleCommandHandler("admins", adminlist)

PIN_HANDLER = CommandHandler("pin", pin, filters=Filters.group)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.group)

INVITE_HANDLER = DisableAbleCommandHandler("invitelink", invite)

PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote)

SET_TITLE_HANDLER = CommandHandler("title", set_title)
ADMIN_REFRESH_HANDLER = CommandHandler(
    "admincache", refresh_admin, filters=Filters.group
)

dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(ADMIN_REFRESH_HANDLER)

__mod_name__ = "Admin"
__command_list__ = [
    "adminlist",
    "admins",
    "invitelink",
    "promote",
    "demote",
    "admincache",
]
__handlers__ = [
    ADMINLIST_HANDLER,
    PIN_HANDLER,
    UNPIN_HANDLER,
    INVITE_HANDLER,
    PROMOTE_HANDLER,
    DEMOTE_HANDLER,
    SET_TITLE_HANDLER,
    ADMIN_REFRESH_HANDLER,
]
