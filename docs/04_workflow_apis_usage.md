# Rainly - Early Flood Detection System
## Document 4: Workflow, APIs, and Usage

---

## Table of Contents

1. [System Startup Workflow](#system-startup-workflow)
2. [Operator Workflows](#operator-workflows)
3. [Developer Workflows](#developer-workflows)
4. [REST API Reference](#rest-api-reference)
5. [WebSocket API Reference](#websocket-api-reference)
6. [Frontend Usage Guide](#frontend-usage-guide)
7. [LLM Configuration Workflow](#llm-configuration-workflow)
8. [Notification Configuration Workflow](#notification-configuration-workflow)
9. [Data Seeding Workflow](#data-seeding-workflow)
10. [Testing the System End-to-End](#testing-the-system-end-to-end)

---

## System Startup Workflow

### Step 1: Clone and Set Up the Backend

```bash
# Navigate into the backend directory
cd backend

# Copy the example environment file
cp .env.example .env

# Edit the .env file and populate required variables
# Minimum required: MONGODB_URI
```

### Step 2: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Start the Backend Server

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

On first start, the console will output:

```
Connected to MongoDB Atlas
[INIT] Database empty. Seeding initial data...
[SUCCESS] Database seeded!
```

The backend is now accessible at `http://localhost:8000`.
The interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs`.

### Step 4: Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Step 5: Configure the Frontend Environment Variable (Optional for Development)

For local development the default API URL (`http://localhost:8000/api`) applies without any configuration. For production or if the backend runs on a non-default port or host, create a `.env` file in the `frontend/` directory:

```
REACT_APP_API_URL=http://your-backend-host:8000/api
```

### Step 6: Start the Frontend Development Server

```bash
cd frontend
npm start
```

The frontend will open at `http://localhost:3000` and connect to the backend at `http://localhost:8000`.

---

## Operator Workflows

### Workflow 1: Monitoring Active Regions

1. Navigate to the Dashboard at `/`.
2. Review the summary statistics cards (Total Devices, Active Devices, In Warning, Regions, Rivers).
3. Check the WebSocket connection status badge in the top-right of the header. A "Live" badge (green) indicates real-time updates are active.
4. Review the Rivers Overview section to see device counts per river basin.
5. Review the Risk Distribution pie chart to assess the overall risk posture across all regions.
6. Examine the Recent Warnings table for the ten most recent alert events.

### Workflow 2: Viewing the Live Map

1. Navigate to the Map at `/map`.
2. The map is centered on India with circle markers at each monitored region.
3. Marker colors indicate current risk level:
   - Red: HIGH or CRITICAL
   - Amber/Orange: MEDIUM
   - Green: LOW
4. Click any marker to view a popup with the region name, river name, state, risk level, and device count.
5. The map updates automatically via WebSocket when risk levels change during active simulations.

### Workflow 3: Running a Flood Simulation

1. Navigate to the Simulator at `/simulator`.
2. Select a device from the device selector dropdown.
3. Configure simulation parameters:
   - Set the starting water level using the slider.
   - Set the starting rainfall intensity.
   - Set the starting flow rate.
   - Choose a trend: `rising`, `falling`, `stable`, or `random`.
   - Choose a speed: `slow`, `medium`, or `fast`.
4. Click "Start Simulation".
5. Observe the real-time sensor value panels updating every 2 seconds.
6. Monitor the risk level indicator changing color and label as water levels evolve.
7. If LLM is enabled, observe the LLM Reasoning panel populating with contextual analysis.
8. Adjust parameters using the live adjustment controls to modify the scenario without stopping.
9. Click "Stop Simulation" when the exercise is complete.

When water levels reach CRITICAL, the system will automatically:
- Dispatch SMS and Email notifications to all participants registered in the device's region.
- Broadcast a flood alert message visible in the Dashboard.
- Trigger browser push notifications if permission was granted.

### Workflow 4: Adding a New Participant

1. Navigate to Participants at `/participants`.
2. Scroll to the participant creation form.
3. Enter the participant's full name, age, phone number (in E.164 format, e.g., `+911234567890`), email address, and select the region.
4. Submit the form.
5. The new participant will immediately appear in the listing and will receive flood alerts for their assigned region.

### Workflow 5: Registering a New Sensor Device

1. Navigate to Devices at `/devices`.
2. Scroll to the device creation form.
3. Enter the device name, select the parent region, and provide the alert threshold water level in metres.
4. Submit the form.
5. The new device will appear in the listing and is immediately available for simulation.

### Workflow 6: Deactivating a Sensor Device

1. Navigate to Devices at `/devices`.
2. Locate the target device in the listing.
3. Click the toggle button next to the device to switch it from Active to Inactive.
4. Any running simulation for this device will detect the inactive status on the next tick and stop automatically.

### Workflow 7: Viewing Warning History for a Participant

1. Navigate to Participants at `/participants`.
2. Locate the participant in the listing.
3. Click the warning history action for that participant.
4. The system queries `/api/warnings/participant/{participant_id}` and displays all warnings issued to that participant, sorted newest first.

---

## Developer Workflows

### Workflow: Sending a Manual Test Sensor Payload

Use any HTTP client (curl, Postman, or the Swagger UI at `/docs`) to submit a test payload:

```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "d001",
    "region_id": "r001",
    "water_level": 360.0,
    "rainfall": 210.0,
    "flow_rate": 4000.0
  }'
```

Expected response when CRITICAL threshold is exceeded:

```json
{
  "status": "success",
  "prediction": {
    "risk_level": "CRITICAL",
    "warning_type": "evacuate",
    "risk_score": 0.95
  },
  "warnings_generated": 2,
  "affected_participants": 2
}
```

### Workflow: Starting a Programmatic Simulation

```bash
curl -X POST "http://localhost:8000/api/simulation/start?device_id=d001" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_water_level": 290.0,
    "initial_rainfall": 30.0,
    "initial_flow_rate": 1000.0,
    "variation_speed": "medium",
    "trend": "rising"
  }'
```

Response:

```json
{
  "status": "simulation_started",
  "device_id": "d001"
}
```

### Workflow: Adjusting Simulation Parameters at Runtime

```bash
curl -X POST http://localhost:8000/api/simulation/adjust/d001 \
  -H "Content-Type: application/json" \
  -d '{
    "water_level": 295.0,
    "rainfall": 85.0,
    "trend": "rising"
  }'
```

### Workflow: Downloading an LLM Model

```bash
cd backend
python download_model.py tinyllama   # For TinyLlama (669MB)
python download_model.py qwen        # For Qwen2-0.5B (352MB)
python download_model.py phi2        # For Phi-2 (1.6GB)
```

After download, update `.env`:

```
LLM_ENABLED=true
LLM_PROVIDER=local
LLM_MODEL_FILE=tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### Workflow: Re-Seeding the Database

```bash
curl -X POST http://localhost:8000/api/seed
```

This clears all existing regions, devices, participants, and warnings and repopulates with the full default dataset. Use this to reset to a known state during development or testing.

---

## REST API Reference

All endpoints accept and return JSON. The base path is `/api`.

---

### Regions

#### GET /api/regions
Returns a list of all monitored regions.

**Response**: Array of `Region` objects.

```json
[
  {
    "region_id": "r001",
    "name": "Haridwar Region",
    "latitude": 29.9457,
    "longitude": 78.1642,
    "river_name": "Ganges",
    "state": "Uttarakhand",
    "district": "Haridwar",
    "risk_level": "MEDIUM"
  }
]
```

#### POST /api/regions
Creates a new region.

**Request Body**: `Region` object (all required fields).

**Response**: The created `Region` object.

---

### Devices

#### GET /api/devices
Returns a list of all registered devices.

**Response**: Array of `Device` objects.

#### GET /api/devices/{device_id}
Returns a single device by ID.

**Path Parameters**: `device_id` (string)

**Response**: Single `Device` object. Returns HTTP 404 if not found.

#### POST /api/devices
Creates a new device.

**Request Body**: `Device` object (all required fields, `is_active` defaults to `true`).

**Response**: The created `Device` object.

#### PUT /api/devices/{device_id}/toggle
Toggles the `is_active` status of a device.

**Path Parameters**: `device_id` (string)

**Response**:

```json
{
  "device_id": "d001",
  "is_active": false
}
```

---

### Participants

#### GET /api/participants
Returns a list of all registered participants.

**Response**: Array of `Participant` objects.

#### POST /api/participants
Creates a new participant. The server generates a UUID for `participant_id`.

**Request Body**:

```json
{
  "name": "Ananya Das",
  "age": 29,
  "phone": "+911234567895",
  "email": "ananya@example.com",
  "region_id": "r006"
}
```

**Response**: The created `Participant` object including the generated `participant_id`.

---

### Warnings

#### GET /api/warnings
Returns all warning records, sorted by timestamp descending (newest first).

**Response**: Array of `Warning` objects.

#### GET /api/warnings/participant/{participant_id}
Returns all warnings for a specific participant, sorted by timestamp descending.

**Path Parameters**: `participant_id` (string)

**Response**: Array of `Warning` objects.

---

### Simulation (One-Time Payload)

#### POST /api/simulate
Submits a single IoT sensor reading for risk analysis. Generates warnings and sends notifications for all participants in the affected region. This endpoint always creates warnings and sends notifications regardless of cooldown state.

**Request Body**:

```json
{
  "sensor_id": "d001",
  "region_id": "r001",
  "water_level": 296.2,
  "rainfall": 45.0,
  "flow_rate": 1200.0,
  "timestamp": "2026-02-24T15:30:00Z"
}
```

Note: `timestamp` is optional. If omitted, the server uses the current UTC time.

**Response**:

```json
{
  "status": "success",
  "prediction": {
    "risk_level": "MEDIUM",
    "warning_type": "prepare",
    "risk_score": 0.55
  },
  "warnings_generated": 2,
  "affected_participants": 2
}
```

---

### Real-Time Simulation Management

#### POST /api/simulation/start?device_id={device_id}
Starts a continuous real-time simulation for the specified device.

**Query Parameters**: `device_id` (string)

**Request Body**:

```json
{
  "initial_water_level": 290.0,
  "initial_rainfall": 30.0,
  "initial_flow_rate": 1000.0,
  "variation_speed": "medium",
  "trend": "rising"
}
```

| Parameter | Accepted Values |
|-----------|----------------|
| `variation_speed` | `"slow"`, `"medium"`, `"fast"` |
| `trend` | `"rising"`, `"falling"`, `"stable"`, `"random"` |

**Response**:

```json
{
  "status": "simulation_started",
  "device_id": "d001"
}
```

#### POST /api/simulation/stop/{device_id}
Stops the active simulation for the specified device.

**Path Parameters**: `device_id` (string)

**Response**:

```json
{
  "status": "simulation_stopped",
  "device_id": "d001"
}
```

#### POST /api/simulation/adjust/{device_id}
Adjusts one or more simulation parameters without stopping the simulation.

**Path Parameters**: `device_id` (string)

**Request Body** (all fields optional):

```json
{
  "water_level": 295.0,
  "rainfall": 85.0,
  "flow_rate": 1500.0,
  "trend": "rising"
}
```

**Response**:

```json
{
  "status": "parameters_adjusted",
  "device_id": "d001"
}
```

#### GET /api/simulation/active
Returns the list of all currently active simulation device IDs.

**Response**:

```json
{
  "active_simulations": ["d001", "d010"],
  "count": 2
}
```

---

### Analytics

#### GET /api/analytics
Returns aggregated system-wide metrics.

**Response**:

```json
{
  "total_devices": 15,
  "active_devices": 14,
  "devices_in_warning": 5,
  "recent_warnings": [
    {
      "warning_id": "uuid-string",
      "region_id": "r001",
      "device_id": "d001",
      "river_name": "Ganges",
      "participant_id": "p001",
      "warning_type": "prepare",
      "risk_level": "MEDIUM",
      "timestamp": "2026-02-24T15:30:00",
      "water_level": 296.2,
      "rainfall": 45.0,
      "flow_rate": 1200.0
    }
  ]
}
```

---

### Database Operations

#### POST /api/seed
Clears all collections and re-populates the database with the full default dataset. Useful for resetting the system to a known state.

**Response**:

```json
{
  "status": "success",
  "message": "Database seeded with comprehensive Indian river data",
  "counts": {
    "regions": 10,
    "devices": 15,
    "participants": 8,
    "warnings": 8
  }
}
```

#### GET /
Root health-check endpoint.

**Response**:

```json
{
  "message": "Rainly - Early Flood Detection API",
  "status": "running"
}
```

---

## WebSocket API Reference

### Connection

Connect to: `ws://localhost:8000/ws/realtime` (development) or `wss://your-backend-domain/ws/realtime` (production).

The connection is established by sending the WebSocket handshake and waiting for server acceptance via `ConnectionManager.connect()`.

### Client-to-Server Messages

#### Ping
Used for keepalive. Sent by the client every 30 seconds.

```json
{
  "type": "ping"
}
```

#### Get Status
Request a snapshot of active simulations and connection count.

```json
{
  "type": "get_status"
}
```

### Server-to-Client Messages

#### Pong (response to ping)

```json
{
  "type": "pong",
  "timestamp": "2026-02-24T15:30:00.000000"
}
```

#### Status (response to get_status)

```json
{
  "type": "status",
  "active_simulations": ["d001", "d010"],
  "total_connections": 3
}
```

#### Device Update (broadcast, sent every simulation tick)

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
    "llm_status": "idle",
    "llm_reasoning": "Water level is approaching threshold with moderate rainfall..."
  },
  "timestamp": "2026-02-24T15:30:00.000000"
}
```

The `llm_reasoning` field is only present when LLM is enabled and has produced output.

#### Flood Alert (broadcast, sent when CRITICAL notifications are dispatched)

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

#### Warning Generated (broadcast, sent when warning records are inserted)

```json
{
  "type": "warning_generated",
  "data": { ... },
  "timestamp": "2026-02-24T15:30:00.000000"
}
```

---

## Frontend Usage Guide

### Dashboard Usage

The Dashboard is the starting point for operators. Navigate to `http://localhost:3000/` to access it. The connection status badge in the upper-right corner confirms whether the WebSocket connection is active. If the badge shows "Offline", check that the backend is running and reachable.

The dashboard auto-refreshes its REST data every 30 seconds. The WebSocket connection provides real-time updates between these polling cycles for live simulations.

### Map Usage

The Map tab at `/map` provides a geographic overview. Users can zoom in and out using the mouse wheel or the map controls. Click any circle marker to open a popup with details about that monitoring station.

### Simulator Usage

The Simulator tab at `/simulator` is the most interactive section. It is recommended to:
1. Select a device in a high-risk region for demonstration purposes.
2. Set a rising trend to observe the system escalating from LOW to MEDIUM to HIGH to CRITICAL.
3. Observe the real-time sensor panels updating every 2 seconds.
4. Watch the Map tab (in another browser tab) simultaneously to observe the region's risk color changing.

### Analytics Usage

The Analytics tab at `/analytics` provides historical trend charts. The charts draw their data from the warnings collection, so they become more meaningful as the system accumulates warning history through simulations or live data.

---

## LLM Configuration Workflow

### Option A: Google Gemini (Recommended for Cloud Deployment)

1. Visit [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey) and generate an API key.
2. Add to `backend/.env`:

```
LLM_ENABLED=true
LLM_PROVIDER=google
GEMINI_API_KEY=your_api_key_here
```

3. Restart the backend. The console will print: `[SUCCESS] Google Gemini Pro loaded successfully!`

### Option B: Local GGUF Model (No Internet Required After Download)

1. Download a model:

```bash
cd backend
python download_model.py qwen   # Recommended (352MB)
```

2. Add to `backend/.env`:

```
LLM_ENABLED=true
LLM_PROVIDER=local
LLM_MODEL_FILE=qwen2-0_5b-instruct-q4_k_m.gguf
LLM_MODEL_PATH=models/llm
```

3. Restart the backend. The console will print: `[SUCCESS] Local Model loaded successfully!`

### Disabling LLM

Set `LLM_ENABLED=false` (or leave the variable unset). The system will use the rule-based predictor and template-based email generator in all scenarios.

---

## Notification Configuration Workflow

### Configuring Gmail SMTP

1. Enable 2-Factor Authentication on your Google account.
2. Generate an App Password at [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Add to `backend/.env`:

```
GMAIL_ADDRESS=your.address@gmail.com
GMAIL_PASSWORD=your_app_password_here
```

The system will attempt port 587 (STARTTLS) first, then fall back to port 465 (SSL) if the first attempt fails.

### Configuring Resend (Preferred for Production)

1. Create an account at [https://resend.com](https://resend.com).
2. Generate an API key.
3. Add to `backend/.env`:

```
RESEND_API_KEY=re_your_key_here
```

Resend takes priority over Gmail SMTP if both are configured. In Resend's free tier, emails can only be sent to verified email addresses.

### Configuring Twilio SMS

1. Create a Twilio account at [https://www.twilio.com](https://www.twilio.com).
2. Provision a phone number in your Twilio console.
3. Obtain your Account SID and Auth Token from the Twilio dashboard.
4. Add to `backend/.env`:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
```

Twilio will only send SMS to verified caller IDs on trial accounts. A paid account allows sending to any E.164-formatted number.

---

## Data Seeding Workflow

The database is seeded automatically on first startup. To reset the database at any time, call the seed endpoint:

```bash
curl -X POST http://localhost:8000/api/seed
```

This is equivalent to calling the route handler `seed_database()` directly.

**Caution**: This endpoint deletes all existing data including any custom regions, devices, participants, and warning history before re-inserting the default dataset.

---

## Testing the System End-to-End

### Manual Full-Stack Test

1. Start the backend and frontend.
2. Open `http://localhost:3000` in a browser.
3. Navigate to the Simulator tab.
4. Start a simulation with trend `rising` and speed `fast`.
5. Monitor the sensor panels escalating.
6. Within 1-2 minutes, the risk should reach CRITICAL.
7. Verify:
   - The risk level panel shows CRITICAL in red.
   - A flood alert message is broadcast (visible in the Dashboard's Recent Warnings table after a page refresh or via WebSocket).
   - If email is configured, an HTML email is delivered to all participants in the region.
   - If SMS is configured, a text message is delivered to all participants in the region.
   - A browser push notification (if permission was granted) appears.

### API-Only Test (Without Frontend)

```bash
# Check backend health
curl http://localhost:8000/

# List regions
curl http://localhost:8000/api/regions

# List devices
curl http://localhost:8000/api/devices

# List participants
curl http://localhost:8000/api/participants

# Submit a CRITICAL sensor payload for device d005 (Patna, Ganges - HIGH risk region)
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "d005",
    "region_id": "r003",
    "water_level": 54.0,
    "rainfall": 210.0,
    "flow_rate": 2200.0
  }'

# Check analytics for generated warnings
curl http://localhost:8000/api/analytics

# List all warnings
curl http://localhost:8000/api/warnings
```
