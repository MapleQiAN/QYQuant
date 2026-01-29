# QY_Quant（Vue 前端 + Flask 后端）

## 目录结构

- `frontend/`：Vue3 + Vite 前端
- `backend/`：Flask 后端 API

## 后端（Flask）启动

建议使用 Python 3.10+。

在 PowerShell 中：

```powershell
cd "f:\Web Projects\QY_Quant\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

默认监听：`http://127.0.0.1:5000`

接口：

- `GET /api/health`
- `GET /api/hello`

## 前端（Vue + Vite）启动

需要 Node.js 18+（建议 18/20）。

```powershell
cd "f:\Web Projects\QY_Quant\frontend"
npm install
npm run dev
```

默认监听：`http://127.0.0.1:5173`

前端已配置开发代理：`/api` -> `http://127.0.0.1:5000`

## 一键启动脚本（推荐）

在项目根目录使用 `start.ps1` 一键启动前后端（会自动创建虚拟环境并安装依赖）：

```powershell
cd "f:\Web Projects\QY_Quant"
.\start.ps1
```

如果你已经安装好依赖，只想单纯启动服务，可跳过安装步骤：

```powershell
cd "f:\Web Projects\QY_Quant"
.\start.ps1 -NoInstall
```


