# In consumers.py
import logging

from channels import Group
from channels.sessions import channel_session

# Logger variable to record such things
LOGGER = logging.getLogger(__name__)


# client who just connected is part of the ws Group
# messages sent via ws, will be sent to that client as well.
@channel_session
def ws_connect(message):
    # Accept the connection request
    message.reply_channel.send({"accept": True})
    Group("ws").add(message.reply_channel)


# Remove the client once they do a WebSocket.close() or they close their browser etc.
@channel_session
def ws_disconnect(message):
    Group("ws").discard(message.reply_channel)


# receives any incoming messages that come from client to the server
@channel_session
def ws_receive(message):
    LOGGER.debug("received" + message['text'])

    Group("ws").send({
        "text": message['text'] + ' echoed',
    })
