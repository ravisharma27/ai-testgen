# AI Test Case Generator

Turns a user story into **validated, structured test cases** using an LLM deployed on Azure AI Foundry.

Most "ChatGPT writes my tests" demos return free text that looks good but can't be parsed, traced or trusted. This project treats LLM output as untrusted input: every response is validated against a strict schema, and invalid output is sent back to the model with the exact validation errors until it is right or the attempt budget runs out.

![CI](https://github.com/<your-username>/ai-testgen/actions/workflows/ci.yml/badge.svg)

## What it does

```
user story (.md)  ->  LLM (gpt-5-mini on Azure)  ->  JSON  ->  Pydantic validation
                                ^                                     |
                                +------ errors fed back (retry) <------+
                                                                       |
                                                    validated TestSuite (.json)
```

Each generated test case has:

| Field | Rule |
|---|---|
| `id` | `TC-001` format, unique within the suite |
| `title` | 5 to 120 characters |
| `technique` | one of: happy_path, boundary_value, equivalence_partitioning, negative, error_guessing, state_transition, decision_table |
| `priority` | high, medium, low |
| `steps` | 1 to 15 non-blank actions |
| `expected_result` | specific and observable |
| `preconditions`, `test_data` | optional |

## Example

```bash
python -m testgen generate examples/stories/password_reset.md -o output/password_reset.json
```

```
ID      Technique                 Priority  Title
------------------------------------------------------------------------------------------
TC-001  happy_path                high      Reset link emailed for registered account
TC-002  negative                  high      Unknown email shows same confirmation message
TC-003  boundary_value            high      Password of exactly 8 characters is accepted
...
14 test cases | techniques: boundary_value, happy_path, negative, state_transition | attempts: 1 | tokens: 3120
```

The saved JSON also records every attempt (validation error, latency, tokens), which feeds the evaluation work planned below.

## Setup

**1. Azure resources** (one time): an Azure AI Foundry resource with a `gpt-5-mini` deployment.

**2. Auth.** Keyless by default via `DefaultAzureCredential`:

```bash
az login
az role assignment create \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role "Azure AI User" \
  --scope $(az cognitiveservices account show -n <resource> -g <rg> --query id -o tsv)
```

An API key also works: set `AZURE_OPENAI_API_KEY`. Never commit it.

**3. Install and configure**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
export AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
```

## Tests

```bash
pytest -q
```

Unit tests use a fake LLM client, so they run offline and in CI with no Azure credentials. They cover schema rules, retry on malformed JSON, retry on schema violations, and giving up after the attempt limit.

## Design decisions

- **Validate, don't trust.** JSON mode guarantees syntax, not meaning. Pydantic enforces the meaning (allowed techniques, id format, unique ids, non-empty steps).
- **Feed errors back.** Retries include the validator's exact messages, which fixes most failures on the second attempt instead of re-rolling blindly.
- **Prompt as code.** Prompts live in `testgen/prompts.py` so changes show up in diffs and code review.
- **Testable seam.** The generator accepts any OpenAI-compatible client, so the logic is tested without network calls.
- **Keyless first.** Entra ID auth is the default; keys are a fallback.

## Roadmap

- [x] **Week 1** - Structured generation with schema validation and retries
- [ ] **Week 2** - Convert generated cases to executable Playwright tests against a demo app; track first-run pass rate
- [ ] **Week 3** - Evaluation harness: golden dataset, coverage of acceptance criteria, run-to-run consistency, LLM-as-judge, model comparison
- [ ] **Week 4** - CI quality gate that fails pull requests when evaluation scores regress

## Project layout

```
testgen/
  schema.py      Pydantic models (the contract)
  prompts.py     system / user / retry prompts
  generator.py   generate -> validate -> retry loop
  client.py      Azure AI Foundry client (keyless or key)
  cli.py         command line interface
examples/stories user stories used as input
tests/           offline unit tests
```

## Author

Ravi Sharma - Lead Quality Assurance Developer, 20+ years in quality engineering and test automation.
