# Rainly - Early Flood Detection System
## Document 5: Deployment and Future Improvements

---

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Deploying to Render (Recommended)](#deploying-to-render-recommended)
3. [Manual Cloud Deployment (Ubuntu Server)](#manual-cloud-deployment-ubuntu-server)
4. [MongoDB Atlas Setup](#mongodb-atlas-setup)
5. [Docker-Based Deployment](#docker-based-deployment)
6. [Environment Variables in Production](#environment-variables-in-production)
7. [Verifying a Production Deployment](#verifying-a-production-deployment)
8. [Known Limitations](#known-limitations)
9. [Future Improvements](#future-improvements)
10. [Recommended Roadmap](#recommended-roadmap)

---

## Deployment Overview

Rainly is designed for cloud deployment on commodity hosting platforms. The recommended production topology is:

| Component | Platform | Service Type |
|-----------|----------|-------------|
| Backend (FastAPI) | Render | Web Service (Python) |
| Frontend (React) | Render | Static Site |
| Database (MongoDB) | MongoDB Atlas | Cloud DBaaS |

The `render.yaml` file at the repository root is a Render Blueprint that automates the creation and linking of both the backend web service and the frontend static site from a single file.

An alternative deployment onto any Ubuntu VPS using systemd services is described in the manual deployment section.

---

## Deploying to Render (Recommended)

### Prerequisites

- A Render account at [https://render.com](https://render.com).
- A MongoDB Atlas cluster with a connection string (see the MongoDB Atlas Setup section below).
- The project pushed to a GitHub repository.

### Step 1: Connect the GitHub Repository to Render

1. Log in to the Render dashboard.
2. Click "New" and select "Blueprint".
3. Connect your GitHub account if not already connected.
4. Select the repository containing the Rainly project.
5. Render will detect the `render.yaml` file automatically.

### Step 2: Configure Environment Variables

Render will prompt you to fill in environment variable values marked as `sync: false` in `render.yaml`. These are intentionally not committed to the repository for security reasons:

| Variable | Value to Provide |
|----------|-----------------|
| `MONGO_URI` | Your full MongoDB Atlas connection string |
| `GMAIL_ADDRESS` | Your Gmail sender address (optional) |
| `GMAIL_APP_PASSWORD` | Your Gmail App Password (optional) |

Any optional variables such as `RESEND_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `GEMINI_API_KEY`, and `LLM_ENABLED` should be added manually in the Render dashboard under the environment section of the backend web service.

### Step 3: Deploy

Click "Apply" in the Render Blueprint wizard. Render will:

1. Create the backend web service named `flood-detection-backend`.
   - Runtime: Python 3.11.9
   - Region: Singapore
   - Build command: `cd backend && pip install -r requirements.txt`
   - Start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

2. Create the frontend static site named `flood-detection-frontend`.
   - Runtime: Node
   - Region: Singapore
   - Build command: `cd frontend && npm install && npm run build`
   - Publish path: `frontend/build`
   - Rewrite rule: All paths (`/*`) rewritten to `/index.html` for client-side routing support.

3. Automatically inject the backend's service URL into the frontend build as `REACT_APP_API_URL`.

### Step 4: Monitor Build Logs

In the Render dashboard, click on each service to monitor the build logs. A successful backend build concludes with a line similar to:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

A successful frontend build concludes with:

```
The build folder is ready to be deployed.
```

### Step 5: Access the Deployed Application

Once both services are live, navigate to the static site URL displayed in the Render dashboard. The frontend will communicate with the backend through the injected `REACT_APP_API_URL`.

### Important Note on WebSocket in Production

Render's Web Services support WebSocket connections natively. The frontend's `useWebSocket` hook automatically uses `wss://` when the page is served over HTTPS, which is correct for Render deployments. No additional configuration is required.

### Render Pricing Consideration

Render's free tier suspends web services after 15 minutes of inactivity and takes up to 60 seconds to spin up on the next request. For a system requiring 24/7 monitoring, a paid instance type (Starter or higher) is recommended to avoid cold starts.

---

## Manual Cloud Deployment (Ubuntu Server)

Use this workflow when deploying to a VPS, AWS EC2, DigitalOcean Droplet, or similar Linux instance.

### Backend Deployment

#### Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip nginx
```

#### Clone the Repository

```bash
git clone https://github.com/your-username/rainly.git /opt/rainly
cd /opt/rainly
```

#### Set Up Python Virtual Environment

```bash
cd /opt/rainly/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Create the Environment File

```bash
cp /opt/rainly/backend/.env.example /opt/rainly/backend/.env
nano /opt/rainly/backend/.env
# Populate all required variables
```

#### Create a systemd Service File

```bash
sudo nano /etc/systemd/system/rainly-backend.service
```

Contents:

```ini
[Unit]
Description=Rainly Flood Detection Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/rainly/backend
Environment="PATH=/opt/rainly/backend/venv/bin"
ExecStart=/opt/rainly/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Enable and Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable rainly-backend
sudo systemctl start rainly-backend
sudo systemctl status rainly-backend
```

#### Configure Nginx as Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/rainly
```

Contents:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Backend API and WebSocket
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/rainly /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Frontend Deployment

#### Build the Frontend

```bash
cd /opt/rainly/frontend
npm install
REACT_APP_API_URL=https://your-domain.com/api npm run build
```

#### Configure Nginx to Serve the Static Build

Update the Nginx configuration to serve the frontend build directory and proxy `/api/` and `/ws/` to the backend:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /opt/rainly/frontend/build;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

#### Enable HTTPS with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Certbot will automatically modify the Nginx configuration to enable HTTPS and set up auto-renewal.

---

## MongoDB Atlas Setup

### Step 1: Create a Free Cluster

1. Visit [https://cloud.mongodb.com](https://cloud.mongodb.com) and create a free account.
2. Click "Build a Database", choose the free M0 tier, and select a cloud region closest to your deployment (Singapore for Render's Singapore region).
3. Choose a cluster name (e.g., `RainlyCluster`).

### Step 2: Create a Database User

1. In the Atlas dashboard, navigate to Database Access.
2. Click "Add New Database User".
3. Choose Password authentication.
4. Set a username (e.g., `rainly-app`) and a strong password.
5. Assign the "Read and write to any database" built-in role.

### Step 3: Configure Network Access

1. Navigate to Network Access.
2. Click "Add IP Address".
3. For Render deployments, click "Allow Access from Anywhere" (`0.0.0.0/0`). This is acceptable for pairing with MongoDB Atlas credential-based authentication.
4. For production VPS deployments, restrict access to the specific server IP address.

### Step 4: Get the Connection String

1. In the Atlas dashboard, click "Connect" on your cluster.
2. Choose "Connect your application".
3. Select Python and any version.
4. Copy the connection string. It will look like:

```
mongodb+srv://rainly-app:<password>@rainklycluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

5. Replace `<password>` with the database user's password.
6. Set this as `MONGODB_URI` in your `.env` file.

---

## Docker-Based Deployment

For teams preferring container-based deployments, the following Dockerfiles and compose configuration provide a containerized setup.

### Backend Dockerfile (`backend/Dockerfile`)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile (`frontend/Dockerfile`)

```dockerfile
FROM node:18-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx configuration for Frontend container (`frontend/nginx.conf`)

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Docker Compose (`docker-compose.yml`)

```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    restart: always

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api
    depends_on:
      - backend
    restart: always
```

Run with:

```bash
docker-compose up --build
```

---

## Environment Variables in Production

### Backend Production `.env` Template

```env
# Required
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority

# Email (configure one provider)
RESEND_API_KEY=re_your_key
# OR
GMAIL_ADDRESS=your.email@gmail.com
GMAIL_PASSWORD=your_app_password

# SMS (optional)
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# LLM (choose one option)
LLM_ENABLED=false
LLM_PROVIDER=google
GEMINI_API_KEY=your_gemini_key
# OR for local:
# LLM_PROVIDER=local
# LLM_MODEL_FILE=qwen2-0_5b-instruct-q4_k_m.gguf
# LLM_MODEL_PATH=models/llm
```

### Frontend Production Environment Variable

The `REACT_APP_API_URL` variable must be set at **build time**, not at runtime, because CRA replaces all `process.env.REACT_APP_*` references with their literal values during the build process. Setting this variable as a Docker environment variable at container start will not work; it must be injected during `npm run build`.

---

## Verifying a Production Deployment

### Health Check

```bash
curl https://your-backend-domain.com/
```

Expected response:

```json
{"message": "Rainly - Early Flood Detection API", "status": "running"}
```

### API Verification

```bash
curl https://your-backend-domain.com/api/regions | python3 -m json.tool
```

### WebSocket Verification

Use the `wscat` utility:

```bash
npm install -g wscat
wscat -c wss://your-backend-domain.com/ws/realtime
{"type": "ping"}
```

Expected server response: `{"type": "pong", "timestamp": "..."}`

### Notification Verification

Submit a CRITICAL-threshold payload via the API and verify that emails and SMS messages are received within 60 seconds:

```bash
curl -X POST https://your-backend-domain.com/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "d010",
    "region_id": "r006",
    "water_level": 65.0,
    "rainfall": 220.0,
    "flow_rate": 4500.0
  }'
```

---

## Known Limitations

### 1. No Authentication Layer

The current implementation has no user authentication or authorization. All API endpoints are publicly accessible. Anyone with the backend URL can create, read, or modify data. For an internal-only dashboard this is acceptable; for a publicly exposed deployment, an authentication mechanism must be added before production use.

### 2. Open CORS Policy

CORS is configured to allow all origins. This should be restricted to the specific frontend domain in production.

### 3. No Physical IoT Device Integration

The current system supports simulated sensor data exclusively. Integration with physical IoT hardware (e.g., through MQTT or HTTPS-based device communication protocols) is not yet implemented. All "real-time" data is software-simulated within the backend simulation engine.

### 4. Local LLM on Render Free Tier

Running a local GGUF model on Render's free instance type is not feasible due to memory constraints (512 MB RAM). The Google Gemini API option or disabling LLM entirely is recommended for Render deployments.

### 5. Database Indexing

The MongoDB collections currently rely on the default `_id` index only. With large warning datasets, query performance for the warnings collection may degrade. Compound index creation on `(region_id, timestamp)` and `(participant_id, timestamp)` is required for production scale.

### 6. No Historical Time-Series Storage

Sensor readings are not individually persisted as time-series documents. Only the most recent reading per device is stored in the device document itself. The warnings collection provides historical data only for alert events, not for continuous sensor telemetry. Long-term hydrological trend analysis is therefore not currently supported.

### 7. Email Personalization Limitation

In Resend's free tier, emails can only be sent to the verified owner email address. In production, a paid Resend account or a properly configured SMTP setup is required to send alerts to arbitrary participant email addresses.

---

## Future Improvements

### 1. Authentication and Role-Based Access Control

Implement an authentication system using JWT tokens. Define at minimum two roles:
- **Viewer**: Read-only access to the dashboard, map, analytics, and warning history.
- **Admin**: Full access including device management, participant management, simulation control, and database seeding.

Integrate OAuth2 via Google or a dedicated identity provider for simplified secure login.

### 2. Physical IoT Device Integration via MQTT

Replace or complement the simulation engine with a real-time MQTT subscriber. Deploy MQTT-compatible microcontrollers (ESP32 or Raspberry Pi Pico W) equipped with ultrasonic water-level sensors and rainfall gauges at physical monitoring locations. The backend MQTT subscriber processes real device payloads identically to the simulation path.

### 3. Time-Series Sensor Data Persistence

Introduce a dedicated `sensor_readings` collection or integrate a time-series database (InfluxDB or MongoDB's native time-series collection type) to persist every sensor tick as a separate document with a high-resolution timestamp. This enables:
- Historical flood event replay.
- Long-term seasonality and trend analysis.
- Machine learning model training on real sensor data.

### 4. Advanced Predictive Modeling

Replace or augment the rule-based risk classifier with a trained machine learning model. Potential approaches include:
- An LSTM (Long Short-Term Memory) neural network trained on multi-day historical sensor sequences to predict flood likelihood 6, 12, and 24 hours in advance.
- A gradient-boosted tree model (XGBoost or LightGBM) trained on features derived from multiple sensor co-readings.
- Integration with India Meteorological Department (IMD) weather forecast data to incorporate predicted rainfall as an input feature.

### 5. Telegram Bot Notifications

Re-introduce Telegram as a third notification channel. A Telegram bot requires only a bot token and the participant's Telegram Chat ID, eliminating the cost and complexity of programmatic SMS. Participants in rural areas with limited cell connectivity who nonetheless have internet access through mobile data may prefer Telegram notifications.

### 6. WhatsApp Business API Integration

Integrate WhatsApp Business through the Meta Cloud API or Twilio's WhatsApp channel. WhatsApp messages have significantly higher open rates than SMS in the Indian market and support rich media (images, documents). Flood risk maps or sensor charts could be sent directly to participants as image attachments.

### 7. Mobile Application

Develop a cross-platform mobile application using React Native or Flutter. Key mobile-specific features:
- GPS-based region auto-detection and automatic subscription.
- Offline map tile caching for use during network disruptions.
- Push notifications via Firebase Cloud Messaging for background alert delivery.
- Emergency contact calling directly from the alert screen.

### 8. Multi-Language Support

Add support for regional Indian languages including Hindi, Bengali, Assamese, Odia, Marathi, and Telugu for both the dashboard interface and notification messages. This is particularly important for participant-facing SMS and email content, as many residents in flood-prone rural areas are more comfortable in their native language.

### 9. Government API and Sensor Network Integration

Integrate with official government data sources:
- **Central Water Commission (CWC) API**: Real-time water level data from official gauging stations.
- **India Meteorological Department (IMD) API**: Live rainfall radar data and rainfall forecast data.
- **National Remote Sensing Centre (NRSC)**: Satellite-derived flood inundation mapping data.

These integrations would transform Rainly from a simulation-capable prototype into a fully operational early warning system backed by authoritative government data.

### 10. Interactive Flood Zone Map Drawing

Extend the Leaflet map interface with polygon drawing tools (using Leaflet Draw or similar) that allow operators to define custom at-risk flood zones, independent of the pre-configured circular region boundaries. Participants residing within a drawn polygon would be auto-enrolled in that zone's alerts.

### 11. Alert Escalation Policy Engine

Build a configurable escalation policy system where alerts are not simply dispatched to all participants simultaneously. Instead, alerts first go to local response coordinators and, if unacknowledged within a configurable time window, escalate to district-level administrators, then to state-level emergency management officers.

### 12. Dashboard Theming and Dark Mode

Implement a full dark mode alternative for the dashboard. Control-room environments often dim screens to reduce eye strain during night shifts, making a dark mode critical for operational usability.

### 13. Horizontal Scaling and Load Balancing

The current single-process architecture is suitable for moderate workloads. To support larger deployments with hundreds of concurrent WebSocket connections and dozens of simultaneous simulations:
- Deploy multiple Uvicorn worker processes behind a load balancer.
- Replace the in-process `ConnectionManager` with a Redis-backed Pub/Sub manager (using `redis-py` and `aioredis`) so that broadcast messages reach clients connected to any worker process.
- Replace the in-process simulation engine task registry with a Celery task queue backed by Redis or RabbitMQ for durable, resumable simulation tasks.

### 14. Automated Database Backups

Configure automated daily MongoDB Atlas backups and set a retention period appropriate for operational requirements. For a disaster management system, a minimum of 30-day backup retention is recommended to support post-event forensic analysis.

### 15. Observability and Monitoring

Add a dedicated observability layer:
- **Structured Logging**: Replace `print` statements with Python's `logging` module using JSON-formatted log output. Forward logs to a log aggregation service (Datadog, Loki, or Amazon CloudWatch).
- **Metrics**: Expose Prometheus-compatible metrics via a `/metrics` endpoint using `starlette-prometheus`. Track request latency, active WebSocket connections, simulation tick frequency, and notification success rates.
- **Health Checks**: Create a `/health` endpoint that checks MongoDB connectivity and reports service readiness. Use this endpoint as the health check URL in Render's service configuration.
- **APM Tracing**: Add OpenTelemetry instrumentation for distributed trace visualization.

---

## Recommended Roadmap

The following phased roadmap prioritizes improvements by impact and implementation effort:

### Phase 1: Immediate Hardening (1-2 weeks)
- Add JWT authentication and basic role-based access control.
- Restrict CORS to the production frontend domain.
- Add MongoDB compound indexes on the `warnings` collection.
- Replace `print` logging with structured `logging` module calls.

### Phase 2: Data Depth (2-4 weeks)
- Implement time-series sensor reading persistence.
- Build historical analytics charts in the Analytics tab drawing from the time-series collection.
- Create a `/health` endpoint for platform health checks.

### Phase 3: Real Hardware Integration (4-8 weeks)
- Implement MQTT subscriber for physical sensor device integration.
- Pilot with two physical monitoring stations (ESP32 + ultrasonic sensors).
- Validate end-to-end alert delivery from physical sensor to participant notification.

### Phase 4: Scale and Reach (2-3 months)
- Integrate IMD weather forecast data for predictive ahead-of-time risk assessment.
- Add WhatsApp Business notification channel.
- Add Hindi and Bengali language support for participant notifications.
- Implement Redis-backed WebSocket broadcasting for horizontal scaling.

### Phase 5: Advanced Intelligence (3-6 months)
- Train and deploy an LSTM flood prediction model on historical CWC sensor data.
- Integrate CWC official gauging station data feeds.
- Develop the React Native mobile application.
- Launch a pilot program with district disaster management authorities in a flood-prone region.
