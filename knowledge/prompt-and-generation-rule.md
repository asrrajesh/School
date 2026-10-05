# Prompts and Generation Rules (current state)

> Reverse-engineered on 2026-10-03 (git `67ba196`) from `llm/`, `ocr/`, `services/question_service.py`, `services/paper_generator.py`, `routers/ebooks.py` and the Generate Questions screen.

## 1. Pipeline overview

```
Setup E-Books:  images ──OCR──> text ──(user edits)──> scanned_chapters.content
Generate:       chapters' text + config + complexity ──LLM──> questions JSON ──> questions (new version)
Upload paper:   images ──OCR──> text ──(user edits)──> LLM extraction ──> questions JSON ──> questions (new version)
Export:         questions document ──python-docx──> .docx   (no AI)
```

## 2. OCR

- Selected by `OCR_ENGINE`: `easyocr` (default) or `llm_vision`. Independent of `LLM_PROVIDER`, so a text-only LLM can be paired with EasyOCR.
- **easyocr** (`ocr/easyocr_engine.py`): local EasyOCR reader, `OCR_LANGUAGES` (default `en`), `OCR_USE_GPU` (default false), paragraph mode. The model loads at API startup (lifespan hook, errors swallowed) to avoid a slow first request.
- **llm_vision** (`ocr/llm_vision_engine.py`): sends each image to the configured LLM with `OCR_EXTRACTION_PROMPT`, `max_tokens=4096`, `temperature=0`. Needs a vision-capable model. MIME type is guessed from the filename (default `image/jpeg`).
- Prompt: "Extract all text from this textbook page exactly as written. Preserve headings, numbered lists, paragraphs, and questions. Return only the extracted text, with no commentary."
- Output per image is wrapped as `--- <filename> ---\n<text>` and images are joined by a blank line. An image with no bytes raises an error.

## 3. LLM provider layer

- Interface `LLMProvider.generate_text(prompt, images, max_tokens, temperature)`; `generate_json` calls it and parses the result (`llm/base.py`).
- Factory `llm/factory.py` selects by `LLM_PROVIDER`: `claude` (default), `openai`, `gemini`, `ollama`. Instances are cached.
- Defaults: Claude `claude-sonnet-4-5-20250929` (`ANTHROPIC_MODEL`), OpenAI `gpt-4o`, Gemini `gemini-1.5-pro`, Ollama `llava` at `http://localhost:11434`.
- **No provider overrides `generate_json`**, so none uses a native JSON mode. All rely on the prompt asking for JSON and on `llm/json_utils.py`, which strips a leading or trailing markdown fence (and a `json` tag) and runs `json.loads`. Failures raise `LLMResponseError` with a 500-character preview.
- Claude provider: one user message (images first as base64, then the prompt); SDK errors are mapped to `LLMAuthenticationError`, `LLMPermissionError`, `LLMConnectionError`, `LLMResponseError`. The other providers were not reviewed line by line.
- Call parameters used by the question service: `max_tokens=4096` (hardcoded; `LLM_MAX_TOKENS` and `LLM_TEMPERATURE` are defined in config but not used here), temperature default 0.

## 4. Question generation

**Entry:** `POST /api/ebooks/generate-questions` → `generate_questions_from_chapter()` → `build_question_generation_prompt()`.

**Inputs:** concatenated chapter text (`--- <chapter> ---` headers), `questionRows`, `complexity`.

**Complexity guidance** (inserted into the prompt):
| Level | Instruction |
|---|---|
| basic | "test direct recall and simple definitions straight from the chapter. Keep language simple and avoid multi-step reasoning." |
| intermediate (default for unknown values) | "mix recall with 'why' and 'how' questions that require understanding and applying a concept, not just repeating it." |
| advanced | "favor higher-order thinking: analysis, comparison, or connecting multiple concepts from the chapter. Avoid pure recall." |

**Per-row requirements** (`build_question_requirements`):
| `questionType` | Line added to the prompt |
|---|---|
| `mcq` | `- {count} multiple-choice questions ({marks} marks each) with 4 options and one correct answer` |
| `short` | `- {count} short-answer questions ({marks} marks each) with a brief answer key (1-2 sentences)` |
| `long` | `- {count} long-answer questions ({marks} marks each) with a detailed answer key (3-5 sentences)` |
| anything else | **no line is added** (ignored silently) |

