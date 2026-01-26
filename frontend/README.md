# CloudNexus Frontend

A Mobile-First Web Application built with React, Vite, and Tailwind CSS. Designed to simulate a native feel for the CloudNexus API.

## Features
- 📱 **Mobile-First Design**: Locked viewport (max-w-md) to simulate mobile app experience on desktop browsers.
- 🎨 **Modern UI**: Built with Tailwind CSS v4 and Lucide Icons.
- 🔐 **Authentication**: Simulated Bearer Token implementation for secure API consumption.
- ⚡ **Fast Performance**: Powered by Vite.

## Setup Instructions

### 1. Prerequisites
- Node.js (v18 or higher)
- npm or yarn

### 2. Installation
```bash
# Navigate to the project directory
cd frontend

# Install dependencies
npm install
```

### 3. Environment Headers
Create a `.env` file in the root of the frontend directory (if not exists):

```env
# Backend API URL
VITE_API_URL=http://localhost:8000

# Security Token (Must match API_TOKEN in Backend)
VITE_API_TOKEN=simulated-secret-token-lks-2025
```

### 4. Running Development Server
```bash
npm run dev
```
Open `http://localhost:5173` in your browser.
> **Tip**: Open Chrome DevTools (F12) and toggle "Device Toolbar" (Ctrl+Shift+M) to simulated iPhone/Android view.

## Project Structure

```
frontend/
├── src/
│   ├── components/   # Reusable UI components (BottomNav, etc.)
│   ├── layouts/      # Layout wrappers (MobileLayout)
│   ├── pages/        # Application screens (Home, Tasks, Create)
│   ├── services/     # API integration logic (Axios)
│   ├── App.jsx       # Main routing
│   └── main.jsx      # Entry point
├── .env              # Environment configuration
└── vite.config.js    # Vite configuration
```

## Deployment Note (LKS Competition)

This folder is designed to be independent. You can move the entire `frontend` folder to a separate location (e.g., `../CloudNexus-Frontend`) and it will work perfectly as long as `VITE_API_URL` points to the running backend.
