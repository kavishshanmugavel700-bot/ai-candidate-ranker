from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.ranker import rank_candidates, init

app = Flask(__name__)
CORS(app)

# Load data and build index when server starts
print('Initialising AI Candidate Ranker...')
init(use_full_dataset=False)  # change to True when ready for full dataset
print('Server ready!')

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'running',
        'message': 'AI Candidate Ranker API',
        'endpoints': {
            'POST /rank': 'Rank candidates for a job description'
        }
    })

@app.route('/rank', methods=['POST'])
def rank():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data sent'}), 400

    jd_text = data.get('job_description', '').strip()

    if not jd_text:
        return jsonify({'error': 'job_description is required'}), 400

    try:
        results = rank_candidates(jd_text, top_n=10)
        return jsonify({
            'success': True,
            'total_found': len(results),
            'candidates': results
        })
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=False)