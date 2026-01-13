import os
import uvicorn
uvicorn.run('fvpn_manager.api_server:app', host='0.0.0.0', port=int(os.getenv('MANAGER_API_PORT','8080')))
