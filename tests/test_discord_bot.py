from interfaces.discord_bot import should_respond, strip_bot_mention


# --- should_respond ---


def test_ignores_own_messages():
    """The bot should not respond to its own messages to avoid infinite loops."""
    respond = should_respond(author_id=123, bot_id=123, is_dm=False, is_mentioned=False)
    assert respond is False


def test_ignores_own_messages_in_dm():
    respond = should_respond(author_id=123, bot_id=123, is_dm=True, is_mentioned=False)
    assert respond is False


def test_ignores_guild_messages_without_mention():
    """In guild channels, the bot only responds when explicitly @mentioned."""
    respond = should_respond(author_id=999, bot_id=123, is_dm=False, is_mentioned=False)
    assert respond is False


def test_responds_when_mentioned_in_guild():
    respond = should_respond(author_id=999, bot_id=123, is_dm=False, is_mentioned=True)
    assert respond is True


def test_responds_to_dm_without_mention():
    """In DMs, the bot responds to any message without requiring an @mention."""
    respond = should_respond(author_id=999, bot_id=123, is_dm=True, is_mentioned=False)
    assert respond is True


def test_responds_to_dm_with_mention():
    respond = should_respond(author_id=999, bot_id=123, is_dm=True, is_mentioned=True)
    assert respond is True


# --- strip_bot_mention ---


def test_strips_mention_from_message():
    result = strip_bot_mention("<@123> What is GDP?", bot_id=123)
    assert result == "What is GDP?"


def test_strips_mention_at_end_of_message():
    result = strip_bot_mention("What is GDP? <@123>", bot_id=123)
    assert result == "What is GDP?"


def test_leaves_message_without_mention_unchanged():
    result = strip_bot_mention("What is GDP?", bot_id=123)
    assert result == "What is GDP?"


def test_strips_only_bot_mention_not_other_users():
    result = strip_bot_mention("<@123> ask <@456> about GDP", bot_id=123)
    assert result == "ask <@456> about GDP"