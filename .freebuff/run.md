# Run Doc — AI Workforce Coach

## How to Reproduce Artifacts

1. Copy the GEMINI_API_KEY from the main checkout's environment (or set it fresh):
   ```
   export GEMINI_API_KEY="your_key_here"
   ```
2. Install dependencies:
   ```
   cd Retail-Industry-The-Customer-Experience-Consistency-Challenge-main/backend
   pip install -r requirements.txt
   ```
   Note: If bcrypt version conflicts occur, pin `bcrypt==4.0.1`.

3. The SQLite database is auto-created and seeded on first startup (10 stores, 127+ associates).

## How to Run the Server

```bash
cd Retail-Industry-The-Customer-Experience-Consistency-Challenge-main/backend
export GEMINI_API_KEY="your_key_here"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- **URL**: http://localhost:8000
- **Demo accounts**: employee@demo.com / employee123, manager@demo.com / manager123, admin@demo.com / admin123
- **Gemini fallback**: If GEMINI_API_KEY is not set, the AI simulation falls back to mock responses automatically.

## Windows Detach (PowerShell)

```powershell
$env:GEMINI_API_KEY='your_key_here'
(Start-Process -FilePath 'python.exe' -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000' -WorkingDirectory '<backend_dir>' -RedirectStandardOutput '<log>' -RedirectStandardError '<log>.err' -WindowStyle Hidden -PassThru).Id
```
