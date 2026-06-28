import json, os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def extract_jd_requirements(jd_text: str) -> dict:
    prompt = f'''Read this job description carefully.
Return ONLY a valid JSON object with exactly these keys:
- required_skills (list of strings)
- experience_years (int)
- domain (string)
- soft_skills (list of strings)
- seniority (one of: junior, mid, senior)

Job Description:
{jd_text}

Respond with ONLY valid JSON. No markdown, no extra text, no explanation.'''

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    resp = response.choices[0].message.content.strip()
    resp = resp.replace('```json', '').replace('```', '').strip()

    try:
        return json.loads(resp)
    except json.JSONDecodeError:
        # fallback if JSON is slightly broken
        return {
            "required_skills": [],
            "experience_years": 0,
            "domain": "general",
            "soft_skills": [],
            "seniority": "mid"
        }


if __name__ == '__main__':
    test_jd = """
    We are looking for a Senior Python Developer with 5+ years of experience.
    Must know Django, REST APIs, PostgreSQL, and AWS.
    Strong communication skills required. Team player.
    """
    result = extract_jd_requirements(test_jd)
    print(json.dumps(result, indent=2))