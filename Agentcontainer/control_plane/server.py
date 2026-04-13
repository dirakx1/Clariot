"""
Clariot Agent Control Plane - REST/WebSocket API for user interaction
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Clariot Agent Control Plane")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance (initialized on startup)
agent = None
llm_gateway = None


@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    global agent, llm_gateway
    
    from ..agent_core.agent import ClariotAgent
    from ..llm_gateway.gateway import LLMGateway
    
    # Initialize LLM gateway
    llm_gateway = LLMGateway()
    
    # Initialize agent
    agent = ClariotAgent(
        agent_id=os.getenv("AGENT_ID", "clariot_agent_1"),
        layer=os.getenv("AGENT_LAYER", "things"),
        llm_gateway=llm_gateway
    )
    
    logger.info("Clariot Agent Control Plane started")
    logger.info(f"LLM Provider: {llm_gateway.provider}")
    logger.info(f"LLM Model: {llm_gateway.model}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": agent.agent_id if agent else None,
        "layer": agent.layer if agent else None
    }


@app.get("/agent/status")
async def get_agent_status():
    """Get current agent status and state."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "agent_id": agent.agent_id,
        "layer": agent.layer,
        "is_running": agent.is_running,
        "current_state": agent.memory.get_current_state(),
        "llm_provider": llm_gateway.provider,
        "llm_model": llm_gateway.model
    }


@app.post("/agent/query")
async def query_agent(request: Dict[str, Any]):
    """
    Query the agent with a natural language command.
    
    Request body:
    {
        "message": "What's the temperature in the factory?"
    }
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    message = request.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    
    result = await agent.handle_user_command(message)
    return result


@app.post("/agent/command")
async def send_command(request: Dict[str, Any]):
    """
    Send a structured command to actuators.
    
    Request body:
    {
        "actuator_id": "motor_1",
        "command": "start",
        "parameters": {"speed": 100}
    }
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    actuator_id = request.get("actuator_id")
    command = request.get("command")
    
    if not actuator_id or not command:
        raise HTTPException(status_code=400, detail="actuator_id and command are required")
    
    actions = [{
        "actuator_id": actuator_id,
        "command": command,
        "parameters": request.get("parameters", {})
    }]
    
    results = await agent.actuator_controller.execute_actions(actions)
    return {"results": results}


@app.get("/agent/memory/recent")
async def get_recent_memory(window_minutes: int = 10):
    """Get recent agent memory entries."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    context = agent.memory.get_recent_context(window_minutes)
    return {"entries": context, "count": len(context)}


@app.get("/agent/sensors")
async def get_current_sensors():
    """Get current state of all sensors."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {"sensors": agent.memory.get_current_state()}


# WebSocket endpoint for real-time interaction
class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent interaction.
    
    Send messages and receive responses in real-time.
    """
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "agent_id": agent.agent_id if agent else None,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message = data.get("message")
            if not message:
                continue
            
            # Process message
            result = await agent.handle_user_command(message)
            
            # Send response
            await websocket.send_json({
                "type": "response",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/sensors")
async def websocket_sensors(websocket: WebSocket):
    """
    WebSocket endpoint for real-time sensor data streaming.
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Get current sensor state
            sensors = agent.memory.get_current_state() if agent else {}
            
            await websocket.send_json({
                "type": "sensor_update",
                "sensors": sensors,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Wait before next update
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket sensor error: {e}")
        manager.disconnect(websocket)


def start_server():
    """Start the control plane server."""
    port = int(os.getenv("CONTROL_PLANE_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    start_server()
