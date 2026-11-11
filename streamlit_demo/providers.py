"""Provider adapters sharing one rubric, schema and deterministic decision policy."""
import hashlib
import json
from datetime import datetime, timezone
from evaluator_core import Assessment, PROMPTS

PROVIDERS = {
    'OpenAI': {'default_model':'gpt-4.1-mini','model_env':'OPENAI_MODEL',
               'key_env':'OPENAI_API_KEY','key_url':'https://platform.openai.com/api-keys',
               'limits_url':'https://platform.openai.com/settings/organization/limits'},
    'Gemini': {'default_model':'gemini-2.5-flash-lite','model_env':'GEMINI_MODEL',
               'key_env':'GEMINI_API_KEY','key_url':'https://aistudio.google.com/apikey',
               'limits_url':'https://aistudio.google.com/usage'},
}

def evaluate_live(c, provider, api_key, model):
    if provider not in PROVIDERS:
        raise ValueError('Unsupported provider.')
    if not api_key.strip() or not model.strip():
        raise ValueError('A model ID and API key are required.')
    prompt = PROMPTS['improved_v2']
    usage = None
    if provider == 'OpenAI':
        from openai import OpenAI
        with OpenAI(api_key=api_key.strip(),timeout=60,max_retries=2) as client:
            response = client.responses.parse(
                model=model,input=[{'role':'system','content':prompt},
                                   {'role':'user','content':json.dumps(c)}],
                text_format=Assessment,max_output_tokens=4000,store=False)
        if response.status!='completed' or response.output_parsed is None:
            raise RuntimeError('No complete assessment returned.')
        a = response.output_parsed
        response_id, resolved_model = response.id, response.model
        usage = response.usage.model_dump() if response.usage else None
    else:
        from google import genai
        from google.genai import types
        # Explicit key and vertexai=False prevent accidental routing to another project/API.
        with genai.Client(api_key=api_key.strip(),vertexai=False,
                          http_options=types.HttpOptions(timeout=60000)) as client:
            response = client.models.generate_content(
                model=model,contents=json.dumps(c),
                config=types.GenerateContentConfig(
                    system_instruction=prompt,response_mime_type='application/json',
                    response_json_schema=Assessment.model_json_schema(),
                    max_output_tokens=4000))
        candidates = response.candidates or []
        if not candidates or candidates[0].finish_reason != types.FinishReason.STOP or not response.text:
            raise RuntimeError('No complete Gemini assessment returned.')
        a = Assessment.model_validate_json(response.text)
        response_id = getattr(response,'response_id',None)
        resolved_model = getattr(response,'model_version',None) or model
        usage = response.usage_metadata.model_dump(mode='json') if response.usage_metadata else None
    if a.case_id != c['case_id']:
        raise ValueError('Assessment ID mismatch.')
    return a, {'provider':provider,'requested_model':model,'model':resolved_model,
               'response_id':response_id,'prompt_version':'improved_v2',
               'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
               'input_sha256':hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest(),
               'timestamp_utc':datetime.now(timezone.utc).isoformat(),'usage':usage}
