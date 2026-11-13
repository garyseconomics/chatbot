"""Real discord.py objects (not mocks) for the tests, built without connecting to Discord.

Tests that use them break if discord.py changes where it stores the guild, the channel id
or the author id."""

import discord
from discord.state import ConnectionState

USER_ID = 456
CHANNEL_ID = 789
GUILD_ID = 100

# The JSON data Discord's API sends for a user and a message. discord.py builds its objects
# from data like this. Most fields are required by the library, not used by the tests.
USER_DATA = {"id": str(USER_ID), "username": "someone", "discriminator": "0", "avatar": None}
MESSAGE_DATA = {
    "id": "1",
    "channel_id": str(CHANNEL_ID),
    "author": USER_DATA,
    "content": "What is wealth?",
    "timestamp": "2026-01-01T00:00:00+00:00",
    "edited_timestamp": None,
    "tts": False,
    "mention_everyone": False,
    "mentions": [],
    "mention_roles": [],
    "attachments": [],
    "embeds": [],
    "pinned": False,
    "type": 0,
}


def _make_state() -> ConnectionState:
    """The library's connection state, never connected (no network)."""
    return ConnectionState(
        dispatch=lambda *args: None,
        handlers={},
        hooks={},
        http=None,
        intents=discord.Intents.default(),
    )


def make_real_dm_message() -> discord.Message:
    state = _make_state()
    me = state.store_user(USER_DATA)
    channel_data = {"id": str(CHANNEL_ID), "type": 1, "recipients": [USER_DATA]}
    channel = discord.DMChannel(me=me, state=state, data=channel_data)
    return discord.Message(state=state, channel=channel, data=MESSAGE_DATA)


def make_real_channel_message() -> discord.Message:
    state = _make_state()
    guild = discord.Guild(data={"id": str(GUILD_ID), "name": "server"}, state=state)
    channel_data = {"id": str(CHANNEL_ID), "type": 0, "name": "youtube-chatbot", "position": 0}
    channel = discord.TextChannel(state=state, guild=guild, data=channel_data)
    return discord.Message(state=state, channel=channel, data=MESSAGE_DATA)
