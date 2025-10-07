# Usage Guide - AI Tech News Assistant

## 🚀 Running the Application

### Quick Start Scripts

We provide automated scripts that make running the app incredibly easy!

---

## Windows Users

### First Time Setup
```bash
# Run setup script (only needed once)
setup-dev.bat
```

This will:
- Check Python and Node.js installation
- Create Python virtual environment
- Install all backend dependencies
- Install all frontend dependencies
- Create `.env` file from template
- Create logs directory

### Starting the Application

**With AI Features (Recommended):**
```bash
start-app.bat
```

**Without AI Features (No Ollama needed):**
```bash
start-app.bat --no-ai
```

**Skip Dependency Checks (Faster startup):**
```bash
start-app.bat --skip-deps
```

### What Happens
- Opens 2 command windows:
  - Backend window (port 8001)
  - Frontend window (port 5173)
- Both services start automatically
- Logs appear in their respective windows
- URLs are displayed for easy access

### Stopping the Application
Simply close both command windows or press `Ctrl+C` in each window.

---

## macOS/Linux Users

### First Time Setup
```bash
# Make scripts executable
chmod +x setup-dev.sh start-app.sh

# Run setup (only needed once)
./setup-dev.sh
```

This will:
- Check Python3 and Node.js installation
- Create Python virtual environment
- Install all backend dependencies
- Install all frontend dependencies
- Create `.env` file from template
- Create logs directory

### Starting the Application

**With AI Features (Recommended):**
```bash
./start-app.sh
```

**Without AI Features (No Ollama needed):**
```bash
./start-app.sh --no-ai
```

**Skip Dependency Checks (Faster startup):**
```bash
./start-app.sh --skip-deps
```

**View Help:**
```bash
./start-app.sh --help
```

### What Happens
- Backend starts in background (PID displayed)
- Frontend starts in background (PID displayed)
- Logs are written to `logs/backend.log` and `logs/frontend.log`
- URLs are displayed for easy access
- Script waits for `Ctrl+C` to stop

### Stopping the Application
Press `Ctrl+C` in the terminal. This will gracefully stop both services.

### Viewing Logs
```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs
tail -f logs/frontend.log

# Both at once
tail -f logs/*.log
```

---

## Accessing the Application

Once started, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | Main web interface |
| **Backend API** | http://localhost:8001 | REST API |
| **API Docs** | http://localhost:8001/docs | Swagger UI documentation |
| **Alternative Docs** | http://localhost:8001/redoc | ReDoc documentation |
| **Health Check** | http://localhost:8001/health | System health status |

---

## Common Scenarios

### Scenario 1: Complete Fresh Start
```bash
# Windows
setup-dev.bat
start-app.bat

# macOS/Linux
./setup-dev.sh
./start-app.sh
```

### Scenario 2: Quick Development (Dependencies Already Installed)
```bash
# Windows
start-app.bat --skip-deps

# macOS/Linux
./start-app.sh --skip-deps
```

### Scenario 3: No Ollama Installed (Basic Features Only)
```bash
# Windows
start-app.bat --no-ai

# macOS/Linux
./start-app.sh --no-ai
```

### Scenario 4: Manual Control (Run Services Separately)
```bash
# Terminal 1 - Backend
cd backend
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
python production_main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## Troubleshooting

### Issue: "Python not found"
**Solution:** Install Python 3.9+ from https://www.python.org/downloads/
Make sure to check "Add Python to PATH" during installation.

### Issue: "Node.js not found"
**Solution:** Install Node.js 18+ from https://nodejs.org/
Restart your terminal after installation.

### Issue: "Port 8001 already in use"
**Solution:** Another process is using port 8001. Either:
1. Stop the other process
2. Change the port in `backend/.env`: `PORT=8002`

### Issue: "Port 5173 already in use"
**Solution:** Another process is using port 5173. The frontend will automatically try 5174, 5175, etc.

### Issue: Backend fails to start
**Check:**
1. Virtual environment activated
2. Dependencies installed: `pip install -r requirements.txt`
3. `.env` file exists in backend/
4. Check `logs/backend.log` for errors

### Issue: Frontend fails to start
**Check:**
1. Node modules installed: `npm install`
2. Check `logs/frontend.log` for errors
3. Try deleting `node_modules` and run `npm install` again

### Issue: AI features not working
**Solution:**
1. Install Ollama from https://ollama.com
2. Run: `ollama pull llama3.2:1b`
3. Verify with: `curl http://localhost:11434/api/tags`
4. Restart the application

### Issue: Database errors
**Solution:**
1. Delete `backend/news_production.db`
2. Restart backend (database will be recreated)

---

## Script Features

### Intelligent Dependency Detection
- Checks if dependencies are already installed
- Only installs/updates when needed
- Saves time on subsequent starts

### Environment Validation
- Verifies Python version
- Verifies Node.js version
- Checks for Ollama if AI is enabled
- Creates missing directories

### Automatic Cleanup (Unix/Linux/macOS)
- Graceful shutdown on `Ctrl+C`
- Kills both processes properly
- No zombie processes left behind

### Helpful Output
- Color-coded messages (Unix/Linux/macOS)
- Progress indicators
- Clear instructions
- URL display

---

## Advanced Usage

### Running with Custom Settings

Edit `backend/.env` before starting:
```env
# Change port
PORT=8002

# Disable AI permanently
OLLAMA_HOST=

# Change database
DATABASE_URL=sqlite:///./my_custom.db
```

### Running Only Backend
```bash
cd backend
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
python production_main.py
```

### Running Only Frontend
```bash
cd frontend
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pytest

# Frontend tests
cd frontend
npm test
```

### Building for Production
```bash
# Frontend production build
cd frontend
npm run build
# Output in: frontend/dist/
```

---

## Environment Variables

### Critical Variables
- `SECRET_KEY` - JWT secret (MUST change in production)
- `DATABASE_URL` - Database connection string
- `ALLOWED_ORIGINS` - CORS allowed origins

### Optional Variables
- `OLLAMA_HOST` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model name (default: llama3.2:1b)
- `PORT` - Backend port (default: 8001)
- `DEBUG` - Debug mode (default: false)

See `backend/.env.example` for all options.

---

## Getting Help

### Check Logs
- Windows: Look at the command windows
- Unix/Linux/macOS: Check `logs/` directory

### API Documentation
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### Common Commands
```bash
# Check backend status
curl http://localhost:8001/health

# Check Ollama
curl http://localhost:11434/api/tags

# View Python packages
cd backend && venv/Scripts/activate && pip list

# View npm packages
cd frontend && npm list --depth=0
```

---

## Quick Reference

### File Locations
- Backend code: `backend/app/`
- Frontend code: `frontend/src/`
- Database: `backend/news_production.db`
- Logs: `logs/`
- Environment: `backend/.env`

### Important Scripts
- `setup-dev.bat` / `setup-dev.sh` - First time setup
- `start-app.bat` / `start-app.sh` - Start application
- `backend/production_main.py` - Backend entry point
- `frontend/package.json` - Frontend config

### Default URLs
- Frontend: http://localhost:5173
- Backend: http://localhost:8001
- API Docs: http://localhost:8001/docs

---

**Need more help?** Check:
- [README.md](README.md) - Main documentation
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current project status
- API Docs: http://localhost:8001/docs (when running)
