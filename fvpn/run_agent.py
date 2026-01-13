import os
import uvicorn
from fvpn_agent.config import load_agent_settings
s=load_agent_settings()
uvicorn.run('fvpn_agent.agent_api:app', host=s.listen_host, port=s.listen_port)
