from __future__ import annotations

# Pinned in code, not settings -- mirrors knowledge_base's EMBEDDING_MODEL_TAG. Swapping the chat
# model affects prompt/tool-schema tuning and should be a reviewed code change, not an
# environment-variable flip that could silently change agent behaviour between deployments.
#
# Minor open item, not blocking: re-verify this exact tag against Ollama's current cloud catalog
# before first run (cloud model tags evolve) -- e.g. `ollama run gemma4:cloud` once manually, or
# check https://ollama.com/library.
CHAT_MODEL_TAG = "gemma4:cloud"
