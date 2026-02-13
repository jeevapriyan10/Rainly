# Rainly
AI-Powered Real-Time Flood Detection System

A comprehensive flood monitoring platform powered by Local LLMs (Qwen) and Google Gemini for real-time risk analysis, automated alerting, and scenario simulation across Indian river basins.

## Features

- **AI-Powered Analysis**: Intelligent flood risk prediction using sensor data (Water Level, Rainfall, Flow Rate) with confidence scoring.
- **Real-Time Monitoring**: Live WebSocket-driven dashboard updating instantly as sensor data changes.
- **Smart Alerts**: Automated Email & SMS notifications for "CRITICAL" risks with a 30-minute anti-spam cooldown.
- **Dual AI Engine**: Supports both **Offline Local Models** (Qwen 0.5B via `llama.cpp`) and **Cloud AI** (Google Gemini).
- **Simulation Engine**: Robust simulator to test scenarios manually or run continuous live data streams.
- **Interactive Dashboard**: Visual analytics with charts, maps, and status indicators.
- **Responsive Design**: Modern UI capable of displaying complex data clearly on any device.

## Tech Stack

**Backend:**
- Python + FastAPI
- MongoDB (Motor AsyncIO)
- WebSockets (Real-time updates)
- Llama.cpp (Local AI) / Google GenAI SDK
- Twilio & SMTP (Notifications)

**Frontend:**
- React 18
- Recharts (Data Visualization)
- Axios & WebSocket API
- Modern CSS (Custom styled components)

## Project Structure

```
Rainly/
├── backend/                    # FastAPI Server
│   ├── models/                # Pydantic Schemas
│   ├── main.py                # API Entry Point & Routes
│   ├── simulation_engine.py   # Core Logic & State Machine
│   ├── llm_service.py         # AI Wrapper (Local/Cloud)
│   ├── notify.py              # Email/SMS Service
│   ├── predictor.py           # Mathematical Risk Models
│   ├── db.py                  # Database Connection
│   └── requirements.txt
│
├── frontend/                   # React Application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboardtab.js    # Main Overview
│   │   │   ├── SimulatorTab.js    # Simulation Controls
│   │   │   ├── AnalyticsTab.js    # History & Charts
│   │   │   └── Header.js          # Navigation
│   │   ├── styles/                # CSS Files
│   │   ├── App.js                 # Layout & Routing
│   │   └── api.js                 # API Integration
│   ├── public/
│   └── package.json
│
├── README.md
└── DEPLOYMENT_INSTRUCTIONS.md
```

## Quick Start

### Prerequisites
- Python >= 3.10
- Node.js >= 18.0.0
- MongoDB Atlas URI
- (Optional) Google Gemini API Key

### Installation

#### Backend Setup
```bash
cd backend
# Create virtual environment (optional but recommended)
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate

pip install -r requirements.txt

# Create .env file
# Copy the format below into a new .env file
```

#### Frontend Setup
```bash
cd frontend
npm install

# Start the development server
npm start
```

### Running Locally

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload
# Server runs on http://127.0.0.1:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
# App runs on http://localhost:3000
```

## Environment Variables

### Backend (.env):
```env
# Database
MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority

# AI Configuration
LLM_PROVIDER=google          # 'google' or 'local'
GEMINI_API_KEY=AIzaSy...     # Required if provider is google
LLM_ENABLED=true

# Notifications (Optional)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

## Usage Guide

### 1. Real-Time Dashboard
1. Open the app to see an overview of all River Basins (Ganges, Yamuna, etc.).
2. Cards display live **Water Levels**, **Rainfall**, and **Risk Status**.
3. **AI Analysis** box appears automatically when high risks are detected.

### 2. Simulator (Testing)
1. Navigate to the **"Simulator"** tab.
2. **Manual Simulation**:
   - Select a target device/region.
   - Enter test values (e.g., Water Level: 305m).
   - Click **"Test Scenario"** to trigger an instant analysis and alert.
3. **Continuous Simulation**:
   - Select a device and click **"Start Live Simulation"**.
   - The system will auto-generate accurate sensor data variations.
   - Watch the dashboard update in real-time.

### 3. Verification & Alerts
1. When a simulation creates a **"CRITICAL"** risk level (Water Level > Threshold):
   - The dashboard turns Red.
   - AI generates a formal warning message.
   - An Email/SMS is dispatched to registered participants (subject to 30m cooldown).

## AI Features Explained

### Smart Risk Prediction
The system uses a hybrid approach:
1. **Mathematical Heuristics**: Immediate threshold checking for instant feedback.
2. **AI Verification**: The LLM analyzes the context (Location, Historic Data, Flow Rate trends) to generate a detailed, human-readable situation report and safety advice.

### Prompt Engineering
The AI is strictly conditioned to act as the **"Rainly Flood Control Room"**. It generates formal, authoritative alerts suitable for emergency broadcasts, avoiding casual language or roleplay.

## Security Features

- **Input Sanitization**: All sensor data is validated before processing.
- **Rate Limiting**: Email/SMS cool-downs prevent alert fatigue and API spam.
- **Environment Isolation**: API Keys managed via `.env` files.
- **CORS Configured**: Strict origin policies for API access.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-sensor`)
3. Commit changes (`git commit -m 'Add new sensor type'`)
4. Push to branch (`git push origin feature/new-sensor`)
5. Open Pull Request

## License

MIT License

Created by [Jeeva Priyan R](https://github.com/jeevapriyan10)
