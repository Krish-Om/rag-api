import uvicorn
from app import app

uvicorn.run(app_dir="./app",app=app.app)