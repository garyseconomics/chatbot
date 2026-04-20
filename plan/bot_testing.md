# Bot Testing

## Testing Telegram Bot Changes 

### Create a Telegram Bot

   1. [Create a Telegram Bot](../README.md#create-a-telegram-bot)
   1. Update `.env` to include the Telegram API key

### Test Against the Local LLM 

   1. [Launch the local LLM](../README.md#install-ollama-and-download-the-models)
   1. [Download the database](../README.md#include-a-copy-of-the-database)
   1. Update `.env` to include the host 

### Launch Telegram Bot

   1. Before launching the bot, make sure you are inside the source dir

      ```
      cd src
      ```
   1. [Launch the Telegram Bot](../README.md#launch-the-telegram-bot)

### Issues

   1. There is no way to disable telemetry easily locally 
      ```
      2026-04-20 06:45:29,946 - opentelemetry.exporter.otlp.proto.http.trace_exporter - ERROR - Failed to export span batch code: 401, reason: Unauthorized
      2026-04-20 06:46:30,275 - opentelemetry.exporter.otlp.proto.http.trace_exporter - ERROR - Failed to export span batch code: 401, reason: Unauthorized
      ```
   1. Unit tests and integration tests are mixed
      ```
      @pytest.mark.skip(reason="missing cloud details")
      @pytest.mark.asyncio
      async def test_chat_ollama_cloud():
      ```
