---
name: llm-provider-rules
description: Use whenever adding or changing an LLM or OCR provider, a prompt, or question-generation/extraction logic in edukoreaiapi (llm/, ocr/, services/question_service.py, services/ocr_service.py, services/paper_generator.py).
---

# LLM and OCR provider rules

Prompts, generation rules and the `.docx` format are documented in `knowledge/prompt-and-generation-rule.md`; read it first.

## Rules
1. **Providers sit behind base classes.** LLM providers implement `LLMProvider` (`llm/base.py`); OCR engines implement `OCRProvider` (`ocr/base.py`). Services and routers depend only on these interfaces and obtain instances from `get_llm_provider()` (`llm/factory.py`) and `get_ocr_engine()` (`ocr/factory.py`). Never import a concrete provider or hardcode provider logic at a call site.
2. **Adding a provider:**
   - LLM: add `llm/providers/<name>_provider.py`, a `_build_<name>` function and an entry in `_BUILDERS` in `llm/factory.py`.
   - OCR: add the engine module, a `_build_<name>` function and an entry in `_BUILDERS` in `ocr/factory.py`.
   - Add its settings to `config/config.py` and `edukoreaiapi/.env.example`. In production, secrets also go into `deploy-api.yml` (see the `security-rules` skill).
3. **Prompts live only in `llm/prompts/templates.py`.** Do not inline prompt text in services or providers.
4. **LLM output is untrusted.** Parse JSON through `llm/json_utils.py` and handle `llm/exceptions.py` errors; keep the `{"success": false, "error": ...}` response shape on failure.
5. **Heavy imports stay lazy** (for example EasyOCR is imported inside its builder) so unused providers do not load at startup.
6. **No provider-specific tests exist**; the scan test `tests/test_scanned_chapter.py` needs a configured OCR/LLM provider. State what you could not verify.
