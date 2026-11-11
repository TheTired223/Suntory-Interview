"""Presentation demo: streamlit run streamlit_app.py"""
import json
import os
import pandas as pd
import streamlit as st
from evaluator_core import (CRITERIA, RUBRIC, PROMPTS, Assessment, cases,
                            demo_assessment, decision, evidence_issues)
from intake import FIELDS, to_case, from_case, questions, demo_match
from api_errors import explain_api_error
from providers import PROVIDERS, evaluate_live

st.set_page_config(page_title='AI Use Case Evaluator', page_icon='💡', layout='wide')
st.markdown('''<style>
.stApp { background: #F8F7F3; }
h1,h2,h3 { color: #102F36; }
[data-testid="stMetricValue"] { color:#007F80; }
.block-container { padding-top:2.4rem; max-width:1350px; }
</style>''', unsafe_allow_html=True)

LABELS = {'business_value':'Business value','feasibility':'Feasibility',
          'data_readiness':'Data readiness','risk':'Risk complexity',
          'adoption':'Adoption potential','productivity':'Productivity impact'}
if 'records' not in st.session_state:
    st.session_state.records = []
if st.session_state.get('intake_version') != 3:
    st.session_state.intake_version = 3
    for key in list(FIELDS):
        st.session_state['draft_'+key]=''

def load_sample():
    selected = st.session_state.sample
    values = from_case(next(c for c in cases if c['title']==selected)) if selected!='Start a new idea' else {k:'' for k in list(FIELDS)}
    for key,val in values.items():
        st.session_state['draft_'+key]=val

def record(c, mode, a=None, meta=None):
    if a is None:
        outcome = {'case_id':c['case_id'],'use_case':c['title'],
                   **{k:None for k in CRITERIA},'total':None,'priority':None,
                   'status':'Awaiting live evaluation',
                   'next_action':'Answer the follow-up questions, or evaluate this submission in Live AI mode.'}
    else:
        outcome = decision(a,c)
    return {'input':c,'mode':mode,'assessment':a.model_dump() if a else None,
            'decision':outcome,'metadata':meta or {},
            'follow_up':list(dict.fromkeys(questions(c)+(a.follow_up_questions if a else [])))}

with st.sidebar:
    st.title('Evaluation settings')
    mode=st.radio('Evaluation mode',['Presentation demo','Live AI'],key='mode')
    provider='OpenAI'
    if mode=='Live AI':
        provider=st.selectbox('AI provider',list(PROVIDERS),key='provider')
        settings=PROVIDERS[provider]
        model=st.text_input('Model ID',value=os.getenv(settings['model_env'],settings['default_model']),
                            key='model_'+provider)
        api_key=st.text_input(provider+' API key',type='password',key='key_'+provider,
                              help='Leave blank to use '+settings['key_env']+' from the environment.')
        st.link_button('Get a '+provider+' API key',settings['key_url'])
        if provider=='Gemini':
            st.caption('Free-tier access depends on your Google project and model quotas. Use synthetic data for the demo.')
        st.caption('Submitting sends this form to '+provider+'. Provider pricing and limits apply. Keys stay out of downloads.')
    else:
        model=api_key=''
        st.caption('No API calls. Unchanged samples use authored fixtures. New or edited ideas show intake feedback without AI scores.')
    st.divider()
    st.caption('Session only: browser refresh may clear your history. Download results before leaving.')
    if st.button('Clear evaluation history'):
        st.session_state.records=[]
        st.rerun()

st.caption('SUNTORY BEVERAGE & FOOD ASIA · INTERVIEW PROTOTYPE')
st.title('AI Use Case Evaluator')
st.write('Describe your idea in plain language. See its potential, readiness and the next questions to resolve.')
if mode=='Presentation demo':
    st.info('Presentation demo — sample scores are illustrative. Custom ideas receive intake feedback until you enable Live AI.')
submit_tab, results_tab, criteria_tab = st.tabs(['Submit an idea','Evaluation results','Evaluation criteria'])

with submit_tab:
    st.subheader('A short starting point')
    st.write('Three short answers are enough to start. Describe your purpose first, then add what you know about the workflow and data.')
    st.selectbox('Try a notebook example', ['Start a new idea']+[c['title'] for c in cases],key='sample',on_change=load_sample)
    with st.form('use_case_form'):
        st.text_area('1. What is your idea, who would use it, and why does it matter? *',
                     key='draft_purpose',height=115,max_chars=3000,
                     placeholder='Start with a short idea name. Then describe the outcome and intended users.',
                     help='Supports business value and adoption potential.')
        st.text_area('2. How is the task done today, and what would improve?',
                     key='draft_workflow',height=115,max_chars=3000,
                     placeholder='Mention the task, systems involved and expected benefit. Include frequency or time savings if known.',
                     help='Supports feasibility and productivity impact. Leave blank if unknown.')
        st.text_area('3. What data would it use, and what constraints should we consider?',
                     key='draft_data',height=115,max_chars=3000,
                     placeholder='Mention documents or systems, access, sensitive information and who would check the output.',
                     help='Supports data readiness and risk complexity. Leave blank if unknown.')
        submitted=st.form_submit_button('Evaluate this idea',type='primary')
    if submitted:
        values={key:st.session_state['draft_'+key] for key in list(FIELDS)}
        try:
            c=to_case(values)
        except ValueError as exc:
            st.error(str(exc))
        else:
            try:
                if mode=='Presentation demo':
                    sample=demo_match(c,cases)
                    if sample:
                        c=sample
                        r=record(c,'Demo fixture',demo_assessment(c,'improved_v2'),
                                 {'provenance':'Hand-authored fixture, not a model response','prompt_version':'improved_v2'})
                    else:
                        r=record(c,'Intake only')
                else:
                    key=api_key.strip() or os.getenv(PROVIDERS[provider]['key_env'],'').strip()
                    if not model.strip() or not key.strip():
                        raise ValueError('Enter a model ID and API key, or configure their environment variables.')
                    with st.spinner('Evaluating the submitted evidence…'):
                        a,meta=evaluate_live(c,provider,key,model.strip())
                    r=record(c,'Live AI',a,meta)
                st.session_state.records.append(r)
                st.success('Saved. Open Evaluation results to inspect the assessment and next steps.')
                st.write('**Outcome:**',r['decision']['status'])
                if r['follow_up']:
                    st.write('**Questions to strengthen this submission**')
                    for question in r['follow_up']:
                        st.write('• '+question)
            except Exception as exc:
                if isinstance(exc,ValueError) and (not model.strip() or not key.strip()):
                    st.error('Enter a model ID and API key in Evaluation settings.')
                else:
                    st.error(explain_api_error(exc,provider))
                    st.link_button('Open '+provider+' limits', PROVIDERS[provider]['limits_url'])
                    if provider=='OpenAI':
                        st.link_button('Open API billing', 'https://platform.openai.com/settings/organization/billing/overview')

