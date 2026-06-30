# RankAI - AI Candidate Ranker

RankAI is a candidate screening and intelligence platform that evaluates candidate profiles against job requirements using LLMs. It assists recruiters in filtering, sorting, and analyzing matches to fast-track hiring.

---

## Key Features

- **AI-Powered Screening & Scoring**: Extracts requirements from a job description and scores candidates based on **Skills**, **Experience**, and **Growth Trajectory**.
- **Candidate Side-by-Side Comparison Matrix**: Select up to 3 candidates and compare their alignment, skills, and AI decision rationale side-by-side.
- **Dynamic Sorting & Filtering**: Sort matches instantly by overall score or specific sub-metrics. Filter candidates by keyword search or score threshold matches.
- **Job Description Preset Chips**: One-click quick presets to test backend, frontend, or data science requirements.
- **Spreadsheet & Document Exports**: Download full evaluations and job description metadata directly as Excel (`.xlsx`) spreadsheets or print-ready PDF reports.

---

## Technical Stack

- **Frontend**: Vanilla HTML5, CSS3, JavaScript.
  - *Excel Engine*: SheetJS (via CDN).
  - *PDF Engine*: html2pdf.js (via CDN).
- **Backend API**: Flask server.
- **LLM Provider**: Groq API (`llama-3.3-70b-versatile` model).
- **Static Hosting & Proxy Server**: Express (Node.js) proxying API requests to the Flask backend.

---

## Setup & Run Instructions

### 1. Environment Configuration
Create a `.env` file in the root directory and add your Groq API key:
```env
GROQ_API_KEY=your_actual_groq_api_key
```

### 2. Run the Backend API
Install python dependencies and run the Flask server:
```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask backend
python -m backend.api
```
*The backend API will run on `http://localhost:5000`.*

### 3. Run the Frontend UI
Navigate to the `ui` folder, install Node modules, and start the Express server:
```bash
# Go to UI folder
cd ui

# Install dependencies
npm install

# Start Express server
npm start
```
*The static client UI server will run on `http://localhost:3000`.*

### 4. Access the Application
Open your web browser and navigate to:
👉 **`http://localhost:3000`**
