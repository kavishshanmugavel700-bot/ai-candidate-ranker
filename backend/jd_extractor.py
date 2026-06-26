import google.generativeai as genai, json, os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

def extract_jd_requirements(jd_text: str) -> dict:
    prompt = f'''Read this job description. Return ONLY valid JSON with keys:
    required_skills (list), experience_years (int), domain (str),
    soft_skills (list), seniority (junior/mid/senior).
    Job Description: {jd_text}
    Respond with ONLY valid JSON — no extra text, no markdown.'''
    resp = model.generate_content(prompt).text.strip()
    resp = resp.replace('```json', '').replace('```', '').strip()
    return json.loads(resp)