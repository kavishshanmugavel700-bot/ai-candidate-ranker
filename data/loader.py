import pandas as pd
import json

def load_candidates(path='data/candidates.jsonl') -> pd.DataFrame:
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    df = pd.DataFrame(records)
    df = df.fillna('')
    df['id'] = df.index.astype(str)
    print(f'Loaded {len(df)} candidates')
    return df

def load_sample(path='data/sample_candidates.json') -> pd.DataFrame:
    with open(path, 'r', encoding='utf-8') as f:
        records = json.load(f)
    if isinstance(records, dict):
        records = list(records.values())
    df = pd.DataFrame(records)
    df = df.fillna('')
    df['id'] = df.index.astype(str)
    print(f'Loaded {len(df)} sample candidates')
    return df

if __name__ == '__main__':
    print("=== Loading sample candidates ===")
    df = load_sample()
    print(f'\nColumn names: {df.columns.tolist()}')
    print(f'\nFirst candidate:')
    print(json.dumps(df.iloc[0].to_dict(), indent=2, default=str))