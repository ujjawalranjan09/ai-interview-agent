# 🎯 AI Multimodal Interview Agent

An AI-powered interview system that conducts adaptive technical interviews with real-time emotion analysis, voice evaluation, and comprehensive performance reports.

## Features

- **📄 Resume Parsing** - Extract skills, projects, and candidate info from PDF resumes
- **🧠 Adaptive Difficulty** - Questions adjust based on answer performance (Easy → Medium → Hard → Expert)
- **🎤 Voice Input** - Answer questions via microphone with Whisper speech-to-text
- **🔊 Text-to-Speech** - Questions read aloud using gTTS/pyttsx3
- **📹 Facial Emotion Detection** - Real-time emotion analysis via DeepFace
- **🎙️ Voice Emotion Analysis** - Pitch, speed, and hesitation detection via librosa
- **📊 Multimodal Confidence Scoring** - Combined facial (50%) + voice (30%) + fluency (20%)
- **📈 7 Visualization Charts** - Bar, line, area, radar, pie, step, and grouped bar charts
- **📄 PDF Report Generation** - Comprehensive multi-page reports with FPDF2
- **🔄 Interview Replay** - Review past interviews with emotion timeline
- **💾 MongoDB Storage** - Persistent storage of all interview data

## Architecture

```
project_root/
├── app/                    # Application entry & config
│   ├── main.py             # Streamlit entry point
│   ├── config.py           # Environment configuration
│   └── constants.py        # Constants & prompt templates
├── modules/
│   ├── orchestrator/       # Interview flow control
│   ├── resume/             # PDF parsing & skill extraction
│   ├── questions/          # Question generation & difficulty
│   ├── voice/              # STT, TTS, voice emotion
│   ├── video/              # Camera & facial emotion
│   ├── evaluation/         # Answer scoring & confidence
│   ├── analytics/          # Performance metrics & charts
│   └── report/             # Feedback, PDF, replay
├── database/               # MongoDB models & queries
├── frontend/               # Streamlit pages & components
├── tests/                  # Unit tests
├── outputs/                # Generated reports & recordings
└── assets/                 # Sample resumes & references
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Database | MongoDB (pymongo) |
| NLP | sentence-transformers, spaCy |
| Speech | OpenAI Whisper, gTTS/pyttsx3 |
| Video | OpenCV, DeepFace |
| Audio Analysis | librosa |
| Charts | Plotly |
| PDF | FPDF2 |
| Graph | NetworkX |
| Resume Parsing | pdfplumber/PyPDF2 |

## Scoring System

### Answer Score (0-100)
```
Score = 0.4 × Semantic + 0.3 × Keywords + 0.3 × Concepts + Modifiers
```

### Confidence Score (0-100)
```
Confidence = 0.5 × Facial + 0.3 × Voice Tone + 0.2 × Fluency
```

### Adaptive Difficulty
- Starts at **Medium** (Level 2)
- Rolling average of last 3 answers:
  - ≥85 → Harder
  - 60-84 → Same
  - 40-59 → Easier
  - <40 → Easy

### Question Distribution
- 40% Resume-based
- 40% Technical
- 20% Behavioral

## Quick Start

### Option 1: Local Setup

```bash
# Clone the repository
git clone https://github.com/your-username/ai-interview-agent.git
cd ai-interview-agent

# Run setup script
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Ensure MongoDB is running
mongod --dbpath /path/to/data

# Run the application
streamlit run app/main.py
```

### Option 2: Docker

```bash
# Clone the repository
git clone https://github.com/your-username/ai-interview-agent.git
cd ai-interview-agent

# Start with Docker Compose
docker-compose up --build

# Access at http://localhost:8501
```

## Configuration

Edit `.env` to configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection URI |
| `OPENAI_API_KEY` | - | OpenAI API key (optional, for LLM features) |
| `WHISPER_MODEL` | `base` | Whisper model size (tiny/base/small/medium/large) |
| `TTS_ENGINE` | `gtts` | TTS engine (gtts/pyttsx3) |
| `DEFAULT_QUESTIONS_COUNT` | `10` | Number of interview questions |

## Interview Flow

```
IDLE → RESUME_PROCESSING → READY → INTRODUCTION → ASKING_QUESTION
→ LISTENING → PROCESSING_ANSWER → [GENERATING_FOLLOWUP → ASKING_FOLLOWUP]
→ SELECTING_NEXT_QUESTION → CLOSING → GENERATING_REPORT → COMPLETED
```

## API Reference

### Key Classes

- `InterviewController` - Main interview orchestrator
- `StateMachine` - Interview state transitions
- `SessionManager` - Session lifecycle management
- `DifficultyManager` - Adaptive difficulty adjustment
- `EmotionTracker` - Temporal emotion smoothing

### Key Functions

- `generate_questions()` - Generate interview questions
- `evaluate_answer()` - Score candidate answers
- `calculate_confidence()` - Multimodal confidence calculation
- `transcribe_audio()` - Whisper STT
- `generate_pdf_report()` - PDF report generation

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_evaluation.py -v

# Run with coverage
pip install pytest-cov
python -m pytest tests/ --cov=modules --cov-report=html
```

## Project Structure Details

### Database Schema

**candidates** collection:
- `name`, `email`, `resume_path`
- `extracted_skills[]`, `extracted_projects[]`
- `skill_graph{}`

**interviews** collection:
- `candidate_id`, `status`, `difficulty_level`
- `start_time`, `end_time`, `total_score`
- `final_feedback{}`

**questions** collection:
- `interview_id`, `question_text`, `question_type`
- `difficulty`, `candidate_answer_text`
- `answer_score`, `semantic_similarity_score`
- `keyword_match_score`, `concept_coverage_score`
- `follow_up_questions[]`

**emotion_timeline** collection:
- `interview_id`, `timestamp`
- `facial_emotion`, `facial_confidence_score`
- `voice_emotion`, `voice_pitch`, `speaking_speed`
- `hesitation_detected`, `combined_confidence_score`

**reports** collection:
- `interview_id`, `pdf_path`
- `strengths[]`, `weaknesses[]`, `suggestions[]`
- `graphs{}`, `overall_assessment`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- OpenAI Whisper for speech recognition
- DeepFace for facial emotion analysis
- Streamlit for the web interface
- Plotly for interactive visualizations