with results_tab:
    records=st.session_state.records
    if not records:
        st.subheader('Your assessments will appear here')
        st.write('Load Marketing content drafting for a pilot candidate, then Sales meeting summarisation to demonstrate a risk gate.')
    else:
        st.subheader('Evaluation history')
        # Keep provenance visible for every row; this is history, not a mixed-mode ranking.
        rows=[{'Idea':r['input']['title'],'Source':r['mode'],'Provider':r['metadata'].get('provider','Demo / intake'),
               'Model':r['metadata'].get('model','Not applicable'),
               'Score /24':r['decision']['total'],'Priority':r['decision']['priority'] or 'Not assigned',
               'Status':r['decision']['status']} for r in records]
        st.dataframe(pd.DataFrame(rows),width='stretch',hide_index=True)
        selected=st.selectbox('Inspect an assessment',list(range(len(records))),
                              index=len(records)-1,format_func=lambda i:f"{i+1}. {records[i]['input']['title']} ({records[i]['mode']})")
        r=records[selected]; d=r['decision']; c=r['input']
        st.subheader(c['title'])
        if r['mode']=='Live AI':
            st.caption('Provider: '+r['metadata'].get('provider','OpenAI')+' / Model: '+r['metadata'].get('model','Unknown'))
        if r['mode']=='Demo fixture':
            st.warning('Illustrative fixture: this assessment is authored, not generated by a live model.')
        elif r['mode']=='Intake only':
            st.info('Intake captured. Live AI evaluation is required for scores on new or edited ideas.')
        a,b,col=st.columns([1,1,2])
        a.metric('Priority score /24','Unknown' if d['total'] is None else str(d['total']))
        b.metric('Priority',d['priority'] or 'Not assigned')
        col.write('**Review status**');col.write(d['status'])
        st.write('**Recommended next action**');st.write(d['next_action'])
        if r['assessment']:
            assessment=Assessment.model_validate(r['assessment'])
            dims=[{'Criterion':LABELS[k],'Score':getattr(assessment.criteria,k).score,
                   'Reason':getattr(assessment.criteria,k).rationale} for k in CRITERIA]
            st.dataframe(pd.DataFrame(dims),width='stretch',hide_index=True)
            if assessment.risk_flags:
                st.write('**Risk flags**')
                for flag in assessment.risk_flags: st.write('• '+flag)
            issues=evidence_issues(assessment,c)
            if issues:
                st.warning('Evidence review needed: '+'; '.join(issues))
            with st.expander('Supporting evidence and missing information'):
                for k in CRITERIA:
                    dim=getattr(assessment.criteria,k)
                    st.markdown('**'+LABELS[k]+'**')
                    for quote in dim.evidence: st.text(quote)
                    for gap in dim.missing_information: st.write('Missing: '+gap)
        if r['follow_up']:
            st.write('**Follow-up questions**')
            for q in r['follow_up']: st.write('• '+q)
        with st.expander('Submitted information'):
            for k in CRITERIA:
                st.write('**'+LABELS[k]+'**')
                st.text(c['facts'][k] or 'Not supplied')
        st.download_button('Download this assessment (JSON)',json.dumps(r,indent=2),
                           file_name='use_case_assessment.json',mime='application/json')
        st.download_button('Download evaluation history (CSV)',pd.DataFrame(rows).to_csv(index=False),
                           file_name='evaluation_history.csv',mime='text/csv')

with criteria_tab:
    st.subheader('What makes a promising AI use case?')
    st.write('Each criterion uses a 1–5 scale. Higher is better except risk, where higher means more complexity. Unknown information stays unknown.')
    for k in CRITERIA:
        with st.expander(LABELS[k],expanded=k=='business_value'):
            for score in range(1,6):
                st.write(f"**{score}:** {RUBRIC[k][score]}")
    st.subheader('How priority works')
    st.code('Business value + Feasibility + Data readiness\n+ Adoption + Productivity − Risk',language=None)
    st.write('Complete scores range from 0 to 24. P1: 18–24. P2: 12–17. P3: 0–11.')
    st.write('Missing evidence requires clarification. Risk ≥4 or any risk flag requires specialist review. Unsupported evidence requires evidence review. Review gates prevent priority assignment.')
    st.caption('Weights and thresholds are provisional. Quotes confirm provenance, not truth. Business owners remain responsible for decisions.')

st.divider()
st.caption('Decision support prototype. A priority recommends the next discussion; it does not approve deployment.')

