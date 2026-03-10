## ATS-Aware Resume Intelligence & Rewriting System

An intelligent, ATS-aware resume analysis system that compares a resume against a job description, computes an ATS compatibility score, and provides explainable feedback and rewriting suggestions using semantic matching and NLP.

### Features

- **Resume upload & parsing**: Upload PDF resumes; text is extracted with `pdfplumber`.
- **Text preprocessing**: Tokenization, stopword removal, and lemmatization via **spaCy** and **NLTK**.
- **Skill extraction**: Dictionary-based detection of technical skills from resume text.
- **Job description input**: Paste job description text and (optionally) explicit required skills.
- **Semantic matching**: Sentence-BERT (`all-MiniLM-L6-v2`) embeddings with cosine similarity.
- **ATS scoring**: Combines semantic similarity, skill match percentage, and keyword relevance into a 0–100 score.
- **Explainable feedback**: Matched/missing skills and keywords, plus narrative feedback.
- **Resume rewriting module**: Suggests stronger, clearer bullet-point versions using better action verbs.
- **Streamlit UI**: Simple web app to upload a resume, paste a JD, and view insights.

### Project Structure

- `resume_parser.py`: PDF text extraction using `pdfplumber`.
- `preprocessing.py`: NLP preprocessing helpers (tokenization, stopword removal, lemmatization).
- `skill_extraction.py`: Dictionary-based skill extraction and skill match analysis.
- `semantic_matching.py`: Sentence-BERT semantic similarity between resume and job description.
- `ats_scoring.py`: ATS score calculation and explanation breakdown data structure.
- `rewriting_module.py`: Bullet-point splitting and rewrite suggestion generation.
- `app.py`: Streamlit web application entry point.
- `requirements.txt`: Python dependencies.

### Installation

1. **Create and activate a virtual environment (recommended)**

   ```bash
   cd d:\NLP
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Download the spaCy English model**

   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **(Optional) Pre-download NLTK stopwords**

   The app will download these automatically on first run if missing, but you can do it up front:

   ```bash
   python -c "import nltk; nltk.download('stopwords')"
   ```

### Running the Streamlit Application

From the project root (`d:\NLP`) with your virtual environment activated:

```bash
streamlit run app.py
```

This will open the Streamlit app in your browser.

### Usage

1. **Upload Resume**
   - Upload your resume as a **PDF** file.
   - The app extracts the text and shows a preview.

2. **Paste Job Description**
   - Paste the full job description text into the text area.

3. **Specify Required Skills (Optional)**
   - Optionally list required skills as comma- or newline-separated values.
   - If left blank, the system infers skills from the job description using the same skill dictionary used for resumes.

4. **Run Analysis**
   - Click **"Analyze Resume"**.
   - The app computes:
     - **ATS Score (0–100)**
     - **Semantic similarity** between resume and job description
     - **Skill match percentage**
     - **Keyword relevance**
     - **Matched and missing skills**
     - **Matched and missing high-value keywords**
   - It also generates **rewrite suggestions** for weak bullet points.

### Notes & Limitations

- **Heuristic skill extraction**: Uses a predefined dictionary of common technical skills. You can extend `DEFAULT_SKILL_DICTIONARY` in `skill_extraction.py` as needed.
- **Heuristic rewriting**: The rewriting module uses rules and verb lists rather than generative models to keep execution lightweight and local.
- **Model downloads**:
  - `sentence-transformers` will download the `all-MiniLM-L6-v2` model the first time it is used.
  - `spaCy` and `NLTK` require language resources as described above.

