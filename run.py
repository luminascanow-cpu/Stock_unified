import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    port = int(os.getenv("DASHBOARD_PORT", "8000"))
    host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     📊 Geo-Political Stock Monitor - India                      ║
║                                                                  ║
║     Starting Dashboard at http://{host}:{port}                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    from src.api.main import app
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
