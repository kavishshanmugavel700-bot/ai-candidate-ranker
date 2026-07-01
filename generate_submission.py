import json
import csv
import argparse
import re
import sys
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Configuration & Constants ─────────────────────────────────────
DEFAULT_JD = """
We're looking for a Senior Backend Engineer with 4+ years of experience in Python, Django, and PostgreSQL. The role involves designing microservices, leading code reviews, building scalable REST APIs, and collaborating cross-functionally with product teams.
"""

COMPANIES_FOUNDED = {
    'Krutrim': 2023,
    'Sarvam AI': 2023
}

# A broad vocabulary of skill/domain terms we know how to recognise inside
# a JD. We intersect this with whatever words actually appear in the JD,
# so reasoning is always grounded in the JD that was actually passed in.
SKILL_VOCAB = [
    'python', 'django', 'flask', 'fastapi', 'postgresql', 'postgres', 'mysql',
    'mongodb', 'redis', 'rest api', 'restful', 'microservices', 'backend',
    'frontend', 'react', 'node.js', 'nodejs', 'javascript', 'typescript',
    'java', 'spring', 'kotlin', 'go', 'golang', 'rust', 'c++', 'c#',
    'pytorch', 'tensorflow', 'nlp', 'natural language processing',
    'machine learning', 'deep learning', 'computer vision', 'llm',
    'data science', 'data engineering', 'spark', 'airflow', 'kafka',
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'devops', 'ci/cd',
    'sql', 'nosql', 'data analysis', 'pandas', 'numpy', 'scikit-learn',
    'product management', 'agile', 'scrum', 'ux', 'ui design',
    'sales', 'crm', 'salesforce', 'b2b', 'negotiation',
]


# Generic role/title words that should NEVER be treated as skill keywords,
# even if they appear capitalized in the JD (e.g. "Data Scientist" should
# not produce the fake "skills" data and scientist).
TITLE_STOPWORDS = {
    'scientist', 'engineer', 'developer', 'manager', 'analyst', 'specialist',
    'lead', 'senior', 'junior', 'principal', 'staff', 'architect', 'director',
    'data', 'software', 'role', 'team', 'years', 'experience', 'looking',
    'strong', 'we', 'the', 'this', 'our', 'with', 'and', 'for',
}


def extract_jd_keywords(jd_text: str) -> list:
    """Pull out the skill/domain terms that are ACTUALLY present in this JD,
    instead of relying on a hardcoded list tied to the default JD."""
    jd_lower = jd_text.lower()
    found = [kw for kw in SKILL_VOCAB if kw in jd_lower]

    # Light fallback for technical terms the vocab might miss (tool/library
    # names we didn't anticipate). Filter out generic title/role words so
    # we don't end up treating "Scientist" or "Data" as a missing skill.
    extra_terms = re.findall(r'\b[A-Z][a-zA-Z0-9+.#]{2,}\b', jd_text)
    extra_terms = [
        t.lower() for t in extra_terms
        if t.lower() not in found and t.lower() not in TITLE_STOPWORDS
    ]
    return found + extra_terms[:5]


# ── Honeypot Detection ───────────────────────────────────────────
def is_honeypot(c) -> bool:
    # 1. Skill honeypots: expert/advanced skill with 0 duration
    for s in c.get('skills', []):
        if s.get('proficiency') in ['expert', 'advanced'] and s.get('duration_months', -1) == 0:
            return True

    # 2. Company honeypots: start date before company foundation
    for job in c.get('career_history', []):
        company = job.get('company')
        start_date = job.get('start_date', '')
        if company in COMPANIES_FOUNDED and start_date:
            try:
                start_year = int(start_date[:4])
                if start_year < COMPANIES_FOUNDED[company]:
                    return True
            except ValueError:
                pass

    # 3. Implausible experience-to-skill-count ratio: claims many "expert"
    #    skills relative to total years of experience.
    profile = c.get('profile', {})
    years = profile.get('years_of_experience', 0) or 0
    expert_skills = sum(1 for s in c.get('skills', []) if s.get('proficiency') == 'expert')
    if years > 0 and expert_skills >= 8 and (expert_skills / max(years, 0.5)) > 3:
        return True

    return False


# ── Programmatic Fact-Based Reasoning Generator ──────────────────
def generate_reasoning(c, keywords, score_tier, rank):
    profile = c.get('profile', {})
    name = profile.get('anonymized_name') or 'Candidate'
    title = profile.get('current_title') or 'Professional'
    years = profile.get('years_of_experience', 0) or 0

    signals = c.get('redrob_signals', {})

    # Count skills with assessment scores — these are "verified/core" skills
    skill_scores = signals.get('skill_assessment_scores', {})
    if isinstance(skill_scores, dict):
        assessed_skills_count = len(skill_scores)
    else:
        assessed_skills_count = 0

    # Recruiter response rate
    response_rate = signals.get('recruiter_response_rate', None)

    # Build reasoning in sample submission format
    reasoning = f"{title} with {float(years):.1f} yrs; {assessed_skills_count} assessed skills"

    if response_rate is not None:
        reasoning += f"; recruiter response rate {float(response_rate):.2f}"

    # Add skill match note for top candidates
    cand_skills = [s.get('name', '') for s in c.get('skills', [])]
    matching = [s for s in cand_skills if s.lower() in keywords]
    if matching and rank <= 20:
        reasoning += f"; matches: {', '.join(matching[:2])}"
    elif not matching and rank > 50:
        reasoning += f"; limited overlap with role requirements"

    reasoning += "."
    return reasoning


