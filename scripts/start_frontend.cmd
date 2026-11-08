@echo off
REM 本地演示：启动 Vite 前端（仓库根目录，不是 frontend/ 子目录）
cd /d "%~dp0.."
if not exist "package.json" (
  echo [ERROR] 请在仓库根目录执行，或直接双击本脚本
  exit /b 1
)
echo Starting frontend (default http://localhost:5173)
echo Ensure VITE_USE_MOCK=false and VITE_API_URL=http://127.0.0.1:8000 in .env.development
npm run dev
