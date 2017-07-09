import itertools
from os.path import expanduser
import sqlite3
import nltk
import operator
from pprint import pprint, pformat
from collections import Counter
from datetime import datetime
from utils import tokens, cleaned, OSX_EPOCH
# import spacy
from addressbook import AddressBook



# List of symbols we don't want to check

# Represents a user that iMessages can be exchanged with.
#
# Each user has...
#  - an `id` property that uniquely identifies him or her in the Messages database
#  - a `phone_or_email` property that is either the user's phone number or iMessage-enabled email address
class Recipient:
    def __init__(self, phone_or_email, handle_id):
        self.phone_or_email = self.clean_number(str(phone_or_email))
        self.handle_id = handle_id


    def __repr__(self):
        return "Phone or email: " + self.phone_or_email + " ID: " + str(self.handle_id)

    @staticmethod
    def clean_number(phone):
        return phone.replace('(', '').replace(' ', '').replace('-', '').replace(')', '')

# Represents an iMessage message.
#
# Each message has:
#  - a `text` property that holds the text contents of the message
#  - a `date` property that holds the delivery date of the message
class Message:
    def __init__(self, text, date, id, is_sent):
        self.text = text
        self.date = date
        self.id = id
        self.is_sent = is_sent

    def __repr__(self):
        return "Date: " + datetime.strftime(self.date, "%H:%M:%S") + "Text: " + self.text +\
                              "\n ID: " + str(self.id) + " IS_Sent: " + str(self.is_sent)



# encapsulates a conversation between you and the recipient
class TextConversation:
    def __init__(self, recipient, messages):
        self.recipient = recipient
        self.messages = messages

    # returns list of sent messages
    def sent_messages(self):
        return [m.text for m in self.messages if bool(m.is_sent)]

    # returns list of received messages
    def received_messages(self):
        return [m.text for m in self.messages if not bool(m.is_sent)]

    # helper
    def add_message(self, m):
        self.messages.append(m)


    # returns a dict of tuple(sent) -> list(replies)
    def call_response(self):
        cr = {}
        sort = sorted(self.messages, key=operator.attrgetter('date'))
        i = 0
        while i < len(sort):
            sent, received = [], []
            while i < len(sort) and sort[i].is_sent:
                sent.append(sort[i].text)
                i += 1
            while i < len(sort) and not sort[i].is_sent:
                received.append(sort[i].text)
                i += 1
            sent_text = " ".join(sent)
            received_text = " ".join(received)
            token_s = tuple(nltk.word_tokenize(str(sent_text)))
            token_r = nltk.word_tokenize(received_text)
            if token_s in cr:
                cr[token_s].append(token_r)
            else:
                cr[token_s] = [token_r]
        return cr

    # returns full transcript sorted by date sent (earliest text is tran[0])
    def transcript(self):
        tran = [m.text for m in sorted(self.messages, key=operator.attrgetter('date'))]
        return tran

    def __repr__(self):
        return pformat({self.recipient: self.messages})



# encapsulates all conversations in iMessage data
class Conversations:
    def __init__(self, all_messages, recipients):
        self.messages = all_messages
        self.recipients = recipients
        self.text_conversations = self.process_conversations(recipients)

    def all_received_text(self):
        convos = self.text_conversations
        received = " ".join([m for c in convos for m in c.received_messages()])
        return received

    def all_sent_text(self):
        convos = self.text_conversations
        sent = " ".join([m for c in convos for m in c.sent_messages()])
        return sent

    def all_text(self):
        return " ".join([m.text for m in self.all_messages])

    def sent_vocabulary(self):
        return tokens(self.get_sent_text())

    def received_vocabulary(self):
        return tokens(self.get_received_text())

    def vocabulary(self):
        return tokens(self.get_all_text())

    # returns number of messages
    def size(self):
        return len(self.messages)

    # returns a list of TextConversations with given recipients
    def process_conversations(self, recipients):
        convos = [TextConversation(get_name_from_address_book(r.phone_or_email),
                                   get_messages_for_recipient(r.handle_id)) for r in recipients]
        return convos

    def __iter__(self):
        return iter(self.text_conversations)

    def __getitem__(self, item):
        return self.text_conversations[item]

    def __repr__(self):
        return str(self.text_conversations)

def _new_connection():
    # The current logged-in user's Messages sqlite database is found at:
    # ~/Library/Messages/chat.db
    db_path = expanduser("~") + '/Library/Messages/chat.db'
    return sqlite3.connect(db_path)

def get_name_from_address_book(phone_or_email):
    book = AddressBook()
    try:
        name = book.query_number(AddressBook.clean_number(phone_or_email))
        if not name:
            # try getting rid of the 1
            name = book.query_number(AddressBook.clean_number(phone_or_email)[1:])
    except KeyError:
        name = book.query_email(phone_or_email.lower())
    if not name:
        return phone_or_email
    return name

# Fetches all known recipients.
#
# The `id`s of the recipients fetched can be used to fetch all messages exchanged with a given recipient.
def get_all_recipients():
    connection = _new_connection()
    c = connection.cursor()

    # The `handle` table stores all known recipients.
    c.execute("SELECT handle.id, handle.rowid FROM `handle`")
    recipients = [Recipient(row[0], row[1]) for row in c]

    connection.close()
    return recipients

def process_messages(cursor):
    messages = []
    for row in cursor:
        text, date, id, is_sent = row
        if text is not None:
            encoded_text = text.encode('ascii', 'ignore')
            date = datetime.fromtimestamp(date + OSX_EPOCH)
            messages.append(Message(encoded_text, date, id, is_sent))
            # Strip any special non-ASCII characters (e.g., the special character that is used as a placeholder for attachments such as files or images).
    return messages

# Fetches all messages exchanged with a given recipient.
def get_messages_for_recipient(id):
    connection = _new_connection()
    c = connection.cursor()

    # The `message` table stores all exchanged iMessages.
    c.execute(
        "SELECT MESSAGE.TEXT, MESSAGE.DATE, MESSAGE.HANDLE_ID, MESSAGE.is_sent FROM `message` WHERE handle_id=" + str(
            id))
    messages = process_messages(c)
    connection.close()
    return messages


def get_all_messages_with(name):
    # TODO
    # DOES NOT WORK NOW
    messages = get_all_messages()
    #pprint(messages)
    return messages[unicode(name.lower())]

def get_all_messages():
    connection = _new_connection()
    c = connection.cursor()

    # The `message` table stores all exchanged iMessages.
    c.execute("SELECT MESSAGE.TEXT, MESSAGE.DATE, MESSAGE.HANDLE_ID, MESSAGE.is_sent FROM `message`")
    messages = process_messages(c)
    connection.close()
    return messages

def get_convos():
    all_messages = get_all_messages()
    recipients = get_all_recipients()
    return Conversations(all_messages, recipients)
# def sentences(all_text):
#     # this takes a couple seconds
#     nlp = spacy.load('en')
#     clean = cleaned(all_text)
#     doc = nlp(clean)
#     return doc.sents



if __name__ == '__main__':
    convos = get_convos()
    print convos.text_conversations[0].call_response()
    # vocab = convos.vocabulary()
    # sentences = itertools.ifilter(lambda x: len(x) > 2, sentences(sent))
    # counts = {}
    # for s in sentences:
    #     c = counts.setdefault(str(s), 0)
    #     counts[str(s)] += 1
    # pprint(Counter(counts).most_common(50))
    # # print '\n\n\n\n'
    # # pprint(Counter(vocab).most_common(50))

