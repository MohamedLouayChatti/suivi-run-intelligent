from __future__ import annotations

# The embedding model this module is calibrated for, pinned in code rather than in configuration.
#
# bge-m3 was chosen by the evaluation in notebooks/models_evaluation/, which compared it against
# qwen3-embedding:0.6b and embeddinggemma:300m on the historical ticket corpus, running the
# production pipeline itself (this module's preprocessor, ranking policy and result cap) with the
# model as the only experimental variable.
#
# These two constants are deliberately not settings. Three things are locked together and are only
# valid as a set: this tag, the vector column's dimension, and MIN_SIMILARITY_THRESHOLD in
# domain/services/similarity_ranking.py (cosine scores are not comparable across models, so a
# threshold calibrated for one model is meaningless for another). Changing the model is therefore
# a code change plus a migration plus a re-embed and rebuild -- not an environment variable.
# OllamaEmbeddingProvider.warm_up() enforces the dimension half of that pairing at runtime.
EMBEDDING_MODEL_TAG = "bge-m3"
EMBEDDING_DIMENSIONS = 1024
