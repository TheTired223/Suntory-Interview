"""Actionable API errors without displaying response bodies or credentials."""
def explain_api_error(exc, provider='OpenAI'):
    if isinstance(exc, ModuleNotFoundError):
        import re
        name = exc.name or 'unknown'
        safe_name = name if re.fullmatch(r'[A-Za-z0-9_.]+', name) else 'unknown'
        return ('A Python dependency is missing: '+safe_name+
                '. Install requirements.txt using the same Python interpreter that runs Streamlit, '
                'then restart the app. This error occurs before the API request.')
    if provider == 'Gemini':
        status = getattr(exc, 'code', None)
        if status == 429:
            return ('Gemini quota or rate limit reached. Check the selected Google project and model '
                    'in Google AI Studio Usage. Free-tier availability and daily/minute quotas vary. '
                    'Wait for the relevant reset before retrying. No result was substituted.')
        if status in (401,403):
            return 'Gemini authentication or permission error. Check the Google API key, project access and regional availability.'
        if status == 404:
            return 'Gemini model not found. Check the model ID and its availability in your Google project.'
        if status == 400:
            return 'Gemini rejected the request. Check model support for structured JSON output and the selected model ID.'
        return ('Gemini evaluation could not complete ('+type(exc).__name__+
                '). Check connectivity, model access and response validity. No result was substituted.')
    code = getattr(exc, 'code', None)
    if code is None:
        body = getattr(exc, 'body', None)
        if isinstance(body, dict):
            detail = body.get('error', body)
            if isinstance(detail, dict):
                code = detail.get('code') or detail.get('type')
    quota_codes = {'insufficient_quota','credit_balance_exhausted',
                   'billing_hard_limit_reached','billing_not_active',
                   'project_spend_limit_exceeded','organization_usage_limit_exceeded'}
    if code in quota_codes:
        return ('API quota or billing limit reached. Check the API project’s billing, '
                'credit balance and usage limits in the OpenAI dashboard. '
                'Waiting or creating another key does not restore quota. '
                'Reference: '+code)
    if getattr(exc,'status_code',None)==429 or type(exc).__name__=='RateLimitError':
        if code in {'rate_limit_exceeded','slow_down'}:
            return ('Request or token rate limit reached. Wait before submitting again, '
                    'then submit one idea at a time. Check your model’s limits in the '
                    'OpenAI dashboard. Reference: '+code)
        return ('OpenAI returned HTTP 429. This can indicate rate limits or unavailable '
                'API quota. Check API billing and credits first, then project/model limits. '
                'The response did not include a recognised diagnostic code.')
    if getattr(exc,'status_code',None)==401:
        return 'API authentication failed. Check that the key is valid and belongs to the intended API project.'
    return ('Evaluation could not complete ('+type(exc).__name__+
            '). Check model access, credentials or connectivity and retry. No result was substituted.')
