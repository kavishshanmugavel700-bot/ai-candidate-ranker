from sentence_transformers import SentenceTransformer
import numpy as np
import os

MODEL_NAME = 'all-MiniLM-L6-v2'
CACHE_PATH = 'data/embeddings.npy'
IDS_CACHE  = 'data/embedding_ids.npy'

def get_embeddings(texts: list, ids: list):
    """
    Creates embeddings for all profile texts.
    Saves to file so we don't recompute every time.
    Returns (embeddings, ids)
    """
    if os.path.exists(CACHE_PATH) and os.path.exists(IDS_CACHE):
        print('Loading cached embeddings...')
        embeddings = np.load(CACHE_PATH)
        cached_ids = np.load(IDS_CACHE, allow_pickle=True).tolist()
        print(f'Loaded {len(embeddings)} cached embeddings')
        return embeddings, cached_ids

    print(f'Computing embeddings for {len(texts)} candidates...')
    print('This takes 2-5 minutes the first time. Please wait...')
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    np.save(CACHE_PATH, embeddings)
    np.save(IDS_CACHE, np.array(ids, dtype=object))
    print(f'Done! Saved {len(embeddings)} embeddings to {CACHE_PATH}')
    return embeddings, ids


if __name__ == '__main__':
    from data.loader import load_sample
    from data.preprocess import build_profile_text

    print('=== Testing embedder with sample data ===')
    df = load_sample()
    texts = [build_profile_text(row) for _, row in df.iterrows()]
    ids   = df['id'].tolist()

    print(f'\nBuilding embeddings for {len(texts)} candidates...')
    embeddings, ids = get_embeddings(texts, ids)
    print(f'Embeddings shape: {embeddings.shape}')
    print(f'Each candidate is now a vector of {embeddings.shape[1]} numbers')
    print('Embedder is working correctly!')