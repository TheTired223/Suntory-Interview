"""Offline provider adapter and UI checks; never makes real API requests."""
import json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from google.genai import types
from evaluator_core import cases, demo_assessment
from providers import evaluate_live
from api_errors import explain_api_error

case=cases[3]
fixture=demo_assessment(case,'improved_v2')
reply=types.GenerateContentResponse(
    candidates=[types.Candidate(finish_reason=types.FinishReason.STOP,
                 content=types.Content(role='model',parts=[types.Part(text=fixture.model_dump_json())]))],
    model_version='gemini-2.5-flash-lite',response_id='test-response')
with patch('google.genai.Client') as Client:
    client=Client.return_value.__enter__.return_value
    client.models.generate_content.return_value=reply
    a,meta=evaluate_live(case,'Gemini','not-a-real-key','gemini-2.5-flash-lite')
    assert a==fixture
    assert meta['provider']=='Gemini'
    assert 'not-a-real-key' not in json.dumps(meta)
    kwargs=client.models.generate_content.call_args.kwargs
    assert kwargs['config'].response_mime_type=='application/json'
    assert kwargs['config'].response_json_schema['type']=='object'
    assert json.loads(kwargs['contents'])==case
    # Truncation cannot silently become a successful assessment.
    client.models.generate_content.return_value=types.GenerateContentResponse(
        candidates=[types.Candidate(finish_reason=types.FinishReason.MAX_TOKENS)])
    try: evaluate_live(case,'Gemini','not-a-real-key','gemini-2.5-flash-lite')
    except RuntimeError: pass
    else: raise AssertionError('Truncated response accepted')
    wrong=fixture.model_copy(update={'case_id':'WRONG'})
    client.models.generate_content.return_value=types.GenerateContentResponse(
        candidates=[types.Candidate(finish_reason=types.FinishReason.STOP,
                     content=types.Content(role='model',parts=[types.Part(text=wrong.model_dump_json())]))])
    try: evaluate_live(case,'Gemini','not-a-real-key','gemini-2.5-flash-lite')
    except ValueError: pass
    else: raise AssertionError('Wrong case ID accepted')

with patch('openai.OpenAI') as Client:
    client=Client.return_value.__enter__.return_value
    client.responses.parse.return_value=NS(status='completed',output_parsed=fixture,
                                          id='test',model='gpt-4.1-mini',usage=None)
    a,meta=evaluate_live(case,'OpenAI','fake-openai-key','gpt-4.1-mini')
    assert a==fixture and meta['provider']=='OpenAI'

error=type('ClientError',(Exception,),{'code':429})()
assert 'Gemini quota' in explain_api_error(error,'Gemini')

at=AppTest.from_file(str(Path(__file__).with_name('streamlit_app.py')),default_timeout=20).run()
at.radio(key='mode').set_value('Live AI').run()
at.selectbox(key='provider').select('Gemini').run()
assert at.text_input(key='model_Gemini').value=='gemini-2.5-flash-lite'
assert at.text_input(key='key_Gemini').value==''
at.selectbox(key='sample').select(case['title']).run()
at.text_input(key='key_Gemini').input('test-gemini-key')
with patch('providers.evaluate_live',return_value=(fixture,{'provider':'Gemini','model':'gemini-2.5-flash-lite'})) as evaluate:
    at.button(key='FormSubmitter:use_case_form-Evaluate this idea').click().run()
    assert evaluate.call_args.args[1]=='Gemini'
    assert evaluate.call_args.args[2]=='test-gemini-key'
assert at.session_state['records'][-1]['metadata']['provider']=='Gemini'
assert not at.exception,at.exception
at.selectbox(key='provider').select('OpenAI').run()
assert at.text_input(key='key_OpenAI').value==''
assert at.text_input(key='model_OpenAI').value=='gpt-4.1-mini'
assert not at.exception,at.exception
print('PASS: both adapters, Gemini schema/ID/truncation checks, error guidance, provider selection, credential isolation and result provenance.')
