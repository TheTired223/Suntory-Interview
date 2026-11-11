# Streamlit presentation demo

From a terminal opened in Desktop/Interview work/streamlit_demo:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

If Python is already selected in VS Code, use that interpreter instead of `py`. Open the localhost URL printed in the terminal. No API key is needed for the presentation demo.

## A short demonstration
1. Explain the two required fields: idea name and purpose. Other fields are optional and missing information leads to clarification.
2. Load **Marketing content drafting**, then Evaluate this idea. Open Evaluation results. The sample receives 20/24 and P1 for a pilot discussion.
3. Load **Sales meeting summarisation**, evaluate, and show how its score of 18 still requires specialist review and receives no priority.
4. Start a new idea with only name and purpose. Show that missing details generate follow-up questions. In presentation mode, custom or edited inputs have no AI scores.
5. Open Evaluation criteria to explain the six criteria and the scoring/review rules.

All sample details and demo assessments are synthetic authored fixtures. They do not establish prompt improvement. Choosing a sample fills the actual form. Editing any field invalidates its fixture match, preventing a canned score from being attached to different evidence.

## Live evaluation
Select Live AI in the sidebar. Enter an available Structured Outputs-compatible model ID and API key, or set OPENAI_MODEL and OPENAI_API_KEY before starting. Only pressing Evaluate sends a request. Custom submissions then receive genuine assessments. API usage charges apply. No API key enters the result exports. Network, refusal and invalid-output errors stay visible and do not fall back to fixtures. Live API execution needs to be verified with your account.

## Architecture
- `streamlit_app.py`: form, session history, results, criteria and downloads.
- `intake.py`: deterministic field mapping and missing-information questions.
- `evaluator_core.py`: reusable schema, prompts, rubric, fixtures and decision rules extracted from the notebook. Importing it makes no API requests and writes no files.
- `test_frontend.py`: meaningful AppTest checks. Run `python test_frontend.py` with dependencies installed.

The frontend evaluates one idea at a time and stores a history, without imposing the notebook's assessment-specific batch limit of 3â€“5. Data remains in the browser's server session until cleared or the session ends. Refresh can clear history. Download JSON/CSV to retain it. Exported assessments can contain business information.

The notebook remains unchanged. The frontend uses a snapshot of its reusable definitions; update both deliberately if the evaluation policy changes. This app uses the refined prompt only; use the notebook for the baseline-versus-refined experiment.

Official implementation references: https://docs.streamlit.io/develop/concepts/architecture/forms and https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest



## Gemini integration
Select Live AI, then Gemini in the provider selector. Default model: gemini-2.5-flash-lite.
Use a Google AI Studio key (https://aistudio.google.com/apikey), not an OpenAI key.
Alternatively set GEMINI_API_KEY and optionally GEMINI_MODEL in the app's environment.
Install updated requirements.txt with the same Python interpreter running Streamlit.
The app uses google-genai structured JSON output and validates it with the notebook's Pydantic schema.
Both providers use the same refined prompt, scoring and review gates. Results/downloads identify provider and model.
Provider keys have separate fields and environment variables. No provider fallback or automatic cross-provider requests occur.
Free-tier access and quotas depend on your Google project. Use synthetic cases for the presentation.
SDK and offline adapter tests do not establish live API access. Validate a live request with your own key before presenting.
The self-contained notebook supports both Gemini and OpenAI, including both baseline and refined prompts.
Official SDK reference: https://googleapis.github.io/python-genai/


## Three-question intake
The form now asks exactly three questions: (1) idea, intended users and purpose, (2) current workflow and expected improvement, (3) available data and constraints. Only the first answer is required. The idea title comes from its first line, so no separate name field is needed. Each answer supports two independently evaluated criteria. All five samples now use this format. A nonempty answer does not establish evidence for both criteria. Unknown information still needs clarification.


## Self-contained notebook submission
The notebook now includes its own three-question intake, full 1-5 rubric, provider adapters and safe error guidance. It does not import local app modules. Demo outputs are saved and labelled. For live evaluation choose PROVIDER and MODEL, set MODE to live and CONFIRM_LIVE_RUN to True, and supply your provider key using the hidden prompt or environment. Run all cells to collect ten assessments with the same provider/model. Live collection still needs human review before claiming prompt improvement. No API keys are saved.


The assessment notebook now lives one folder above this demo and uses three cases without canned outputs. The Streamlit app retains five labelled sample fixtures for presentation use. Its modules and settings are independent of the notebook.
