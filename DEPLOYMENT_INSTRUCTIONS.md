# 🚀 Rainly Project Deployment Guide

Follow these steps to deploy your AI-powered flood detection system to Render (or Vercel).

## 1. Prerequisites (Accounts)
*   **GitHub**: Upload this code to a new repository.
*   **Render**: Create an account on [render.com](https://render.com).
*   **MongoDB Atlas**: Have your `MONGODB_URI` ready (ensure network access IP is whitelisted or set to `0.0.0.0/0` for production).
*   **Google Gemini API Key** (Recommended for free cloud hosting): Get one from [aistudio.google.com](https://aistudio.google.com).

## 2. Deploy Backend (Web Service)

1.  **Create New Web Service** on Render.
2.  **Connect GitHub Repo**: Select your project repository.
3.  **Use Default Values**:
    *   **Name**: `rainly-backend` (or similar)
    *   **Region**: Singapore (for faster Indian access) or US/Europe.
    *   **Branch**: `main`
    *   **Root Directory**: `backend`
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
4.  **Environment Variables** (Add these):
    *   `MONGODB_URI`: `mongodb+srv://...` (your full connection string)
    *   `LLM_PROVIDER`: `google` (IMPORTANT: Use 'google' for Render Free Tier to save RAM)
    *   `GEMINI_API_KEY`: `AIzaSy...` (Your API Key)
    *   `LLM_ENABLED`: `true`
    *   `GMAIL_ADDRESS`: your_email@gmail.com (Optional, for alerts)
    *   `GMAIL_APP_PASSWORD`: xxxx-xxxx... (Optional, for alerts)
5.  **Create Web Service**. Wait for deployment to finish.
    *   **Note the URL**: e.g., `https://rainly-backend.onrender.com`

## 3. Deploy Frontend (Static Site)

1.  **Create New Static Site** on Render.
2.  **Connect GitHub Repo**: Same repo.
3.  **Configuration**:
    *   **Name**: `rainly-frontend`
    *   **Root Directory**: `frontend`
    *   **Build Command**: `npm install && npm run build`
    *   **Publish Directory**: `build`
4.  **Environment Variables**:
    *   `REACT_APP_API_URL`: The Backend URL from Step 2 **plus `/api`** (e.g., `https://rainly-backend.onrender.com/api`)
5.  **Create Static Site**. Wait for build.
6.  **Access the URL**: e.g., `https://rainly-frontend.onrender.com`

---

## 🛠️ Configuration Tips

### Why use Google Gemini on Render?
Render's **Free Tier** limits RAM to 512MB. A local LLM (like Qwen 0.5B) needs ~500MB+ just to load, leading to potential crashes or slow performance. The Google Gemini API runs on Google's cloud, using near-zero RAM on your server, making it perfect for free hosting.

### Database Checks
If users or regions don't appear, check your MongoDB Atlas "Network Access". Ensure `0.0.0.0/0` is whitelisted so Render can connect.

### Email Alerts
Make sure to use an **App Password** for Gmail (not your main password) if you enabled 2FA.

---

**✅ You're Live!**
Your system is now monitoring data in real-time on the cloud. 
Test it by opening the frontend URL and using the **Simulator** tab.
