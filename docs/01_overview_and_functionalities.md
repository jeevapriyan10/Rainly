# Rainly - Early Flood Detection System
## Document 1: General Overview, Functionalities, and Technology Stack

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [System Objectives](#system-objectives)
4. [Core Functionalities](#core-functionalities)
5. [Technology Stack](#technology-stack)
6. [System Capabilities at a Glance](#system-capabilities-at-a-glance)
7. [Geographic Coverage](#geographic-coverage)
8. [Notification Channels](#notification-channels)

---

## Project Overview

Rainly is a full-stack, real-time flood detection and early warning platform built to monitor hydrological conditions across major Indian river basins. The system ingests data from IoT-based water-level and rainfall sensors, processes that data through a multi-layered risk prediction engine, and dispatches timely flood warnings to registered participants via SMS and Email. A secondary simulation engine is also included, enabling administrators and researchers to replicate real-world flood scenarios for testing and training without requiring physical hardware.

The system is designed to operate in two modes simultaneously:

- **Live IoT Mode**: Real physical sensors push data payloads to the backend through REST endpoints. The system processes each payload and determines the flood risk in near real time.
- **Simulation Mode**: A built-in software simulation engine generates realistic, physics-inspired sensor readings for any registered device. These synthetic readings follow configurable trends (rising, falling, stable, or random) and variability speeds, closely approximating actual field conditions.

Both modes push results to a React-based operator dashboard over WebSocket, allowing control-room operators to observe the system state in real time without manually refreshing the page.

---

## Problem Statement

India experiences some of the most severe annual flooding in the world. Rivers such as the Ganges, Brahmaputra, Godavari, Krishna, Narmada, Yamuna, and Mahanadi regularly breach danger levels during monsoon months, displacing millions of people and causing significant loss of life and property. Official warning dissemination through government channels is frequently delayed, and information does not always reach residents in flood-prone areas with adequate lead time.

Rainly addresses this gap by providing an automated, sensor-driven flood detection network that:

- Continuously monitors river water levels, rainfall intensity, and volumetric flow rates at geographically distributed sensor stations.
- Evaluates incoming readings against scientifically determined danger thresholds.
- Immediately classifies risk severity into one of four levels: LOW, MEDIUM, HIGH, or CRITICAL.
- Dispatches personalized, actionable alert messages directly to individual residents registered in at-risk areas.
- Displays a live operational dashboard to enable operators to overview the situation across all monitored regions at once.

---

## System Objectives

| Objective | Description |
|-----------|-------------|
| Early Warning | Detect flood risk conditions before water levels exceed safe thresholds and notify residents with sufficient lead time for action. |
| Multi-Region Coverage | Monitor multiple river basins and regions across different Indian states from a single unified platform. |
| Real-Time Visibility | Provide live updates to operators through a WebSocket-connected dashboard, reflecting device status changes within seconds. |
| Autonomous Notification | Automatically send formatted SMS and Email alerts to all registered participants in an affected region without manual intervention. |
| AI-Augmented Analysis | Optionally integrate a Large Language Model (LLM) to generate contextual risk reasoning and personalized alert email content. |
| Simulation and Testing | Enable full system testing through a built-in simulation engine that generates realistic sensor data without requiring physical devices. |
| Extensibility | Maintain a clean API surface and modular backend architecture to facilitate future integration with additional sensor types, notification channels, or data sources. |

---

## Core Functionalities

### 1. Region and River Basin Management

The system maintains a persistent registry of monitored regions. Each region entry records the geographic coordinates (latitude and longitude), the name of the associated river, the Indian state and district, and the current risk classification. Ten regions are pre-seeded across five major river basins at platform initialization and administrators may create additional regions through the REST API at any time.

### 2. IoT Sensor Device Registry

Physical or simulated sensor devices are registered against a specific region. Each device record stores the device identifier, the danger threshold water level specific to that measurement station, the current active or inactive status, the most recently recorded water level, rainfall, and flow rate values, and the battery charge percentage. This registry enables the system to track sensor health, apply region-specific thresholds, and correlate incoming data payloads with the correct geographic area.

### 3. Participant Registry and Notification Subscription

Residents in flood-prone areas are registered as participants in the system. Each participant record contains the participant's full name, age, phone number, email address, and a reference to the region they inhabit. When a flood warning is generated for a region, every participant linked to that region receives an alert through all configured notification channels. This design ensures broad, targeted coverage without the need for participants to subscribe manually each time a warning is issued.

### 4. Flood Risk Prediction Engine

The prediction engine evaluates incoming sensor payloads using a weighted multi-factor model:

- **Water Level Ratio (50% weight)**: The ratio of the current water level to the device-specific alert threshold.
- **Rainfall Intensity (30% weight)**: The current rainfall reading normalized against a maximum expected reference of 200 mm.
- **Flow Rate (20% weight)**: The current volumetric flow rate normalized against a maximum reference of 3,000 cubic meters per second.

The combined weighted score determines a risk classification. The system applies the following graduated decision rules:

- **CRITICAL**: Water level at or above 120% of threshold, or rainfall at or above 200 mm. Immediate evacuation required.
- **HIGH**: Water level at or above 110% of threshold, or rainfall at or above 150 mm. Evacuation recommended.
- **MEDIUM**: Water level at or above threshold, or rainfall at or above 75 mm. Preparation for evacuation advised.
- **LOW**: All readings below threshold levels. Continued monitoring recommended.

### 5. Real-Time Simulation Engine

The simulation engine generates synthetic sensor data streams for registered devices. Each simulation run accepts a starting water level, rainfall intensity, flow rate, a trend direction (rising, falling, stable, or random), and a speed multiplier. The engine applies stochastic increments or decrements to sensor values every two seconds and broadcasts the results over WebSocket. When simulated readings reach CRITICAL levels, the engine triggers the full alert pipeline identically to live sensor data, dispatching real SMS and Email notifications to registered participants. This makes the simulation engine useful both for functional testing and for preparing personnel through realistic flood scenario drills.

### 6. Automated Multi-Channel Notification System

When a warning is generated, the system dispatches notifications through two channels:

- **SMS via Twilio**: A concise, high-priority text message of up to 160 characters delivers the region name, river name, risk level, current water level, safety threshold, and the recommended action directly to the participant's mobile phone.
- **Email via Gmail SMTP or Resend API**: A richly formatted HTML email is delivered to the participant's email address. The email includes the full sensor readings, a color-coded risk indicator, a list of recommended safety actions scaled to the risk level, and emergency helpline numbers. If the LLM integration is enabled, the email body is generated dynamically by the language model with contextual reasoning specific to the current sensor conditions.

### 7. Live Analytics Dashboard

The analytics endpoint aggregates system-wide metrics and delivers them to the frontend dashboard component. Aggregated data includes total device count, active device count, the count of devices currently reporting above-threshold water levels, and the ten most recent warning records. These figures are displayed through summary statistic cards, a risk distribution pie chart, a water level and rainfall trend line chart, and a tabular warning log.

### 8. LLM Integration (Optional)

The system supports an optional LLM integration layer that augments both real-time analysis and notification content. Two LLM provider modes are supported:

- **Local Mode**: A small quantized GGUF model (TinyLlama at 669 MB, Qwen2-0.5B at 352 MB, or Phi-2 at 1.6 GB) is loaded and executed using the `llama-cpp-python` inference library at CPU level. This mode operates entirely offline and incurs no API costs.
- **Google Gemini Mode**: The system connects to Google's Gemini Pro API using an API key. This mode delivers higher-quality reasoning without requiring local model storage.

When LLM is enabled, the system uses the language model to generate structured risk analysis JSON objects during high-risk simulation ticks and to compose personalized flood warning email bodies for participant notifications.

---

## Technology Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | FastAPI | >= 0.110.0 |
| ASGI Server | Uvicorn | >= 0.29.0 |
| Database Driver | Motor (Async MongoDB) | >= 3.4.0 |
| Data Validation | Pydantic | >= 2.7.0 |
| Environment Management | python-dotenv | >= 1.0.0 |
| WebSocket Support | websockets | >= 12.0 |
| SMS Notifications | Twilio | >= 9.0.0 |
| Email Notifications | smtplib (SMTP), Resend API | Standard Library / REST |
| AI - Cloud LLM | google-generativeai | >= 0.4.1 |
| AI - Local LLM | llama-cpp-python | >= 0.2.70 |
| HTTP Client | requests | >= 2.31.0 |
| Progress Tracking | tqdm | >= 4.66.0 |
| Language | Python | 3.11+ |

### Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| UI Framework | React | ^18.2.0 |
| DOM Rendering | react-dom | ^18.2.0 |
| Routing | react-router-dom | ^6.21.1 |
| Build Tooling | react-scripts (CRA) | 5.0.1 |
| Map Rendering | Leaflet + react-leaflet | ^1.9.4 / ^4.2.1 |
| Data Visualization | Recharts | ^2.10.3 |
| Language | JavaScript (ES2020+) | - |

### Database

| Component | Technology |
|-----------|-----------|
| Primary Database | MongoDB (Atlas or self-hosted) |
| Async ORM Layer | Motor (AsyncIOMotorClient) |
| Schema Enforcement | Pydantic models on backend |

### Infrastructure and Deployment

| Component | Technology |
|-----------|-----------|
| Cloud Hosting | Render (Backend: Web Service, Frontend: Static Site) |
| Database Hosting | MongoDB Atlas |
| Region | Singapore (configurable) |
| Backend Build | `pip install -r requirements.txt` |
| Backend Start | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Frontend Build | `npm install && npm run build` |
| Configuration | `render.yaml` (Infrastructure as Code) |

---

## System Capabilities at a Glance

| Capability | Status |
|-----------|--------|
| Real-time WebSocket data streaming | Supported |
| Rule-based flood risk prediction | Supported |
| LLM-augmented risk analysis (Local) | Optional (configurable) |
| LLM-augmented risk analysis (Google Gemini) | Optional (configurable) |
| SMS notifications via Twilio | Optional (configurable) |
| Email notifications via Gmail SMTP | Optional (configurable) |
| Email notifications via Resend API | Optional (configurable) |
| Interactive simulation with configurable trends | Supported |
| Multi-region monitoring | Supported (10 regions pre-seeded) |
| Battery level monitoring for devices | Supported |
| Alert cooldown and rate limiting | Supported (30-minute per-participant, 15-minute per-device) |
| Browser push notifications | Supported (Notification API) |
| Interactive map with region markers | Supported (Leaflet) |
| Analytics charts and visualizations | Supported (Recharts) |

---

## Geographic Coverage

The system is pre-seeded with monitoring coverage across ten regions spanning five major Indian river basins and eight Indian states:

| River Basin | Regions Covered | States |
|------------|----------------|--------|
| Ganges | Haridwar, Varanasi, Patna | Uttarakhand, Uttar Pradesh, Bihar |
| Yamuna | Delhi, Agra | Delhi, Uttar Pradesh |
| Brahmaputra | Guwahati | Assam |
| Godavari | Nashik | Maharashtra |
| Krishna | Vijayawada | Andhra Pradesh |
| Narmada | Jabalpur | Madhya Pradesh |
| Mahanadi | Cuttack | Odisha |

---

## Notification Channels

### SMS Message Format

The SMS notification condenses the alert into a concise, urgency-coded message. For a CRITICAL alert, the message reads: `[CRITICAL] FLOOD at {Region}, {River}! Water {level}m (limit {threshold}m). EVACUATE NOW!`. For lower risk levels, the tone and action verb are adjusted proportionally.

### Email Notification Format

The HTML email notification is structured into the following sections:

1. **Color-coded header bar** with the risk level and region name displayed prominently.
2. **Personalized greeting** addressing the participant by name.
3. **Current sensor readings** in a two-column data grid showing water level against threshold and current rainfall.
4. **Risk-appropriate action list** recommending specific safety measures calibrated to the current risk level.
5. **Emergency contact numbers** including the National Disaster Response Force helpline (1078), Police (100), and Ambulance (108).
6. **System attribution footer** identifying the message as originating from the Rainly automated system.

When LLM email generation is enabled, the algorithmic template is replaced with a dynamically generated 200-word alert body authored by the language model, structured around current sensor conditions, immediate threat assessment, and specific safety recommendations.
