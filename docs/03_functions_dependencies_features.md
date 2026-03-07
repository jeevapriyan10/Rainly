# Rainly - Early Flood Detection System
## Document 3: Functions, Dependencies, and Features

---

## Table of Contents

1. [Backend Functions Reference](#backend-functions-reference)
2. [Frontend Functions and Components Reference](#frontend-functions-and-components-reference)
3. [Python Dependency Reference](#python-dependency-reference)
4. [JavaScript Dependency Reference](#javascript-dependency-reference)
5. [Feature Reference](#feature-reference)
6. [Error Handling Patterns](#error-handling-patterns)

---

## Backend Functions Reference

### `db.py`

#### `connect_db()`
**Signature**: `async def connect_db() -> None`

Establishes the asynchronous MongoDB connection. Reads the `MONGODB_URI` environment variable (default: `mongodb://localhost:27017/flood_detection`) and creates an `AsyncIOMotorClient` instance. Assigns the `flood_detection` database to the module-level `db` variable. Called once during application startup via the lifespan context manager.

#### `close_db()`
**Signature**: `async def close_db() -> None`

Closes the active MongoDB client connection. Called once during application shutdown via the lifespan context manager. Logs a confirmation message on successful closure.

#### `get_db()`
**Signature**: `def get_db() -> AsyncIOMotorDatabase`

Returns the module-level MongoDB database instance. Called by every route handler that requires database access. This is a synchronous function that returns the already-connected database object; it does not create a new connection.

---

### `models.py`

#### `Region` (Pydantic Model)
Represents a monitored geographic region.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `region_id` | `str` | Yes | - | Unique identifier |
| `name` | `str` | Yes | - | Human-readable name |
| `latitude` | `float` | Yes | - | Geographic latitude |
| `longitude` | `float` | Yes | - | Geographic longitude |
| `river_name` | `str` | Yes | - | Associated river |
| `state` | `Optional[str]` | No | `None` | Indian state |
| `district` | `Optional[str]` | No | `None` | District name |
| `risk_level` | `Optional[str]` | No | `"LOW"` | LOW, MEDIUM, HIGH, CRITICAL |

#### `Device` (Pydantic Model)
Represents a registered IoT sensor device.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `device_id` | `str` | Yes | - | Unique device identifier |
| `region_id` | `str` | Yes | - | Parent region reference |
| `name` | `str` | Yes | - | Sensor station name |
| `alert_threshold` | `float` | Yes | - | Danger water level in metres |
| `is_active` | `bool` | No | `True` | Operational status |
| `last_water_level` | `Optional[float]` | No | `None` | Last water level reading |
| `last_rainfall` | `Optional[float]` | No | `None` | Last rainfall reading in mm |
| `last_flow_rate` | `Optional[float]` | No | `None` | Last flow rate in m³/s |
| `battery_level` | `Optional[int]` | No | `None` | Battery percentage 0-100 |
| `last_seen` | `Optional[datetime]` | No | `None` | Last data reception timestamp |

#### `Participant` (Pydantic Model)
Represents a registered resident in a monitored region.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `participant_id` | `Optional[str]` | No | `None` | UUID (generated server-side) |
| `name` | `str` | Yes | - | Full name |
| `age` | `Optional[int]` | No | `None` | Age in years |
| `phone` | `Optional[str]` | No | `None` | Phone in E.164 format |
| `email` | `Optional[str]` | No | `None` | Email address |
| `region_id` | `str` | Yes | - | Parent region reference |

#### `Warning` (Pydantic Model)
Represents a flood warning event record.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `warning_id` | `Optional[str]` | No | `None` | UUID (generated server-side) |
| `region_id` | `str` | Yes | - | Affected region |
| `device_id` | `str` | Yes | - | Triggering device |
| `river_name` | `str` | Yes | - | River name |
| `participant_id` | `str` | Yes | - | Notified participant |
| `warning_type` | `str` | Yes | - | monitor, prepare, evacuate |
| `risk_level` | `str` | Yes | - | Risk classification |
| `timestamp` | `datetime` | Yes | - | Warning UTC timestamp |
| `water_level` | `float` | Yes | - | Triggering water level |
| `rainfall` | `float` | Yes | - | Triggering rainfall |
| `flow_rate` | `float` | Yes | - | Triggering flow rate |

#### `SensorPayload` (Pydantic Model)
Represents an incoming IoT sensor reading.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `sensor_id` | `str` | Yes | - | Device identifier |
| `region_id` | `str` | Yes | - | Region identifier |
| `water_level` | `float` | Yes | - | Current water level |
| `rainfall` | `float` | Yes | - | Current rainfall |
| `flow_rate` | `float` | Yes | - | Current flow rate |
| `timestamp` | `Optional[datetime]` | No | `None` | Reading timestamp |

#### `PredictionResult` (Pydantic Model)
Represents the output of the prediction engine.

| Field | Type | Description |
|-------|------|-------------|
| `risk_level` | `str` | LOW, MEDIUM, HIGH, CRITICAL |
| `warning_type` | `str` | monitor, prepare, evacuate |
| `risk_score` | `float` | Weighted risk score, 0.0 to 1.0 |

---

### `predictor.py`

#### `predict_flood_risk(payload, alert_threshold)`
**Signature**: `def predict_flood_risk(payload: SensorPayload, alert_threshold: float) -> PredictionResult`

Top-level prediction dispatcher. Currently delegates entirely to `rules_based_predict`. The design intent preserved in comments is that LLM prediction was evaluated at this level but moved to background tasks to avoid blocking the main event loop on every sensor tick. Returns a `PredictionResult` instance.

#### `rules_based_predict(payload, alert_threshold)`
**Signature**: `def rules_based_predict(payload: SensorPayload, alert_threshold: float) -> PredictionResult`

Implements the multi-factor weighted risk scoring algorithm:

1. Computes `water_ratio = water_level / alert_threshold`.
2. Computes `rainfall_factor = min(rainfall / 200.0, 1.0)`.
3. Computes `flow_factor = min(flow_rate / 3000.0, 1.0)`.
4. Computes `risk_score = (water_ratio * 0.5) + (rainfall_factor * 0.3) + (flow_factor * 0.2)`.
5. Applies graduated threshold rules to classify risk level and warning type.
6. Returns a `PredictionResult` with the capped risk score.

---

### `simulation_engine.py`

#### `SimulationEngine.__init__()`
Initializes the engine with two empty dictionaries: `active_simulations` (stores configuration and state for each running simulation, keyed by `device_id`) and `running_tasks` (stores `asyncio.Task` references, keyed by `device_id`).

#### `SimulationEngine.start_simulation(device_id, region_id, config, db)`
**Signature**: `async def start_simulation(self, device_id: str, region_id: str, config: dict, db) -> dict`

Stops any existing simulation for the device, stores the new configuration, creates a new `asyncio.Task` wrapping `_run_simulation`, and performs an immediate database update with the initial sensor values. Returns `{"status": "simulation_started", "device_id": device_id}`.

**Configuration dictionary keys**:

| Key | Type | Description |
|-----|------|-------------|
| `initial_water_level` | float | Starting water level |
| `initial_rainfall` | float | Starting rainfall |
| `initial_flow_rate` | float | Starting flow rate |
| `alert_threshold` | float | Injected from device record |
| `variation_speed` | str | `slow`, `medium`, or `fast` |
| `trend` | str | `rising`, `falling`, `stable`, or `random` |

#### `SimulationEngine.stop_simulation(device_id)`
**Signature**: `async def stop_simulation(self, device_id: str) -> dict`

Cancels the `asyncio.Task` for the specified device, removes the device from `active_simulations` and `running_tasks`. Returns `{"status": "simulation_stopped", "device_id": device_id}` or `{"status": "no_active_simulation"}` if no simulation was running.

#### `SimulationEngine.adjust_parameters(device_id, params)`
**Signature**: `async def adjust_parameters(self, device_id: str, params: dict) -> dict`

Updates the in-memory simulation configuration dictionary with new parameter values. Immediately broadcasts the updated values to all WebSocket clients. Returns a status confirmation dictionary.

#### `SimulationEngine.get_active_simulations()`
**Signature**: `def get_active_simulations(self) -> list`

Returns a list of `device_id` strings for all currently running simulations.

#### `SimulationEngine._run_simulation(device_id, region_id, config, db)`
**Signature**: `async def _run_simulation(self, device_id, region_id, config, db) -> None`

The main simulation coroutine. Executes in a `while True` loop with a 2-second `asyncio.sleep` tick. On each tick:
1. Checks the device's `is_active` flag in MongoDB and stops if the device has been deactivated.
2. Computes deltas for water level, rainfall, and flow rate based on the configured trend and speed multiplier.
3. Clamps values to realistic physical bounds (water: 250-350m, rainfall: 0-300mm, flow: 0-5000 m³/s).
4. Creates non-blocking database update tasks.
5. Optionally launches a background LLM analysis task.
6. Broadcasts updated sensor data over WebSocket.
7. If risk is CRITICAL, launches a background alert dispatch task.

The coroutine exits cleanly on `asyncio.CancelledError` and removes itself from the engine's tracking dictionaries.

#### `SimulationEngine._process_llm_analysis(device_id, sensor_data)`
**Signature**: `async def _process_llm_analysis(self, device_id: str, sensor_data: dict) -> None`

Background coroutine that runs LLM inference in a thread pool using `asyncio.to_thread(analyze_with_llm, sensor_data)`. Updates the `llm_status` field in `active_simulations` and broadcasts the reasoning result or failure status over WebSocket.

#### `SimulationEngine._process_alerts(device_id, region_id, prediction, water, rain, flow, threshold, db)`
**Signature**: `async def _process_alerts(...) -> None`

Background coroutine that handles alert dispatch for CRITICAL events. Applies the 15-minute bulk cooldown and 30-minute per-participant cooldown. For each eligible participant, inserts a warning record, calls `send_flood_alert`, and updates cooldown timestamps. On completion, broadcasts a `flood_alert` message over WebSocket.

---

### `websocket_manager.py`

#### `ConnectionManager.__init__()`
Initializes `active_connections` (list of active `WebSocket` objects) and `device_data` (in-memory cache of the most recent data for each device, keyed by `device_id`).

#### `ConnectionManager.connect(websocket)`
**Signature**: `async def connect(self, websocket: WebSocket) -> None`

Accepts the WebSocket handshake and appends the connection to `active_connections`.

#### `ConnectionManager.disconnect(websocket)`
**Signature**: `def disconnect(self, websocket: WebSocket) -> None`

Removes the WebSocket from `active_connections`. Safe to call even if the connection is not in the list.

#### `ConnectionManager.broadcast(message)`
**Signature**: `async def broadcast(self, message: dict) -> None`

Sends a JSON-serializable dictionary to all active connections. Silently removes any connections that raise an exception during send (indicating a closed or dropped connection).

#### `ConnectionManager.send_personal_message(message, websocket)`
**Signature**: `async def send_personal_message(self, message: dict, websocket: WebSocket) -> None`

Sends a message to a single specific WebSocket connection.

#### `ConnectionManager.update_device_data(device_id, data)`
**Signature**: `def update_device_data(self, device_id: str, data: dict) -> None`

Updates the in-memory device data cache with a new data dictionary and a `last_update` timestamp.

#### `ConnectionManager.broadcast_device_update(device_id, data)`
**Signature**: `async def broadcast_device_update(self, device_id: str, data: dict) -> None`

Updates the device cache and broadcasts a `device_update` type message to all connected clients.

#### `ConnectionManager.broadcast_alert(alert_data)`
**Signature**: `async def broadcast_alert(self, alert_data: dict) -> None`

Broadcasts a `flood_alert` type message to all connected clients.

#### `ConnectionManager.broadcast_warning(warning_data)`
**Signature**: `async def broadcast_warning(self, warning_data: dict) -> None`

Broadcasts a `warning_generated` type message to all connected clients.

---

### `notify.py`

#### `format_sms_alert(region_name, river_name, risk_level, water_level, threshold, action)`
**Signature**: `def format_sms_alert(...) -> str`

Produces a concise SMS message tailored to the risk level. Designed to stay within the 160-character SMS limit.

#### `format_email_alert(participant_name, region_name, river_name, risk_level, water_level, threshold, rainfall, action)`
**Signature**: `def format_email_alert(...) -> str`

Produces a complete, styled HTML email string. The email includes a color-coded header, personalized greeting, data grid with sensor readings, a risk-level-appropriate action list, and emergency contact numbers.

#### `_sync_send_resend(to_email, subject, html_body)`
**Signature**: `def _sync_send_resend(to_email: str, subject: str, html_body: str) -> dict`

Synchronous blocking function. Sends an email via the Resend API using an HTTP POST request. Returns a status dictionary with `{"status": "sent", "provider": "resend", "id": ...}` on success.

#### `_sync_send_smtp(to_email, subject, html_body)`
**Signature**: `def _sync_send_smtp(to_email: str, subject: str, html_body: str) -> dict`

Synchronous blocking function. Sends an HTML email via Gmail SMTP. Attempts port 587 (STARTTLS) first, then falls back to port 465 (SSL). Returns a status dictionary.

#### `_sync_send_sms(to_phone, message)`
**Signature**: `def _sync_send_sms(to_phone: str, message: str) -> dict`

Synchronous blocking function. Sends an SMS via the Twilio REST client. Returns a status dictionary with the Twilio message SID on success.

#### `send_email(to_email, subject, html_body)`
**Signature**: `async def send_email(to_email: str, subject: str, html_body: str) -> dict`

Async wrapper. Calls `_sync_send_resend` if `RESEND_API_KEY` is present, otherwise calls `_sync_send_smtp`, both via `asyncio.to_thread` to avoid blocking the event loop.

#### `send_sms(to_phone, message)`
**Signature**: `async def send_sms(to_phone: str, message: str) -> dict`

Async wrapper for `_sync_send_sms` via `asyncio.to_thread`.

#### `send_flood_alert(participant, region, device, prediction, sensor_data)`
**Signature**: `async def send_flood_alert(participant: dict, region: dict, device: dict, prediction: dict, sensor_data: dict) -> dict`

Top-level orchestrator. Formats and sends both SMS and Email alerts for a single participant. If LLM is enabled, attempts to generate the email body via `generate_detailed_warning`. Falls back to the template system if LLM generation fails. Returns a dictionary with `sms` and `email` result sub-dictionaries.

#### `send_notification(participant, message)`
**Signature**: `async def send_notification(participant: dict, message: str)`

Legacy single-channel SMS helper. Used for simple notification dispatch without the full flood alert formatting pipeline.

---

### `llm_service.py`

#### `initialize_llm()`
**Signature**: `def initialize_llm() -> bool`

Initializes the LLM system. For Google provider, configures the `google-generativeai` SDK and creates the Gemini Pro model instance. For local provider, loads the GGUF model file via `llama-cpp-python`. Returns `True` on success, `False` on any failure. Called at module import time when `LLM_ENABLED=true`.

#### `generate_with_llm(prompt, max_tokens)`
**Signature**: `def generate_with_llm(prompt: str, max_tokens: int = 500) -> str`

Sends a prompt to the configured LLM and returns the generated text string. Acquires `_model_lock` before calling the local model to prevent concurrent inference. Returns a fallback string on any exception.

#### `analyze_with_llm(sensor_data)`
**Signature**: `def analyze_with_llm(sensor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]`

Constructs a hydrology expert prompt from the sensor data dictionary and calls `generate_with_llm`. Parses the response as JSON and returns a structured dictionary containing `risk_level`, `action`, and `reasoning`. Returns `None` if LLM is unavailable or parsing fails.

#### `generate_detailed_warning(participant, region, device, prediction, sensor_data)`
**Signature**: `def generate_detailed_warning(...) -> str`

Constructs an authoritative flood warning email prompt and generates a 200-word alert email body via `generate_with_llm`. Wraps the generated content in a fully styled HTML template and returns the complete HTML string. Falls back to `generate_enhanced_email_fallback` on any error.

#### `generate_enhanced_email_fallback(participant, region, device, prediction, sensor_data)`
**Signature**: `def generate_enhanced_email_fallback(...) -> str`

Produces a detailed, structured HTML flood warning email using static content blocks without any LLM dependency. Analyzes the sensor data to identify likely causes (heavy rainfall, excess water level, high flow rate), selects risk-calibrated action lists and timeline estimates, and composes a complete HTML email. This is the primary email generation path when LLM is disabled.

---

### `download_model.py`

#### `download_file(url, destination)`
**Signature**: `def download_file(url: str, destination: str) -> None`

Downloads a file from a URL to a local path using streaming HTTP. Displays a `tqdm` progress bar showing download speed and percentage completion.

#### `download_model(model_key)`
**Signature**: `def download_model(model_key: str = "tinyllama") -> bool`

Validates the model key, creates the `models/llm` directory if it does not exist, checks for an existing valid download (files under 100 MB are considered corrupt and re-downloaded), and calls `download_file`. Prints post-download instructions for updating the `.env` configuration.

#### `show_models()`
**Signature**: `def show_models() -> None`

Prints a formatted listing of all supported GGUF models with their names, sizes, and quality characteristics. Used in interactive CLI mode.

---

## Frontend Functions and Components Reference

### `api.js`

| Function | HTTP Method | Endpoint | Description |
|----------|-------------|----------|-------------|
| `fetchRegions()` | GET | `/api/regions` | Returns array of all region objects |
| `createRegion(region)` | POST | `/api/regions` | Creates a new region |
| `fetchDevices()` | GET | `/api/devices` | Returns array of all device objects |
| `createDevice(device)` | POST | `/api/devices` | Creates a new device |
| `toggleDevice(deviceId)` | PUT | `/api/devices/{id}/toggle` | Flips the `is_active` flag |
| `fetchParticipants()` | GET | `/api/participants` | Returns array of all participants |
| `createParticipant(participant)` | POST | `/api/participants` | Creates a new participant |
| `fetchWarnings()` | GET | `/api/warnings` | Returns all warnings, sorted newest first |
| `fetchParticipantWarnings(participantId)` | GET | `/api/warnings/participant/{id}` | Returns warnings for a specific participant |
| `simulatePayload(payload)` | POST | `/api/simulate` | Submits a one-time sensor payload |
| `fetchAnalytics()` | GET | `/api/analytics` | Returns aggregated system analytics |

### `hooks/useWebSocket.js`

#### `useWebSocket()`
**Returns**: `{ isConnected, lastMessage, deviceUpdates, alerts, sendMessage }`

Custom React hook. Establishes a WebSocket connection on mount, sets up message handling, manages reconnection, requests browser notification permission, and cleans up on unmount. The `deviceUpdates` object is a dictionary where keys are device IDs and values are the most recently received sensor data objects from the server. The `alerts` array accumulates all received `flood_alert` messages during the session.

### `components/Dashboard.js`

The Dashboard component fetches analytics, regions, and device data on mount and sets up a 30-second polling interval for REST data refresh (WebSocket provides real-time granularity between polls). It computes river groups, state groups, risk level distributions, and low-battery device lists from the fetched data. Renders:

- WebSocket connection status badge.
- Low battery warning banner (conditional).
- Statistics summary cards: Total Devices, Active Devices, In Warning, Regions, Rivers.
- River Overview grid showing regions and device count per river.
- Risk Distribution pie chart (Recharts PieChart).
- Water Level and Rainfall trend line chart (Recharts LineChart, from recent warnings data).
- State Coverage grid (sorted by region count descending).
- Recent Warnings table with risk badges.

### `components/MapTab.js`

Renders an interactive Leaflet map centered on India. For each monitored region, places a `CircleMarker` with a color encoding the current risk level (red for HIGH/CRITICAL, amber for MEDIUM, green for LOW). Clicking a marker displays a popup with the region name, river, state, current risk level, and device count. Subscribes to WebSocket updates to reflect risk level changes without page refresh.

### `components/SimulatorTab.js`

Provides the primary real-time simulation control interface. Features:

- Device selector dropdown populated from the device registry.
- Trend configuration controls: starting water level slider, rainfall slider, flow rate slider, trend direction selector (rising, falling, stable, random), and speed selector (slow, medium, fast).
- Start Simulation and Stop Simulation buttons that call `/api/simulation/start` and `/api/simulation/stop/{device_id}`.
- Real-time sensor value display panels that update from WebSocket `device_update` messages.
- Risk level indicator with color coding.
- LLM status indicator (idle, processing, completed, failed).
- LLM reasoning text display panel (populated when LLM is enabled).
- Parameter adjustment controls that send live updates to a running simulation via `/api/simulation/adjust/{device_id}`.

### `components/DevicesTab.js`

Lists all registered devices with their name, associated region, alert threshold, active/inactive status, battery level with visual indicator, and last recorded sensor readings. Provides a toggle button for each device that calls `toggleDevice()`. Includes a device creation form.

### `components/ParticipantsTab.js`

Lists all registered participants with their name, age, region, contact information, and most recent warning status. Provides a participant creation form and a warning history view accessible per participant.

### `components/RegionsTab.js`

Lists all monitored regions with their name, river, state, district, coordinates, and current risk level displayed as a color-coded badge. Provides a region creation form.

### `components/AnalyticsTab.js`

Provides detailed analytics visualizations. Fetches the analytics endpoint and renders advanced charts including warning frequency over time, device status breakdown, and per-risk-level distribution charts using Recharts components.

### `components/NavBar.js`

Renders the top navigation bar with links to all seven routes: Dashboard, Map, Regions, Devices, Participants, Analytics, and Simulator. Includes the Rainly branding and a live/offline indicator.

---

## Python Dependency Reference

| Package | Version Constraint | Purpose | Notes |
|---------|-------------------|---------|-------|
| `fastapi` | `>=0.110.0` | Web framework and HTTP router | Core backend dependency |
| `uvicorn` | `>=0.29.0` | ASGI server | Runs the FastAPI application |
| `motor` | `>=3.4.0` | Async MongoDB driver | Wraps PyMongo for async access via Motor |
| `pydantic` | `>=2.7.0` | Data validation and schema enforcement | Used for all request/response models |
| `python-dotenv` | `>=1.0.0` | Environment variable loading | Reads `.env` file on startup |
| `websockets` | `>=12.0` | WebSocket protocol implementation | Required by FastAPI's WebSocket support |
| `twilio` | `>=9.0.0` | SMS notification dispatch | Optional; gracefully disabled if not configured |
| `python-multipart` | `>=0.0.9` | Form data parsing | Required by FastAPI for file upload / multipart support |
| `google-generativeai` | `>=0.4.1` | Google Gemini Pro LLM access | Optional; loaded only when `LLM_PROVIDER=google` |
| `llama-cpp-python` | `>=0.2.70` | Local GGUF model inference | Optional; loaded only when `LLM_PROVIDER=local` |
| `requests` | `>=2.31.0` | HTTP client for Resend API and model downloads | Used in `notify.py` and `download_model.py` |
| `tqdm` | `>=4.66.0` | Progress bar for model downloads | Used in `download_model.py` |

**Standard Library Modules Used (no installation required)**:
- `asyncio`: Asyncio event loop, tasks, threading bridge.
- `smtplib`: SMTP email dispatch.
- `email.mime.text`, `email.mime.multipart`: MIME email composition.
- `os`: Environment variable access and file path manipulation.
- `uuid`: UUID generation for IDs.
- `json`: JSON parsing for LLM responses.
- `threading`: Threading lock for LLM model access.
- `datetime`: UTC timestamp generation.
- `typing`: Type hints (`List`, `Dict`, `Optional`, `Any`).

---

## JavaScript Dependency Reference

| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `react` | `^18.2.0` | UI component library | Core frontend framework |
| `react-dom` | `^18.2.0` | React DOM renderer | Mounts React into the HTML document |
| `react-router-dom` | `^6.21.1` | Client-side routing | Powers the multi-page navigation without full reloads |
| `react-scripts` | `5.0.1` | CRA build tooling | Provides `start`, `build`, `test` scripts |
| `leaflet` | `^1.9.4` | Interactive map library | Renders the geospatial India flood map |
| `react-leaflet` | `^4.2.1` | React bindings for Leaflet | Provides `MapContainer`, `TileLayer`, `CircleMarker` components |
| `recharts` | `^2.10.3` | Chart library | Powers all data visualizations (LineChart, PieChart, etc.) |

**Browser Web APIs Used**:
- `WebSocket`: Native browser WebSocket client for real-time connection.
- `Notification` API: Browser push notifications for flood alerts.
- `fetch` API: HTTP requests to the REST backend.
- `window.location`: Protocol detection for ws/wss URL construction.
- `setInterval` / `clearInterval`: Polling loops in Dashboard and WebSocket keepalive.
- `setTimeout` / `clearTimeout`: WebSocket reconnection delay.

---

## Feature Reference

### Feature: Auto-Seed Database on First Run

On application startup, if the `regions` collection is empty, `seed_database()` is called automatically without requiring manual intervention. This seeds 10 regions, 15 devices, 8 participants, and 8 sample warnings.

### Feature: Multi-Trend Simulation

The simulation engine supports four distinct trend modes configurable per device:
- **Rising**: Water level and rainfall increase over time, simulating an approaching flood event.
- **Falling**: Water level and rainfall decrease over time, simulating post-flood recession.
- **Stable**: Minor random fluctuations around a stable baseline.
- **Random**: Unpredictable, noisy variation suitable for stress-testing the alert pipeline.

### Feature: Speed Multiplier

Each simulation can be configured with a speed multiplier applied to the delta calculations:
- **Slow** (0.3x): Gentle, slow-moving changes suitable for long-duration monitoring drills.
- **Medium** (1.0x): Standard rate matching typical real-world conditions.
- **Fast** (2.0x): Rapid escalation useful for quick testing of alert thresholds.

### Feature: Battery Level Monitoring

Each device record includes a `battery_level` integer. The Dashboard components identifies devices with battery levels below 30% and renders a prominent warning banner listing those device names, prompting operators to schedule maintenance or battery replacement.

### Feature: Alert Cooldown System

The simulation engine implements a two-tier cooldown system to prevent notification flooding during sustained high-risk conditions:
- Per-participant cooldown prevents the same person from receiving more than one alert per 30 minutes per device.
- Bulk alert cooldown prevents a device from sending any alert batch more frequently than once every 15 minutes.

### Feature: Browser Push Notifications

The `useWebSocket` hook requests browser notification permission on mount. When a `flood_alert` message is received over WebSocket, a browser push notification is triggered displaying the risk level and affected region, even if the browser tab is not in focus.

### Feature: LLM Reasoning Display

When LLM is enabled, the SimulatorTab renders an LLM reasoning panel that displays the model's textual risk assessment in real time. The panel shows the LLM status lifecycle: idle, processing, completed, or failed.

### Feature: Real-Time Parameter Adjustment

While a simulation is running, the SimulatorTab provides controls to adjust the water level, rainfall, and flow rate in real time via the `/api/simulation/adjust/{device_id}` endpoint, without stopping and restarting the simulation. This enables dynamic scenario exercises.

---

## Error Handling Patterns

### Backend Error Handling

- **HTTP 404**: Returned when a `device_id` or `region_id` lookup fails.
- **Notification failure isolation**: All notification dispatch is wrapped in `try/except` blocks. A failed SMS or email does not propagate an exception to the caller or halt subsequent notifications for other participants.
- **LLM failure graceful degradation**: If LLM initialization fails, the system continues operating with rule-based prediction and template-based email generation.
- **WebSocket error recovery**: The `broadcast` method catches exceptions from individual connections and removes the broken connection from the active list, preventing a single dropped client from disrupting the broadcast to all other clients.
- **Simulation cancellation handling**: The simulation coroutine catches `asyncio.CancelledError` and performs clean exit, removing the device from tracking dictionaries to prevent memory leaks.

### Frontend Error Handling

- **API call failures**: All `fetch` calls in `api.js` are called within `try/catch` blocks in the consuming components. Failures are logged to the console and surfaces a fallback UI message.
- **WebSocket disconnection**: The `useWebSocket` hook automatically attempts to reconnect after a 5-second delay on any disconnection event.
- **Loading states**: All data-dependent components render a loading state while asynchronous data is being fetched, preventing null reference errors in the render tree.
