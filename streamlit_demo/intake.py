"""Convert a short business form to the notebook's six evidence fields."""
from uuid import uuid4

FIELDS = {
    'purpose': (('business_value','adoption'), 'What outcome matters and who would use or sponsor the idea?'),
    'workflow': (('feasibility','productivity'), 'How does the task work today and what effort or outcome could improve?'),
    'data': (('data_readiness','risk'), 'What data is available and what access, sensitivity or review constraints apply?'),
}

def to_case(values):
    purpose = values.get('purpose','').strip()
    if not purpose:
        raise ValueError('Please describe your idea, intended users and purpose in question 1.')
    title = purpose.splitlines()[0][:100]
    facts = {criterion: values.get(field,'').strip() or None
             for field,(criteria,_) in FIELDS.items() for criterion in criteria}
    return {'case_id': 'CUSTOM-'+uuid4().hex[:8], 'title':title, 'facts':facts}

def from_case(c):
    return {field:'\n'.join(dict.fromkeys(c['facts'][k] for k in criteria if c['facts'][k]))
            for field,(criteria,_) in FIELDS.items()}

def questions(c):
    return [question for criteria,question in FIELDS.values() if any(not c['facts'][k] for k in criteria)]

def demo_match(c, samples):
    # Never reuse a fixture merely because a custom submission shares a title or ID.
    return next((sample for sample in samples
                 if c['title']==sample['title'] and c['facts']==sample['facts']),None)
