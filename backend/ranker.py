import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.loader import load_candidates, load_sample
from data.preprocess import build_profile_text
from data.search import build_index, find_top_candidates
from backend.jd_extractor import extract_jd_requirements
from backend.scorer import score_candidate
import pandas as pd

# Global variables — loaded once at startup
_df     = None
_indexed = False

def init(use_full_dataset=False):
    """Load data and build search index. Call once at startup."""
    global _df, _indexed
    if _indexed:
        return

    print('Loading candidates...')
    if use_full_dataset:
        _df = load_candidates()
    else:
        _df = load_sample()

    texts = [build_profile_text(row) for _, row in _df.iterrows()]
    ids   = _df['id'].tolist()

    print('Building search index...')
    build_index(_df, texts, ids)
    _indexed = True
    print(f'Ready! {len(_df)} candidates indexed.')


def rank_candidates(jd_text: str, top_n: int = 10) -> list:
    """
    Main function. Takes job description text.
    Returns ranked list of top candidates with scores and reasons.
    """
    global _df

    if not _indexed:
        init()

    print('Extracting JD requirements...')
    jd_req = extract_jd_requirements(jd_text)
    print(f'JD Requirements: {jd_req}')

    print('Searching for top candidates...')
    search_results = find_top_candidates(jd_text, n=20)
    print(f'Found {len(search_results)} candidates to score')

    # Get full candidate data for each search result
    candidates_to_score = []
    for r in search_results:
        candidate_id = r['id']
        row = _df[_df['id'] == candidate_id]
        if not row.empty:
            candidate = row.iloc[0].to_dict()
            candidates_to_score.append(candidate)

    print(f'Scoring {len(candidates_to_score)} candidates with AI...')
    scored = []
    for i, candidate in enumerate(candidates_to_score):
        print(f'  Scoring candidate {i+1}/{len(candidates_to_score)}...')
        score = score_candidate(candidate, jd_req)
        scored.append(score)

    # Sort by total score descending
    scored.sort(key=lambda x: x.get('total_score', 0), reverse=True)

    return scored[:top_n]


if __name__ == '__main__':
    print('=== Testing full ranking pipeline ===\n')
    init()

    test_jd = """
    We are looking for a Senior Python Developer with 5+ years of experience.
    Must know Django, REST APIs, PostgreSQL and AWS.
    Strong communication and teamwork skills required.
    """

    results = rank_candidates(test_jd, top_n=5)

    print('\n=== TOP 5 CANDIDATES ===\n')
    for i, r in enumerate(results):
        print(f"#{i+1} {r.get('name', 'Unknown')} — Score: {r.get('total_score', 0)}/100")
        print(f"     Reason: {r.get('reason', '')}")
        print()