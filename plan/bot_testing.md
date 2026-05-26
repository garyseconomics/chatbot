# Bot Testing

## Manually Testing Telegram Bot

### Create a Telegram Bot

   1. [Create a Telegram Bot](../README.md#create-a-telegram-bot)
   1. Update `.env` to set the Telegram API key

### Start the Local LLM 

   1. [Launch the local LLM](../README.md#install-ollama-and-download-the-models)
   1. [Download the database](../README.md#include-a-copy-of-the-database)
   1. Update `.env` to set the local LLM host 

### Launch the Telegram Bot

   1. Before launching the bot, make sure you are inside the source dir.
      Otherwise, the Python interpreter won't be able to find `config` module.

      ```
      cd src
      ```
   1. If testing the message chunking, it may be necessary to reduce the chunk size as it is possible to make the LLM to produce a large answer consistently.
      The chunk size can be set in the `.env` file.
      ```
      TELEGRAM_MESSAGE_LIMIT=2048
      ```
   1. [Launch the Telegram Bot](../README.md#launch-the-telegram-bot)

### Issues

   1. Sending telemetry should be disabled if credentials are set.
      ```
      2026-04-20 06:45:29,946 - opentelemetry.exporter.otlp.proto.http.trace_exporter - ERROR - Failed to export span batch code: 401, reason: Unauthorized
      2026-04-20 06:46:30,275 - opentelemetry.exporter.otlp.proto.http.trace_exporter - ERROR - Failed to export span batch code: 401, reason: Unauthorized
      ``
   1. Integration tests should be automatically skipped locally using `skipIf`
      ```
      @pytest.mark.skipif(isCI, reason="Integration tests should only run on CI")
      @pytest.mark.asyncio
      async def test_chat_ollama_cloud():
      ```
