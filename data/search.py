import chromadb
from sentence_transformers import SentenceTransformer
import os

MODEL_NAME = 'all-MiniLM-L6-v2'
_model      = None
_collection = None
_indexed    = False

def get_model():
    global _model
    if _model is None:
        print('Loading embedding model...')
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def build_index(df, profile_texts: list, ids: list):
    """
    Builds the ChromaDB search index from candidate profiles.
    Call this once before searching.
    """
    global _collection, _indexed
    if _indexed:
        return

    print(f'Building search index for {len(ids)} candidates...')
    client     = chromadb.Client()
    _collection = client.get_or_create_collection(
        name='candidates',
        metadata={'hnsw:space': 'cosine'}
    )

    model = get_model()

    # Process in batches to avoid memory issues with large datasets
    batch_size = 100
    for i in range(0, len(profile_texts), batch_size):
        batch_texts = profile_texts[i:i+batch_size]
        batch_ids   = [str(id_) for id_ in ids[i:i+batch_size]]
        batch_embs  = model.encode(batch_texts).tolist()
        _collection.add(
            documents=batch_texts,
            ids=batch_ids,
            embeddings=batch_embs
        )
        print(f'  Indexed {min(i+batch_size, len(ids))}/{len(ids)}...')

    _indexed = True
    print(f'Index ready!')


def find_top_candidates(jd_text: str, n: int = 20) -> list:
    """
    Takes a job description string.
    Returns top N most similar candidates as a list of dicts.
    Each dict has: id, text, score
    """
    global _collection
    if not _indexed or _collection is None:
        raise RuntimeError(
            'Index not built yet. Call build_index() first.'
        )

    model     = get_model()
    jd_emb    = model.encode([jd_text]).tolist()
    results   = _collection.query(
        query_embeddings=jd_emb,
        n_results=min(n, _collection.count())
    )

    candidates = []
    for id_, doc, dist in zip(
        results['ids'][0],
        results['documents'][0],
        results['distances'][0]
    ):
        candidates.append({
            'id':    id_,
            'text':  doc,
            'score': round(1 - dist, 4)   # convert distance to similarity
        })

    return candidates


if __name__ == '__main__':
    from data.loader import load_sample
    from data.preprocess import build_profile_text

    print('=== Testing search with sample data ===\n')

    # Load candidates
    df     = load_sample()
    texts  = [build_profile_text(row) for _, row in df.iterrows()]
    ids    = df['id'].tolist()

    # Build index
    build_index(df, texts, ids)

    # Test search with a job description
    test_jd = """
    We are looking for a Senior Python Developer with 4+ years of experience.
    Must have strong skills in Django, REST APIs, and PostgreSQL.
    Experience with AWS and Docker is a plus.
    """

    print(f'\nSearching for: Senior Python Developer\n')
    results = find_top_candidates(test_jd, n=5)

    print('Top 5 matches:')
    for i, r in enumerate(results):
        print(f'\n#{i+1} (similarity: {r["score"]})')
        print(f'   {r["text"][:150]}...')

    print('\nSearch is working!')