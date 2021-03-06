import json, time, os
from io import BytesIO

from telegram import ParseMode, Message
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async

import MissHannahRobot.modules.sql.notes_sql as sql
from MissHannahRobot import dispatcher, LOGGER, OWNER_ID, JOIN_LOGGER, SUPPORT_CHAT
from MissHannahRobot.__main__ import DATA_IMPORT
from MissHannahRobot.modules.helpo_hannah.chat_status import user_admin
from MissHannahRobot.modules.helpo_hannah.alternate import typing_action

# from MissHannahRobot.modules.rules import get_rules
import MissHannahRobot.modules.sql.rules_sql as rulessql

# from MissHannahRobot.modules.sql import warns_sql as warnssql
import MissHannahRobot.modules.sql.blacklist_sql as blacklistsql
from MissHannahRobot.modules.sql import disable_sql as disabledsql

# from MissHannahRobot.modules.sql import cust_filters_sql as filtersql
# import MissHannahRobot.modules.sql.welcome_sql as welcsql
import MissHannahRobot.modules.sql.locks_sql as locksql
from MissHannahRobot.modules.connection import connected


@run_async
@user_admin
@typing_action
def import_data(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    # TODO: allow uploading doc with command, not just as reply
    # only work with a doc

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            update.effective_message.reply_text("ഈ കമാൻഡ് ഗ്രൂപ്പിൽ മാത്രമേ വർക്ക്‌ ചെയ്യുകയുള്ളൂ..")
            return ""

        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if msg.reply_to_message and msg.reply_to_message.document:
        try:
            file_info = context.bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            msg.reply_text(
                "ഫയൽ വീണ്ടും ഡൌൺലോഡ് ചെയ്ത് അപ്‌ലോഡ് ചെയ്യാൻ ശ്രമിക്കുക, ഇത് എനിക്ക് തകർന്നതായി തോന്നുന്നു!"
            )
            return

        with BytesIO() as file:
            file_info.download(out=file)
            file.seek(0)
            data = json.load(file)

        # only import one group
        if len(data) > 1 and str(chat.id) not in data:
            msg.reply_text(
                "ഈ ഫയലിൽ ഒന്നിൽ കൂടുതൽ ഗ്രൂപ്പുകളുണ്ട്, ചാറ്റ് ഐഡി സമാനമല്ല!  ഞാൻ എങ്ങനെ import ചെയ്യും??"
            )
            return

        # Check if backup is this chat
        try:
            if data.get(str(chat.id)) is None:
                if conn:
                    text = "ഈ ബാക്കപ്പ് മറ്റൊരു ഗ്രൂപ്പിന്റെയാണ്.. *{}*".format(
                        chat_name
                    )
                else:
                    text = "ഈ ബാക്കപ്പ് മറ്റൊരു ഗ്രൂപ്പിന്റെയാണ്.."
                return msg.reply_text(text, parse_mode="markdown")
        except Exception:
            return msg.reply_text("Importing ചെയ്യുന്നതിൽ പിശക് സംഭവിച്ചു..!")
        # Check if backup is from self
        try:
            if str(context.bot.id) != str(data[str(chat.id)]["bot"]):
                return msg.reply_text(
                    "നിർദ്ദേശിച്ചിട്ടില്ലാത്ത മറ്റൊരു ബോട്ടിൽ നിന്നുള്ള ബാക്കപ്പ് പ്രശ്‌നമുണ്ടാക്കാം, പ്രമാണങ്ങൾ, ഫോട്ടോകൾ, വീഡിയോകൾ, ഓഡിയോകൾ, റെക്കോർഡുകൾ പ്രവർത്തിക്കാനിടയില്ല."
                )
        except Exception:
            pass
        # Select data source
        if str(chat.id) in data:
            data = data[str(chat.id)]["hashes"]
        else:
            data = data[list(data.keys())[0]]["hashes"]

        try:
            for mod in DATA_IMPORT:
                mod.__import_data__(str(chat.id), data)
        except Exception:
            msg.reply_text(
                f"നിങ്ങളുടെ ഡാറ്റ വീണ്ടെടുക്കുമ്പോൾ ഒരു പിശക് സംഭവിച്ചു.  പ്രക്രിയ പരാജയപ്പെട്ടു.  നിങ്ങൾ‌ക്ക് ഇതിൽ‌ ഒരു പ്രശ്‌നം നേരിടുന്നുണ്ടെങ്കിൽ‌, ദയവായി സപ്പോർട്ട് ഗ്രൂപ്പുമായി ബന്ധപ്പെടുക.. @{SUPPORT_CHAT}"
            )

            LOGGER.exception(
                "Imprt for the chat %s with the name %s failed.",
                str(chat.id),
                str(chat.title),
            )
            return

        # TODO: some of that link logic
        # NOTE: consider default permissions stuff?
        if conn:

            text = "ബാക്കപ്പ് പൂർണ്ണമായും പുനസ്ഥാപിച്ചു *{}*.".format(chat_name)
        else:
            text = "ബാക്കപ്പ് പൂർണ്ണമായും പുനസ്ഥാപിച്ചു"
        msg.reply_text(text, parse_mode="markdown")


@run_async
@user_admin
def export_data(update, context):
    chat_data = context.chat_data
    msg = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    current_chat_id = update.effective_chat.id
    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        # chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            update.effective_message.reply_text("ഈ കമാൻഡ് ഗ്രൂപ്പിൽ മാത്രമേ വർക്ക്‌ ചെയ്യുകയുള്ളൂ..")
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        # chat_name = update.effective_message.chat.title

    jam = time.time()
    new_jam = jam + 10800
    checkchat = get_chat(chat_id, chat_data)
    if checkchat.get("status"):
        if jam <= int(checkchat.get("value")):
            timeformatt = time.strftime(
                "%H:%M:%S %d/%m/%Y", time.localtime(checkchat.get("value"))
            )
            update.effective_message.reply_text(
                "നിങ്ങൾക്ക് ഒരു ദിവസത്തിൽ ഒരിക്കൽ മാത്രമേ ബാക്കപ്പ് ചെയ്യാൻ കഴിയൂ!\nനിങ്ങൾക്ക് വീണ്ടും ബാക്കപ്പ് ചെയ്യാൻ കഴിയും `{}`".format(
                    timeformatt
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        else:
            if user.id != OWNER_ID:
                put_chat(chat_id, new_jam, chat_data)
    else:
        if user.id != OWNER_ID:
            put_chat(chat_id, new_jam, chat_data)

    note_list = sql.get_all_chat_notes(chat_id)
    backup = {}
    # button = ""
    buttonlist = []
    namacat = ""
    isicat = ""
    rules = ""
    count = 0
    countbtn = 0
    # Notes
    for note in note_list:
        count += 1
        # getnote = sql.get_note(chat_id, note.name)
        namacat += "{}<###splitter###>".format(note.name)
        if note.msgtype == 1:
            tombol = sql.get_buttons(chat_id, note.name)
            # keyb = []
            for btn in tombol:
                countbtn += 1
                if btn.same_line:
                    buttonlist.append(
                        ("{}".format(btn.name), "{}".format(btn.url), True)
                    )
                else:
                    buttonlist.append(
                        ("{}".format(btn.name), "{}".format(btn.url), False)
                    )
            isicat += "###button###: {}<###button###>{}<###splitter###>".format(
                note.value, str(buttonlist)
            )
            buttonlist.clear()
        elif note.msgtype == 2:
            isicat += "###sticker###:{}<###splitter###>".format(note.file)
        elif note.msgtype == 3:
            isicat += "###file###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        elif note.msgtype == 4:
            isicat += "###photo###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        elif note.msgtype == 5:
            isicat += "###audio###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        elif note.msgtype == 6:
            isicat += "###voice###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        elif note.msgtype == 7:
            isicat += "###video###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        elif note.msgtype == 8:
            isicat += "###video_note###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        else:
            isicat += "{}<###splitter###>".format(note.value)
    notes = {
        "#{}".format(namacat.split("<###splitter###>")[x]): "{}".format(
            isicat.split("<###splitter###>")[x]
        )
        for x in range(count)
    }
    # Rules
    rules = rulessql.get_rules(chat_id)
    # Blacklist
    bl = list(blacklistsql.get_chat_blacklist(chat_id))
    # Disabled command
    disabledcmd = list(disabledsql.get_all_disabled(chat_id))
    # Filters (TODO)
    """
	all_filters = list(filtersql.get_chat_triggers(chat_id))
	export_filters = {}
	for filters in all_filters:
		filt = filtersql.get_filter(chat_id, filters)
		# print(vars(filt))
		if filt.is_sticker:
			tipefilt = "sticker"
		elif filt.is_document:
			tipefilt = "doc"
		elif filt.is_image:
			tipefilt = "img"
		elif filt.is_audio:
			tipefilt = "audio"
		elif filt.is_voice:
			tipefilt = "voice"
		elif filt.is_video:
			tipefilt = "video"
		elif filt.has_buttons:
			tipefilt = "button"
			buttons = filtersql.get_buttons(chat.id, filt.keyword)
			print(vars(buttons))
		elif filt.has_markdown:
			tipefilt = "text"
		if tipefilt == "button":
			content = "{}#=#{}|btn|{}".format(tipefilt, filt.reply, buttons)
		else:
			content = "{}#=#{}".format(tipefilt, filt.reply)
		print(content)
		export_filters[filters] = content
	print(export_filters)
	"""
    # Welcome (TODO)
    # welc = welcsql.get_welc_pref(chat_id)
    # Locked
    curr_locks = locksql.get_locks(chat_id)
    curr_restr = locksql.get_restr(chat_id)

    if curr_locks:
        locked_lock = {
            "sticker": curr_locks.sticker,
            "audio": curr_locks.audio,
            "voice": curr_locks.voice,
            "document": curr_locks.document,
            "video": curr_locks.video,
            "contact": curr_locks.contact,
            "photo": curr_locks.photo,
            "gif": curr_locks.gif,
            "url": curr_locks.url,
            "bots": curr_locks.bots,
            "forward": curr_locks.forward,
            "game": curr_locks.game,
            "location": curr_locks.location,
            "rtl": curr_locks.rtl,
        }
    else:
        locked_lock = {}

    if curr_restr:
        locked_restr = {
            "messages": curr_restr.messages,
            "media": curr_restr.media,
            "other": curr_restr.other,
            "previews": curr_restr.preview,
            "all": all(
                [
                    curr_restr.messages,
                    curr_restr.media,
                    curr_restr.other,
                    curr_restr.preview,
                ]
            ),
        }
    else:
        locked_restr = {}

    locks = {"locks": locked_lock, "restrict": locked_restr}
    # Warns (TODO)
    # warns = warnssql.get_warns(chat_id)
    # Backing up
    backup[chat_id] = {
        "bot": context.bot.id,
        "hashes": {
            "info": {"rules": rules},
            "extra": notes,
            "blacklist": bl,
            "disabled": disabledcmd,
            "locks": locks,
        },
    }
    baccinfo = json.dumps(backup, indent=4)
    with open("MissHannahRobot{}.backup".format(chat_id), "w") as f:
        f.write(str(baccinfo))
    context.bot.sendChatAction(current_chat_id, "upload_document")
    tgl = time.strftime("%H:%M:%S - %d/%m/%Y", time.localtime(time.time()))
    try:
        context.bot.sendMessage(
            JOIN_LOGGER,
            "*Successfully imported backup:*\nChat: `{}`\nChat ID: `{}`\nOn: `{}`".format(
                chat.title, chat_id, tgl
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except BadRequest:
        pass
    context.bot.sendDocument(
        current_chat_id,
        document=open("MissHannahRobot{}.backup".format(chat_id), "rb"),
        caption="*വിജയകരമായി ബാക്കപ്പ് ഫയൽ എക്സ്പോർട്ട് ചെയ്തു.:*\n🔰ഗ്രൂപ്പ്‌: `{}`\n☑️ഐഡി: `{}`\n⏲️സമയം: `{}`\n\n⚠️അറിയിപ്പ്: This `MissHannahRobot-Backup` was specially made for notes.".format(
            chat.title, chat_id, tgl
        ),
        timeout=360,
        reply_to_message_id=msg.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )
    os.remove("MissHannahRobot{}.backup".format(chat_id))  # Cleaning file


# Temporary data
def put_chat(chat_id, value, chat_data):
    # print(chat_data)
    status = value is not False
    chat_data[chat_id] = {"backups": {"status": status, "value": value}}


def get_chat(chat_id, chat_data):
    # print(chat_data)
    try:
        return chat_data[chat_id]["backups"]
    except KeyError:
        return {"status": False, "value": False}


__mod_name__ = "Backups"

__help__ = """
*Only for group owner:*

 • /import: Reply to the backup file for the butler / emilia group to import as much as possible, making transfers very easy! \
 Note that files / photos cannot be imported due to telegram restrictions.

 • /export: Export group data, which will be exported are: rules, notes (documents, images, music, video, audio, voice, text, text buttons) \

"""

IMPORT_HANDLER = CommandHandler("import", import_data)
EXPORT_HANDLER = CommandHandler("export", export_data, pass_chat_data=True)

dispatcher.add_handler(IMPORT_HANDLER)
dispatcher.add_handler(EXPORT_HANDLER)
