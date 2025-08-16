@echo off
REM AI Tech News Assistant - Quick Deploy Setup (Windows)

echo 🚀 AI Tech News Assistant - Quick Deploy Setup
echo ==============================================

REM Check if we're in the right directory
if not exist "docker-compose.yml" (
    echo ❌ Error: Please run this script from the project root directory
    pause
    exit /b 1
)

echo.
echo 📋 Let's set up your deployment configuration...
echo.

REM Get user preferences
set /p DEPLOY_TYPE="Deploy type (local/cloud) [cloud]: "
if "%DEPLOY_TYPE%"=="" set DEPLOY_TYPE=cloud

set /p BACKEND_SERVICE="Backend service (railway/render/docker) [railway]: "
if "%BACKEND_SERVICE%"=="" set BACKEND_SERVICE=railway

set /p FRONTEND_SERVICE="Frontend service (vercel/netlify/docker) [vercel]: "
if "%FRONTEND_SERVICE%"=="" set FRONTEND_SERVICE=vercel

echo.
echo 🔧 Configuration Summary:
echo • Deploy type: %DEPLOY_TYPE%
echo • Backend: %BACKEND_SERVICE%
echo • Frontend: %FRONTEND_SERVICE%
echo.

if "%DEPLOY_TYPE%"=="local" (
    echo 🐳 Setting up local Docker deployment...
    
    REM Create local environment file
    copy .env.production .env.local > nul
    
    echo ✅ Local setup complete!
    echo.
    echo 🚀 To deploy locally:
    echo    docker-compose up -d
    echo.
    echo 📊 Monitor your deployment:
    echo    docker-compose logs -f
    echo.
    echo 🌐 Access your app:
    echo    • Frontend: http://localhost:3000
    echo    • Backend: http://localhost:8000
    echo    • API Docs: http://localhost:8000/docs
    
) else (
    echo ☁️ Setting up cloud deployment...
    
    if "%BACKEND_SERVICE%"=="railway" (
        echo.
        echo 🚂 Railway Backend Setup:
        echo 1. Install Railway CLI: npm install -g @railway/cli
        echo 2. Login: railway login
        echo 3. Create project: railway link
        echo 4. Deploy: railway up
        echo.
        echo 📋 Environment variables to set in Railway:
        echo    • ENVIRONMENT=production
        echo    • DEBUG=false
        echo    • CORS_ORIGINS=https://your-frontend-url.vercel.app
    )
    
    if "%BACKEND_SERVICE%"=="render" (
        echo.
        echo 🎨 Render Backend Setup:
        echo 1. Go to render.com and connect your GitHub repo
        echo 2. Create a new Web Service
        echo 3. Use the included render.yaml configuration
        echo 4. Add environment variables in Render dashboard
    )
    
    if "%FRONTEND_SERVICE%"=="vercel" (
        echo.
        echo ▲ Vercel Frontend Setup:
        echo 1. Install Vercel CLI: npm install -g vercel
        echo 2. Navigate to frontend: cd frontend
        echo 3. Deploy: vercel
        echo 4. Set environment variable:
        echo    vercel env add VITE_API_BASE_URL https://your-backend-url
    )
    
    if "%FRONTEND_SERVICE%"=="netlify" (
        echo.
        echo 🌐 Netlify Frontend Setup:
        echo 1. Go to netlify.com and connect your GitHub repo
        echo 2. Set build directory: frontend/dist
        echo 3. Set build command: npm run build
        echo 4. Add environment variable VITE_API_BASE_URL
    )
    
    echo.
    echo 🔗 After deployment, update these URLs:
    echo 1. Update CORS_ORIGINS in backend with your frontend URL
    echo 2. Update VITE_API_BASE_URL in frontend with your backend URL
    echo.
    echo 📚 See DEPLOYMENT.md for detailed instructions
)

echo.
echo ✨ Next steps:
echo 1. Review and customize .env.production
echo 2. Follow the service-specific setup instructions above
echo 3. Test your deployment with the health endpoints
echo 4. Add monitoring and custom domains as needed
echo.
echo 🎉 Happy deploying!
echo.
pause
