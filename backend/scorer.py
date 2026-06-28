import json, os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def score_candidate(candidate: dict, jd_req: dict) -> dict:
    profile   = candidate.get('profile', {})
    skills    = candidate.get('skills', [])
    career    = candidate.get('career_history', [])
    signals   = candidate.get('redrob_signals', {})
    education = candidate.get('education', [])
    certs     = candidate.get('certifications', [])

    if isinstance(profile, dict):
        name    = profile.get('name') or profile.get('full_name') or 'Unknown'
        title   = profile.get('title') or profile.get('current_title') or ''
        summary = profile.get('summary') or ''
    else:
        name, title, summary = str(profile), '', ''

    if isinstance(skills, list):
        skills_str = ', '.join(str(s) for s in skills[:20])
    else:
        skills_str = str(skills)

    career_str = ''
    if isinstance(career, list):
        for job in career[:3]:
            if isinstance(job, dict):
                t = job.get('title') or job.get('role') or ''
                c = job.get('company') or job.get('employer') or ''
                if t or c:
                    career_str += f"{t} at {c}, "

    exp_years = ''
    if isinstance(signals, dict):
        exp_years = (signals.get('total_experience_years') or
                     signals.get('experience_years') or '')

    candidate_summary = f"""
Name: {name}
Current Role: {title}
Skills: {skills_str}
Career History: {career_str}
Experience: {exp_years} years
Education: {education}
Certifications: {certs}
Summary: {str(summary)[:200]}
"""

    prompt = f'''You are an expert recruiter. Score this candidate for the job.

Job Requirements:
{json.dumps(jd_req, indent=2)}

Candidate Profile:
{candidate_summary}

Return ONLY a valid JSON object with exactly these keys:
- skills_score (0-100): how well skills match
- experience_score (0-100): how well experience matches
- growth_score (0-100): career growth and trajectory
- total_score (0-100): overall fit (skills 40% + experience 30% + growth 30%)
- reason (string): one sentence explaining the score

No markdown, no extra text, ONLY valid JSON.'''

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        resp = response.choices[0].message.content.strip()
        resp = resp.replace('```json', '').replace('```', '').strip()
        result = json.loads(resp)
    except Exception as e:
        print(f"Scoring error for {name}: {e}")
        result = {
            "skills_score": 0,
            "experience_score": 0,
            "growth_score": 0,
            "total_score": 0,
            "reason": "Could not score this candidate."
        }

    result['id']   = str(candidate.get('id', ''))
    result['name'] = name
    return result