# ── Main Generator Pipeline ──────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="RankAI Hackathon Submission Generator")
    parser.add_argument("--jd", type=str, default=DEFAULT_JD, help="Job description text")
    parser.add_argument("--id", type=str, required=True, help="Your Hackathon Team/Participant ID")
    args = parser.parse_args()

    jd_text = args.jd
    participant_id = args.id

    print(f"Initializing submission generation for Team ID: {participant_id}")

    # Extract keywords FROM THE ACTUAL JD PASSED IN — not hardcoded
    keywords = extract_jd_keywords(jd_text)
    print(f"JD keywords detected: {keywords}")
    if not keywords:
        print("WARNING: no recognised skill keywords found in this JD. "
              "Reasoning will rely on semantic similarity framing only. "
              "Consider extending SKILL_VOCAB.")

    # 1. Load candidates from JSONL
    print("Loading candidates database...")
    candidates = []
    honeypots_count = 0

    with open('data/candidates.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                c = json.loads(line)
                if is_honeypot(c):
                    honeypots_count += 1
                    continue
                candidates.append(c)

    print(f"Loaded {len(candidates)} valid candidates. Filtered out {honeypots_count} honeypot candidates.")

    if not candidates:
        print("Error: No matching candidates found.")
        sys.exit(1)

    # 2. Build candidate profile texts
    print("Building candidate profile texts...")
    from data.preprocess import build_profile_text
    profile_texts = [build_profile_text(c) for c in candidates]

    # 3. Fast TF-IDF pre-ranking to select top 1000 candidates
    print("Running fast TF-IDF pre-ranking on full candidate pool...")
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(profile_texts)
    jd_vector = vectorizer.transform([jd_text])

    tfidf_scores = cosine_similarity(tfidf_matrix, jd_vector).flatten()
    top_1000_indices = np.argsort(tfidf_scores)[::-1][:1000]

    filtered_candidates = [candidates[idx] for idx in top_1000_indices]
    filtered_profile_texts = [profile_texts[idx] for idx in top_1000_indices]
    print(f"Filtered down to top {len(filtered_candidates)} candidates using TF-IDF.")

    # 4. Local Embedding Semantic Scoring (Zero network calls)
    print("Computing semantic embeddings for top 1000 candidates...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    jd_emb = model.encode([jd_text])[0]
    cand_embs = model.encode(filtered_profile_texts, show_progress_bar=True, batch_size=64)

    # 5. Combine semantic similarity with an explicit skill-overlap bonus.
    #    Pure embedding similarity tends to cluster narrowly (as you saw:
    #    a ~4.5 point spread). Adding a real keyword-overlap signal makes
    #    scores actually differentiate strong vs weak matches.
    print("Calculating composite match scores (semantic + skill overlap)...")
    scores = []
    for idx, cand_emb in enumerate(cand_embs):
        similarity = np.dot(jd_emb, cand_emb) / (np.linalg.norm(jd_emb) * np.linalg.norm(cand_emb))

        c = filtered_candidates[idx]
        cand_skills_lower = [s.get('name', '').lower() for s in c.get('skills', [])]
        overlap = len(set(keywords) & set(cand_skills_lower))
        overlap_ratio = overlap / max(len(keywords), 1)

        # Composite: 70% semantic similarity + 30% explicit skill overlap.
        # This keeps embeddings as the primary signal (handles synonyms,
        # paraphrasing) while still rewarding literal keyword matches that
        # a recruiter would sanity-check first.
        composite = 0.70 * similarity + 0.30 * overlap_ratio
        scores.append((c, composite, similarity, overlap_ratio))

    # 6. Sort and take top 100
    scores.sort(key=lambda x: x[1], reverse=True)
    top_100 = scores[:100]

    # Score matches sample_submission.csv format exactly:
    # score = 1.0000 - (rank * 0.0080)
    # Rank 1 = 0.9920, Rank 100 = 0.2000
    formatted_results = []
    for rank_idx, (c, composite, sim, overlap_ratio) in enumerate(top_100):
        rank = rank_idx + 1
        score = round(1.0000 - (rank * 0.0080), 4)
        score_tier = 'high' if rank <= 20 else 'mid' if rank <= 60 else 'low'
        reasoning = generate_reasoning(c, keywords, score_tier, rank)
        formatted_results.append({
            'candidate_id': c.get('candidate_id'),
            'rank': rank,
            'score': score,
            'reasoning': reasoning
        })

    # 8. Write to CSV file named <participant_id>.csv
    output_filename = f"{participant_id}.csv"
    print(f"Writing rankings to {output_filename}...")

    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['candidate_id', 'rank', 'score', 'reasoning']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in formatted_results:
            writer.writerow(row)

    print(f"Success! Generated exactly {len(formatted_results)} rows in {output_filename}")
    print(f"Score range in output: {min(r['score'] for r in formatted_results):.2f} "
          f"to {max(r['score'] for r in formatted_results):.2f}")


if __name__ == '__main__':
    main()