**Prompt skeleton:** persona "expert teacher"; `CHAPTER CONTENT`; difficulty level and guidance; `QUESTIONS TO GENERATE` list; the JSON shape below; guidelines (4 options A–D with the correct one marked for MCQ; clear, concise answer keys; diverse coverage of the chapter; test understanding, not just recall; match the difficulty for every question; total marks must equal count × marks per question); "Return ONLY valid JSON, no additional text."

**Output JSON shape** (shared with extraction):
```json
{"questions": [
  {"type": "mcq" | "short" | "long", "marks": <number>, "question": "<text>",
   "options": ["A","B","C","D"], "correctOption": "A", "answerKey": "<answer or explanation>"}
]}
```
(`options` and `correctOption` only for MCQ.) The service returns `data["questions"]` (empty list if the key is absent).

## 5. Question extraction from an uploaded paper

**Entry:** `POST /save-uploaded-questions` (or `/upload-questions`) → `extract_questions_from_paper(paper_text, complexity)` → `build_paper_extraction_prompt()`.
- Persona "expert teacher analyzing an uploaded question paper". Asks for type (MCQ, short or long, based on options and answer length), text, marks, options, and answer key if present.
- Defaults stated in the prompt: marks missing → 1 for MCQ, 2 for short, 5 for long; MCQ options labelled A–D; take the answer from an answer key if present, else `answerKey` is `""`; preserve exact question text; be strict about type.
- The `complexity` argument is accepted but **not used** by the prompt; it is only stored on the saved document.
- The configuration rows sent by the UI are saved with the document but **not used to map or constrain extraction**, although the UI text says the scan is mapped "to your selections".

## 6. Saving and versioning
After generation or extraction the questions are saved unchanged as a new `questions` document (see [data-model.md](data-model.md)) with the next version number. There is no validation of types, counts or marks, no de-duplication, and no review step.

## 7. Word export rules (`services/paper_generator.py`)
- Title: `"<FA|SA> <number>"` centred and bold. A two-cell line shows `Subject: <subject>` on the left and marks on the right: `Marks: <questions> x <marks> = <total>` when all configuration rows share one marks value, otherwise `Marks: <total>`.
- Sections follow the **order of the configuration rows**, numbered I, II, III … (Arabic numerals after X). If configuration is empty, section order follows the order in which types first appear in the questions.
- Section titles by type: mcq "Choose the correct answer"; fib "Fill in the blanks with a suitable correct answer"; mtf "Match the following"; tf "Answer the following statements are True or False"; sa "Answer the following in one sentence"; short "Answer the following questions (Short)"; long "Answer the following questions (Long)"; diagram "Draw a neat labeled diagram of the following". Unknown types use the title-cased type name.
- Each question: running number, text and `[N mark(s)]`. MCQ options are listed as A, B, C, … as bullets.
- Final page "Answer Key": `n. <correctOption> - <answerKey>` for MCQ, otherwise the `answerKey`.
- python-docx default page size (US Letter), 2 cm margins. No school name, class, chapters, date, duration or student fields.

## 8. Known gaps in the generation rules

1. **Type mismatch:** the UI offers 8 question types (mcq, fib, mtf, sa, tf, short, long, diagram) but the generation prompt knows only mcq, short and long. Rows of any other type are dropped from the prompt, so such questions are not requested. If all rows are of those types, the prompt lists no questions to generate.
2. **Export drops unconfigured types:** when configuration rows exist, the `.docx` includes only questions whose `type` matches a configured type. For uploaded papers the LLM may return types the user did not configure; those questions are saved but omitted from the document.
3. **No marks or count validation** after generation, despite the prompt asking for exact totals.
4. **Token limit:** `max_tokens` is fixed at 4096, which may truncate large question sets or long extractions and then fail JSON parsing.
5. **Input size:** multi-chapter text is concatenated with no length limit.
6. Generated answer keys are unverified LLM output.
7. Router docstrings and UI client docstrings say "Claude" although the provider is configurable.
