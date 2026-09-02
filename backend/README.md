# Backend · FastAPI + JWT

## 启动

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 账号

- `admin` / `123456`
- `teacher` / `123456`

## 主要路由

- `POST /login`
- `GET /user/info`
- `POST /logout`
- `GET /dashboard`
- `GET|POST|PUT|DELETE /course...`
- `GET|POST|PUT|DELETE /teacher...`
- `GET|POST|PUT /student...`
- `GET|POST|DELETE /resource...`
- `POST /ai/generate-intro` `/ai/parse-pdf` `/ai/generate-quiz`
