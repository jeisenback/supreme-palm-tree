# DOCX to Markdown Converter

Simple CLI to convert `.docx` files to Markdown using `mammoth` (DOCX -> HTML) and `html2text` (HTML -> MD).

Installation

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Usage

```bash
python docx_to_md.py path/to/input.docx
python docx_to_md.py -o outdir file1.docx file2.docx
python docx_to_md.py --no-images input.docx
```

Output

- A Markdown file `input.md` will be written to the output directory.
- If the document contains images, an `input_assets` folder will be created containing extracted images and referenced from the Markdown.

Notes

- This is a straightforward converter; complex Word-specific features (tracked changes, comments, forms) may not convert perfectly.
- If you want different Markdown styling, adjust the `html2text` options in `docx_to_md.py`.


Template generation

Templates are plain Markdown (`.md`) files containing simple placeholders like `{{ key }}`.
Placeholders support nested keys with dot notation and list indexing (e.g. `{{ headings.0 }}`).

Example template (`email_template.md`):

```
Subject: {{ title }}

Hello {{ recipient_name }},

{{ summary }}

Best,
{{ author }}
```

Generate from a stored context JSON produced by the ingest pipeline:

```bash
python generate_cli.py -t email_template.md --context etn/financial/annual_planning/east_tn_business_plan_2025.json -o out/email.md
```

Or generate using a project + stem (looks for `<project>/converted/<stem>.json`):

```bash
python generate_cli.py -t email_template.md --project etn east_tn_business_plan_2025 -o out/email.md
```

Role agents
-----------

This repository includes PoC role agents to help board officers and staff. Invoke them via the `agents-cli` entrypoint:

Examples:

```bash
# Fundraising plan from inline CSV
PYTHONPATH=. python -m agents.agents_cli role fundraising --csv "donor,amount\nAlice,100\nBob,50\n"

# Membership insights from a file
PYTHONPATH=. python -m agents.agents_cli role membership --csv-file data/members.csv

# Draft communications from JSON
PYTHONPATH=. python -m agents.agents_cli role communications --json-file data/ctx.json

# Professional development plan
PYTHONPATH=. python -m agents.agents_cli role professional_development --json-file data/skills.json

# Operations checklist
PYTHONPATH=. python -m agents.agents_cli role operations --json-file data/ops.json

# Accelerator plan
PYTHONPATH=. python -m agents.agents_cli role accelerator --json-file data/apps.json
```


