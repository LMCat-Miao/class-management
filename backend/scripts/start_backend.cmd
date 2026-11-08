@echo off
REM 本地演示：启动 FastAPI（勿写入真实密码）
cd /d "%~dp0.."
if not exist ".venv\Scripts\activate.bat" (
  echo [ERROR] 未找到 backend\.venv ，请先创建虚拟环境并安装 requirements.txt
  exit /b 1
)
call .venv\Scripts\activate.bat
echo Starting API at http://127.0.0.1:8000  (docs: /docs)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
