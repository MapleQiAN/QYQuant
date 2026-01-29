# QY_Quant

Vue 3 + Vite 前端，Flask 后端 API。  
Vue 3 + Vite frontend with a Flask backend API.

## 目录 | Table of Contents
- 项目结构 | Project Structure
- 环境要求 | Requirements
- 快速开始 | Quick Start
- 开发说明 | Development Notes
- 接口 | API
- 常见问题 | Troubleshooting

## 项目结构 | Project Structure
- `frontend/` — Vue 3 + Vite 前端应用 | Vue 3 + Vite app
- `backend/` — Flask 后端 API | Flask API

## 环境要求 | Requirements
- Node.js 18+（建议 18/20）| Node.js 18+ (recommended 18/20)
- Python 3.10+
- npm

## 快速开始 | Quick Start

### 后端 | Backend (Flask)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

默认地址 | Default URL: `http://127.0.0.1:5000`

### 前端 | Frontend (Vue + Vite)
```powershell
cd frontend
npm install
npm run dev
```

默认地址 | Default URL: `http://127.0.0.1:5173`

## 开发说明 | Development Notes
- Vite 已配置代理 | Proxy configured: `/api` → `http://127.0.0.1:5000`

## 接口 | API
- `GET /api/health`
- `GET /api/hello`

## 常见问题 | Troubleshooting
- **PowerShell 无法激活虚拟环境 | Cannot activate venv**
  - 运行 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` 后再执行 `Activate.ps1`
- **端口被占用 | Port already in use**
  - 修改后端监听端口或 Vite 配置中的代理目标
