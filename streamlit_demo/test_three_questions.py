from pathlib import Path
from streamlit.testing.v1 import AppTest
from evaluator_core import cases
from intake import to_case,from_case,demo_match
for c in cases:
    assert to_case(from_case(c))['facts']==c['facts']
    assert demo_match(to_case(from_case(c)),cases)==c
app=AppTest.from_file(str(Path(__file__).with_name('streamlit_app.py'))).run()
assert not app.exception,app.exception
assert len(app.text_area)==3 and len(app.text_input)==0
app.button(key='FormSubmitter:use_case_form-Evaluate this idea').click().run()
assert len(app.error)==1
for title,total in [('Marketing content drafting',20),('Sales meeting summarisation',18),('Beverage concept testing assistant',None)]:
    app.selectbox(key='sample').select(title).run()
    app.button(key='FormSubmitter:use_case_form-Evaluate this idea').click().run()
    assert not app.exception,app.exception
    assert app.session_state['records'][-1]['decision']['total']==total
app.text_area(key='draft_purpose').input('A different idea')
app.button(key='FormSubmitter:use_case_form-Evaluate this idea').click().run()
assert app.session_state['records'][-1]['assessment'] is None
app.selectbox(key='sample').select('Start a new idea').run()
app.text_area(key='draft_purpose').input('Summarise sales notes for representatives')
app.button(key='FormSubmitter:use_case_form-Evaluate this idea').click().run()
assert len(app.session_state['records'][-1]['follow_up'])==2
assert app.session_state['records'][-1]['decision']['priority'] is None
assert not app.exception,app.exception
print('PASS: exactly three questions, all five sample roundtrips, fixture isolation, validation, missing-information handling and review decisions.')
