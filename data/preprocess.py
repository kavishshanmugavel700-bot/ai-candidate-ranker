def build_profile_text(row) -> str:
    parts = []

    # candidate_id
    cid = row.get('candidate_id', '')
    if cid:
        parts.append(f"ID: {cid}")

    # profile — likely has name, title, summary inside
    profile = row.get('profile', '')
    if isinstance(profile, dict):
        name = profile.get('name') or profile.get('full_name') or ''
        title = profile.get('title') or profile.get('current_title') or profile.get('headline') or ''
        summary = profile.get('summary') or profile.get('bio') or profile.get('about') or ''
        location = profile.get('location') or profile.get('city') or ''
        if name:    parts.append(f"Name: {name}")
        if title:   parts.append(f"Role: {title}")
        if summary: parts.append(f"Summary: {str(summary)[:300]}")
        if location:parts.append(f"Location: {location}")
    elif isinstance(profile, str) and profile:
        parts.append(f"Profile: {profile[:300]}")

    # skills
    skills = row.get('skills', '')
    if isinstance(skills, list):
        skills = ', '.join(str(s) for s in skills)
    if skills:
        parts.append(f"Skills: {skills}")

    # career_history — list of jobs
    career = row.get('career_history', [])
    if isinstance(career, list) and career:
        job_titles = []
        companies  = []
        for job in career[:4]:  # only first 4 jobs
            if isinstance(job, dict):
                t = job.get('title') or job.get('role') or job.get('position') or ''
                c = job.get('company') or job.get('employer') or job.get('organization') or ''
                if t: job_titles.append(str(t))
                if c: companies.append(str(c))
        if job_titles: parts.append(f"Past roles: {', '.join(job_titles)}")
        if companies:  parts.append(f"Companies: {', '.join(companies)}")
    elif isinstance(career, str) and career:
        parts.append(f"Career: {career[:200]}")

    # education
    edu = row.get('education', '')
    if isinstance(edu, list):
        edu_texts = []
        for e in edu[:2]:
            if isinstance(e, dict):
                deg    = e.get('degree') or e.get('qualification') or ''
                school = e.get('institution') or e.get('university') or e.get('school') or ''
                if deg:    edu_texts.append(str(deg))
                if school: edu_texts.append(str(school))
            elif isinstance(e, str):
                edu_texts.append(e)
        if edu_texts:
            parts.append(f"Education: {', '.join(edu_texts)}")
    elif isinstance(edu, str) and edu:
        parts.append(f"Education: {edu}")

    # certifications
    certs = row.get('certifications', '')
    if isinstance(certs, list):
        certs = ', '.join(str(c) for c in certs[:5])
    if certs:
        parts.append(f"Certifications: {certs}")

    # languages
    langs = row.get('languages', '')
    if isinstance(langs, list):
        langs = ', '.join(str(l) for l in langs)
    if langs:
        parts.append(f"Languages: {langs}")

    # redrob_signals — behavioral signals
    signals = row.get('redrob_signals', {})
    if isinstance(signals, dict) and signals:
        exp_years = (signals.get('total_experience_years') or
                     signals.get('experience_years') or
                     signals.get('years_of_experience') or '')
        if exp_years:
            parts.append(f"Total experience: {exp_years} years")

    return '. '.join(str(p) for p in parts if p)


if __name__ == '__main__':
    from data.loader import load_sample
    import json

    df = load_sample()
    print("\n=== Sample profile texts ===\n")
    for _, row in df.head(5).iterrows():
        text = build_profile_text(row)
        print(text[:400])
        print('---')