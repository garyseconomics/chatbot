
from llm.llm_providers_helpers import select_llm_provider


def test_select_llm_provider_local():
    provider_priority = ["ollama_local"]
    provider_name = select_llm_provider(provider_priority)
    assert provider_name, "ollama_local"

def test_select_llm_provider_self_hosted():
    provider_priority = ["ollama_self_hosted","ollama_local"]
    provider_name = select_llm_provider(provider_priority)
    assert provider_name, "ollama_self_hosted"

def test_select_llm_provider_ollama_cloud():
    provider_priority = ["ollama_cloud","ollama_local"]
    provider_name = select_llm_provider(provider_priority)
    assert provider_name, "ollama_cloud"
