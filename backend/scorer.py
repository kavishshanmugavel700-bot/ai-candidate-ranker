import json

def score_candidate(candidate: dict, jd_req: dict, model) -> dict:
    prompt = f'''Score this candidate for the job.
    Return ONLY valid JSON with keys:
    skills_score (0-100), experience_score (0-100),
    growth_score (0-100), total_score (0-100), reason (1 sentence).
    Job requires: {jd_req}
    Candidate: {candidate}
    Weights: skills 40%, experience 30%, growth 30%.
    ONLY valid JSON — no markdown.'''
    resp = model.generate_content(prompt).text.strip()
    resp = resp.replace('```json', '').replace('```', '').strip()
    result = json.loads(resp)
    result['id'] = candidate.get('id', '')
    result['name'] = candidate.get('name', '')
    return result