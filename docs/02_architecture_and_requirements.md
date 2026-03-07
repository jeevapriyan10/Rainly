# Rainly - Early Flood Detection System
## Document 2: Architecture and Requirements

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Component Architecture](#component-architecture)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Database Architecture](#database-architecture)
6. [Real-Time Communication Architecture](#real-time-communication-architecture)
7. [Notification Architecture](#notification-architecture)
8. [LLM Integration Architecture](#llm-integration-architecture)
9. [Data Flow Diagrams](#data-flow-diagrams)
10. [System Requirements](#system-requirements)
11. [Environment Configuration Requirements](#environment-configuration-requirements)
12. [Security Considerations](#security-considerations)

---

## High-Level Architecture

Rainly follows a classic three-tier client-server architecture with a dedicated real-time communication layer. The three tiers are:

1. **Presentation Tier**: A React single-page application served as a static build. The frontend communicates with the backend through both HTTP REST calls and a persistent WebSocket connection.

2. **Application Tier**: A FastAPI-based Python backend that handles all business logic including data ingestion, flood risk prediction, notification dispatch, simulation orchestration, and WebSocket broadcasting.

3. **Data Tier**: A MongoDB database accessed asynchronously through the Motor driver. All application state, including region configurations, device registrations, participant records, and historical warning logs, is persisted here.

```
+---------------------------+
|     React Frontend        |
|  (Static Site / Browser)  |
|                           |
|  - REST API Calls (HTTP)  |
|  - WebSocket Connection   |
+------------+--------------+
             |
             | HTTP / WebSocket
             |
+------------+--------------+
|    FastAPI Backend        |
|                           |
|  - REST API Routes        |
|  - WebSocket Manager      |
|  - Prediction Engine      |
|  - Simulation Engine      |
|  - Notification Service   |
|  - LLM Service            |
+------------+--------------+
             |
             | Motor (Async)
             |
+------------+--------------+
|     MongoDB Database      |
|                           |
|  Collections:             |
|  - regions                |
|  - devices                |
|  - participants           |
|  - warnings               |
+---------------------------+
```

---

## Component Architecture

The system is divided into the following discrete components, each maintained in its own source file:

### Backend Components

| File | Responsibility |
|------|---------------|
| `main.py` | Application entry point, CORS configuration, lifespan management, REST endpoint definitions, WebSocket endpoint, database auto-seeding |
| `db.py` | MongoDB connection lifecycle management (`connect_db`, `close_db`, `get_db`) |
| `models.py` | Pydantic data models for all domain entities and request/response schemas |
| `predictor.py` | Rule-based flood risk scoring and classification logic |
| `simulation_engine.py` | Asynchronous real-time simulation loop, trend-based sensor value evolution, per-device task management |
| `websocket_manager.py` | WebSocket connection registry, broadcast methods, device data caching |
| `notify.py` | SMS and Email notification formatting and dispatch |
| `llm_service.py` | LLM provider initialization, prompt construction, inference execution, fallback handling |
| `download_model.py` | CLI utility for downloading GGUF model files from Hugging Face |

### Frontend Components

| File | Responsibility |
|------|---------------|
| `App.js` | Root component, React Router configuration, route-to-component mapping |
| `api.js` | Centralized HTTP client functions for all REST endpoints |
| `hooks/useWebSocket.js` | Custom React hook for WebSocket connection management, reconnection logic, message parsing, and alert state |
| `components/NavBar.js` | Top navigation bar with links to all major sections |
| `components/Dashboard.js` | System overview, statistics cards, risk distribution chart, warnings table |
| `components/MapTab.js` | Interactive Leaflet map, region markers with risk-coded colors, popover tooltips |
| `components/RegionsTab.js` | Region listing, risk level badges, region creation form |
| `components/DevicesTab.js` | Device listing, battery indicators, active/inactive toggle, device creation |
| `components/ParticipantsTab.js` | Participant listing, warning history per participant, participant creation |
| `components/AnalyticsTab.js` | Advanced analytics charts, trend visualization, warning frequency breakdown |
| `components/SimulatorTab.js` | Real-time simulation control panel, trend configuration, live sensor readout |

---

## Backend Architecture

### Application Entry Point and Lifespan Management

The FastAPI application uses the `asynccontextmanager` pattern for startup and shutdown lifecycle management. On startup, the application:

1. Establishes the MongoDB connection via `connect_db()`.
2. Checks whether the database is empty and, if so, executes `seed_database()` to populate regions, devices, participants, and sample warnings.
3. If the LLM provider is set to `local`, the application checks for the presence of the configured GGUF model file on disk and triggers an automatic download if the file is not found.

On shutdown, the application calls `close_db()` to close the MongoDB connection cleanly.

### Request Routing Layer

All REST routes are mounted under the `/api` prefix. The WebSocket endpoint is mounted at `/ws/realtime`. A root health check endpoint is available at `/`. The CORS middleware is configured to allow requests from all origins, which is appropriate for a deployment where the frontend and backend may be hosted on different domains.

### Middleware

The application applies a single middleware layer:

- **CORSMiddleware**: Configured with `allow_origins=["*"]`, `allow_credentials=True`, `allow_methods=["*"]`, and `allow_headers=["*"]`. This open CORS configuration facilitates development and cross-domain production deployments. Production deployments should restrict origins to the known frontend domain.

### Prediction Engine Design

The prediction engine in `predictor.py` is designed with a clear architectural intent: it is a thin, fast, synchronous function. The design decision to keep the primary prediction path rule-based (rather than LLM-based) is documented inline:

- Rule-based prediction executes in microseconds and can handle high-frequency sensor ticks.
- LLM inference takes hundreds of milliseconds to seconds and is therefore reserved for background tasks: generating reasoning explanations during simulation and composing email bodies for notifications.

This separation ensures the main event loop is never blocked waiting for LLM inference, maintaining the responsiveness of the WebSocket broadcast pipeline.

### Asynchronous Concurrency Model

The backend is fully asynchronous. The FastAPI application runs on Uvicorn's async event loop. All database operations use Motor's async interface. The simulation engine creates separate `asyncio.Task` objects for each active simulation, allowing multiple devices to run concurrent simulation loops without blocking each other or the main API handler. Background tasks created with `asyncio.create_task` handle database writes and notification dispatch, ensuring the WebSocket broadcast fires within the two-second simulation tick budget.

---

## Frontend Architecture

### Single-Page Application Structure

The frontend is a standard Create React App (CRA) project. The `index.js` file mounts the root React component into the HTML DOM. `App.js` wraps all routes in a `BrowserRouter`, enabling client-side navigation without full page reloads. The router is configured with seven routes:

| Route | Component |
|-------|-----------|
| `/` | Dashboard |
| `/map` | MapTab |
| `/regions` | RegionsTab |
| `/devices` | DevicesTab |
| `/participants` | ParticipantsTab |
| `/analytics` | AnalyticsTab |
| `/simulator` | SimulatorTab |

### API Client Layer

The `api.js` module centralizes all HTTP communication. The base URL is derived from the `REACT_APP_API_URL` environment variable at build time, falling back to `http://localhost:8000/api` for local development. Each exported function corresponds to a single API endpoint and returns the parsed JSON response directly.

### WebSocket Hook Architecture

The `useWebSocket` custom hook encapsulates all WebSocket connection logic. Key design decisions:

- **Automatic reconnection**: On `onclose`, a 5-second timeout triggers a new `connect()` call.
- **Ping/Pong keepalive**: A 30-second interval sends `{"type": "ping"}` to the server to prevent idle connection teardown by load balancers or proxies.
- **Protocol selection**: The hook derives the correct WebSocket protocol (`ws:` or `wss:`) from the page's current HTTP protocol, ensuring correct behavior in both development and HTTPS production environments.
- **State management**: The hook exposes `isConnected`, `lastMessage`, `deviceUpdates` (keyed dictionary), and `alerts` (array) as reactive React state, allowing consuming components to re-render automatically when new data arrives over the socket.

---

## Database Architecture

### Collections

The MongoDB database named `flood_detection` contains four collections:

**`regions` Collection**

| Field | Type | Description |
|-------|------|-------------|
| `region_id` | String | Unique region identifier (e.g., `r001`) |
| `name` | String | Human-readable region name |
| `latitude` | Float | Geographic latitude |
| `longitude` | Float | Geographic longitude |
| `river_name` | String | Name of the monitored river |
| `state` | String | Indian state name |
| `district` | String | District name |
| `risk_level` | String | Current risk level: LOW, MEDIUM, HIGH, CRITICAL |

**`devices` Collection**

| Field | Type | Description |
|-------|------|-------------|
| `device_id` | String | Unique device identifier (e.g., `d001`) |
| `region_id` | String | Reference to parent region |
| `name` | String | Human-readable device name |
| `alert_threshold` | Float | Water level (in metres) at which alerts trigger |
| `is_active` | Boolean | Whether the device is operational |
| `last_water_level` | Float/Null | Most recent water level reading |
| `last_rainfall` | Float/Null | Most recent rainfall reading |
| `last_flow_rate` | Float/Null | Most recent flow rate reading |
| `battery_level` | Integer/Null | Battery percentage (0-100) |
| `last_seen` | DateTime/Null | Timestamp of last data reception |

**`participants` Collection**

| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | String (UUID) | Unique participant identifier |
| `name` | String | Full name |
| `age` | Integer | Age in years |
| `phone` | String | Phone number in E.164 format |
| `email` | String | Email address |
| `region_id` | String | Reference to parent region |

**`warnings` Collection**

| Field | Type | Description |
|-------|------|-------------|
| `warning_id` | String (UUID) | Unique warning event identifier |
| `region_id` | String | Reference to affected region |
| `device_id` | String | Reference to triggering device |
| `river_name` | String | Name of the river at time of warning |
| `participant_id` | String | Reference to notified participant |
| `warning_type` | String | Action type: `monitor`, `prepare`, `evacuate` |
| `risk_level` | String | Risk classification at time of warning |
| `timestamp` | DateTime | UTC timestamp of the warning event |
| `water_level` | Float | Water level reading that triggered the warning |
| `rainfall` | Float | Rainfall reading at time of warning |
| `flow_rate` | Float | Flow rate reading at time of warning |

### Indexing Considerations

The current implementation performs document lookups using MongoDB's default `_id` index and queries filtered on `region_id`, `device_id`, and `participant_id`. For production workloads with large warning history datasets, compound indexes on `(region_id, timestamp)` and `(participant_id, timestamp)` are recommended to reduce query latency for the warning history retrieval endpoints.

---

## Real-Time Communication Architecture

The WebSocket layer is implemented using FastAPI's native WebSocket support together with the `websockets` library. The `ConnectionManager` class in `websocket_manager.py` maintains a list of all currently connected WebSocket clients.

### Message Types

The server emits messages in one of three formats:

**Device Update Message**
```json
{
  "type": "device_update",
  "device_id": "d001",
  "data": {
    "water_level": 296.4,
    "rainfall": 48.2,
    "flow_rate": 1235.0,
    "risk_level": "MEDIUM",
    "risk_score": 0.52,
    "alert_threshold": 294.5,
    "llm_status": "idle"
  },
  "timestamp": "2026-02-24T15:30:00.000000"
}
```

**Flood Alert Message**
```json
{
  "type": "flood_alert",
  "data": {
    "region": "Haridwar Region",
    "river": "Ganges",
    "risk_level": "CRITICAL",
    "water_level": 353.8,
    "threshold": 294.5,
    "participants_notified": 2
  },
  "timestamp": "2026-02-24T15:30:00.000000"
}
```

**Warning Generated Message**
```json
{
  "type": "warning_generated",
  "data": { ... },
  "timestamp": "2026-02-24T15:30:00.000000"
}
```

The client sends only two message types to the server: `{"type": "ping"}` for keepalive, and `{"type": "get_status"}` to request a snapshot of active simulations.

---

## Notification Architecture

The notification system in `notify.py` follows a layered, provider-agnostic design:

### Email Provider Hierarchy

1. **Resend API (Primary)**: If `RESEND_API_KEY` is present in the environment, all emails are sent through Resend's transactional email API. Resend is preferred for production use because it offers reliable deliverability without requiring SMTP configuration.

2. **Gmail SMTP (Fallback)**: If Resend is not configured but `GMAIL_ADDRESS` and `GMAIL_PASSWORD` are present, emails are sent via Gmail's SMTP server. The system first attempts port 587 with STARTTLS, then falls back to port 465 with SSL if the initial attempt fails.

3. **Disabled**: If neither provider is configured, email notifications are gracefully skipped and the outcome is logged without raising an exception.

### Email Content Hierarchy

1. **LLM-Generated Content**: If `LLM_ENABLED=true` and the LLM is initialized, the `generate_detailed_warning` function in `llm_service.py` is called inside an `asyncio.to_thread` executor to produce a personalized, context-aware email body without blocking the event loop.

2. **Enhanced Template Fallback**: If LLM generation fails or is disabled, `format_email_alert` in `notify.py` produces a structured HTML email using risk-calibrated static content blocks for causes, timeline, risk description, and recommended actions.

### Alert Rate Limiting

To prevent alert flooding, the simulation engine applies two independent cooldown windows:

- **Per-participant cooldown**: 1,800 seconds (30 minutes). A given participant will not receive more than one alert per device event within this window.
- **Per-device bulk alert cooldown**: 900 seconds (15 minutes). After a bulk alert batch is dispatched for a device, no further batch is sent for that device within this window, regardless of individual participant cooldown states.

---

## LLM Integration Architecture

The `llm_service.py` module uses a module-level singleton pattern to manage the LLM model instance. A threading lock (`_model_lock`) prevents concurrent inference on the local model, which is not thread-safe. When `asyncio.to_thread` calls the synchronous inference function from an async context, the lock ensures only one generation executes at a time.

### Provider Selection Logic

```
LLM_ENABLED=true?
     |
     +-- No  --> Rule-based fallback throughout the system
     |
     +-- Yes --> LLM_PROVIDER check
                    |
                    +-- "google" --> Initialize Gemini Pro via google-generativeai SDK
                    |
                    +-- "local"  --> Load GGUF model via llama-cpp-python
                                     |
                                     +-- Model file exists? No --> Log error, disable LLM
                                     +-- Model file exists? Yes --> Load model, set _model singleton
```

---

## Data Flow Diagrams

### IoT Sensor Data Flow

```
IoT Sensor / Test Client
        |
        | POST /api/simulate
        v
FastAPI Route Handler
        |
        | Lookup device, validate region
        v
Update Device (last_water_level, last_rainfall, last_flow_rate, last_seen)
        |
        v
predict_flood_risk(payload, alert_threshold)
        |
        +--- Return PredictionResult (risk_level, warning_type, risk_score)
        |
        v
For each Participant in Region:
  - Create Warning document -> Insert to MongoDB
  - Call send_flood_alert() -> SMS + Email dispatch
        |
        v
Return { status, prediction, warnings_generated, affected_participants }
```

### Real-Time Simulation Data Flow

```
POST /api/simulation/start
        |
        v
SimulationEngine.start_simulation()
        |
        v
asyncio.create_task(_run_simulation()) --> Background coroutine launched
        |
        v
Every 2 seconds:
  Compute water/rainfall/flow deltas based on trend + speed
  Update active_simulations[device_id] state
  predict_flood_risk() --> PredictionResult
  asyncio.create_task(db.devices.update_one()) --> Non-blocking DB write
  asyncio.create_task(db.regions.update_one()) --> Update region risk level
  If LLM_ENABLED and not processing:
    asyncio.create_task(_process_llm_analysis()) --> Background LLM call
  manager.broadcast_device_update(device_id, update_data) --> WebSocket push
  If CRITICAL: asyncio.create_task(_process_alerts()) --> Background notification batch
  await asyncio.sleep(2)
```

### WebSocket Message Flow to Frontend

```
Server _run_simulation() tick
        |
        v
ConnectionManager.broadcast_device_update()
        |
        | WebSocket JSON frame
        v
Frontend useWebSocket hook
        |
        | message.type === "device_update"
        v
setDeviceUpdates(prev => { ...prev, [device_id]: data })
        |
        v
SimulatorTab / DevicesTab re-renders with new sensor values
```

---

## System Requirements

### Minimum Hardware Requirements (Development)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB |
| Disk Space (without LLM) | 500 MB | 1 GB |
| Disk Space (with local LLM - Qwen) | 1 GB | 2 GB |
| Disk Space (with local LLM - TinyLlama) | 1.5 GB | 2 GB |
| Disk Space (with local LLM - Phi-2) | 2.5 GB | 4 GB |

### Software Requirements

| Software | Version | Notes |
|----------|---------|-------|
| Python | 3.11+ | Required for the backend. Earlier versions are untested. |
| Node.js | 18+ | Required for the frontend build. |
| npm | 9+ | Bundled with Node.js 18+. |
| MongoDB | 6.0+ (Atlas or local) | Atlas free tier is sufficient for development. |

### Python Dependencies (Full)

```
fastapi>=0.110.0
uvicorn>=0.29.0
motor>=3.4.0
pydantic>=2.7.0
python-dotenv>=1.0.0
websockets>=12.0
twilio>=9.0.0
python-multipart>=0.0.9
google-generativeai>=0.4.1
llama-cpp-python>=0.2.70
requests>=2.31.0
tqdm>=4.66.0
```

### Node.js Dependencies (Frontend)

```
react: ^18.2.0
react-dom: ^18.2.0
react-router-dom: ^6.21.1
react-scripts: 5.0.1
leaflet: ^1.9.4
react-leaflet: ^4.2.1
recharts: ^2.10.3
```

---

## Environment Configuration Requirements

The backend reads configuration exclusively from environment variables loaded via `python-dotenv` from a `.env` file placed in the `backend/` directory.

### Required Variables

| Variable | Description |
|----------|-------------|
| `MONGODB_URI` | Full MongoDB connection string, including credentials if using Atlas (e.g., `mongodb+srv://user:pass@cluster.mongodb.net/`) |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_ENABLED` | `false` | Set to `true` to enable LLM features. |
| `LLM_PROVIDER` | `google` | Set to `local` or `google`. |
| `LLM_MODEL_FILE` | `qwen2-0_5b-instruct-q4_k_m.gguf` | GGUF model filename for local inference. |
| `LLM_MODEL_PATH` | `models/llm` | Directory path where GGUF model files are stored. |
| `GEMINI_API_KEY` | - | Google Gemini API key (required if `LLM_PROVIDER=google`). |
| `GMAIL_ADDRESS` | - | Gmail sender address for SMTP email dispatch. |
| `GMAIL_PASSWORD` | - | Gmail App Password (not the account password). |
| `RESEND_API_KEY` | - | Resend transactional email API key (takes priority over Gmail). |
| `TWILIO_ACCOUNT_SID` | - | Twilio Account SID for SMS dispatch. |
| `TWILIO_AUTH_TOKEN` | - | Twilio Authentication Token. |
| `TWILIO_PHONE_NUMBER` | - | Twilio-provisioned sender phone number in E.164 format. |
| `DEV_EMAIL_RECIPIENT` | `yo.heisenberg10@gmail.com` | Override recipient email (used in Resend free-tier development). |

### Frontend Environment Variable

| Variable | Default | Description |
|----------|---------|-------------|
| `REACT_APP_API_URL` | `http://localhost:8000/api` | Backend API base URL. Must be set at build time for production builds. |

---

## Security Considerations

### Current State

- CORS is fully open (`allow_origins=["*"]`). This is intentional for development flexibility but should be restricted to the known frontend origin in production.
- No authentication or authorization layer is implemented. All API endpoints are publicly accessible. This is acceptable for an internal operations tool but should be addressed before public exposure.
- MongoDB credentials are stored in the `.env` file, which is excluded from version control via `.gitignore`. The `.env.example` file provides a template without sensitive values.
- Email credentials (Gmail App Password or Resend API key) are stored in environment variables and never appear in source code.
- Twilio credentials are stored in environment variables and never appear in source code.
- The Gemini API key is stored in environment variables and never appears in source code.

### Recommended Production Hardening

1. Restrict CORS `allow_origins` to the specific production frontend domain.
2. Implement API key or JWT-based authentication on all write endpoints.
3. Add rate limiting on the `/api/simulate` and `/api/simulation/start` endpoints.
4. Rotate all secrets (API keys, SMTP credentials) periodically.
5. Enable MongoDB Atlas IP allowlisting to restrict database access to the production server's IP address.
6. Serve the backend exclusively over HTTPS in production. The frontend WebSocket hook automatically upgrades to `wss:` when the page is served over HTTPS.
