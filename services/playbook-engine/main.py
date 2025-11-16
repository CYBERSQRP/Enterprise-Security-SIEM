"""
Playbook Engine Service
Executes automated response playbooks
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    BLOCK_IP = "block_ip"
    ISOLATE_ENDPOINT = "isolate_endpoint"
    DISABLE_ACCOUNT = "disable_account"
    SEND_EMAIL = "send_email"
    CREATE_TICKET = "create_ticket"
    RUN_SCRIPT = "run_script"
    SEND_WEBHOOK = "send_webhook"


class PlaybookStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PlaybookAction(BaseModel):
    id: str
    action_type: ActionType
    parameters: Dict[str, Any]
    condition: Optional[str] = None
    retry_count: int = 0
    timeout: int = 300


class Playbook(BaseModel):
    id: UUID
    name: str
    description: str
    trigger: str
    actions: List[PlaybookAction]
    enabled: bool = True
    created_at: datetime
    updated_at: datetime


class PlaybookExecution(BaseModel):
    id: UUID
    playbook_id: UUID
    status: PlaybookStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    context: Dict[str, Any]
    results: Dict[str, Any] = {}


# In-memory storage (would use database in production)
playbooks: Dict[UUID, Playbook] = {}
executions: Dict[UUID, PlaybookExecution] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Playbook Engine Service")
    # Load sample playbooks
    load_sample_playbooks()
    yield
    logger.info("Shutting down Playbook Engine Service")


app = FastAPI(
    title="SIEM Playbook Engine",
    description="Automated response playbook execution",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "playbook-engine"}


@app.get("/api/v1/playbooks", response_model=List[Playbook])
async def list_playbooks():
    return list(playbooks.values())


@app.post("/api/v1/playbooks", response_model=Playbook, status_code=201)
async def create_playbook(playbook: Playbook):
    playbooks[playbook.id] = playbook
    return playbook


@app.get("/api/v1/playbooks/{playbook_id}", response_model=Playbook)
async def get_playbook(playbook_id: UUID):
    if playbook_id not in playbooks:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbooks[playbook_id]


@app.post("/api/v1/playbooks/{playbook_id}/execute", response_model=PlaybookExecution)
async def execute_playbook(playbook_id: UUID, context: Dict[str, Any]):
    if playbook_id not in playbooks:
        raise HTTPException(status_code=404, detail="Playbook not found")

    playbook = playbooks[playbook_id]
    execution = PlaybookExecution(
        id=uuid4(),
        playbook_id=playbook_id,
        status=PlaybookStatus.PENDING,
        started_at=datetime.utcnow(),
        context=context
    )

    executions[execution.id] = execution

    # Execute playbook asynchronously (simplified)
    await execute_playbook_actions(playbook, execution)

    return execution


@app.get("/api/v1/executions/{execution_id}", response_model=PlaybookExecution)
async def get_execution(execution_id: UUID):
    if execution_id not in executions:
        raise HTTPException(status_code=404, detail="Execution not found")
    return executions[execution_id]


async def execute_playbook_actions(playbook: Playbook, execution: PlaybookExecution):
    """Execute playbook actions"""
    execution.status = PlaybookStatus.RUNNING
    results = {}

    try:
        for action in playbook.actions:
            logger.info(f"Executing action: {action.action_type}")

            # Simulate action execution
            result = await execute_action(action, execution.context)
            results[action.id] = result

        execution.status = PlaybookStatus.COMPLETED
        execution.results = results
        execution.completed_at = datetime.utcnow()

    except Exception as e:
        logger.error(f"Playbook execution failed: {e}")
        execution.status = PlaybookStatus.FAILED
        execution.results = {"error": str(e)}


async def execute_action(action: PlaybookAction, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single action"""
    if action.action_type == ActionType.BLOCK_IP:
        return {"status": "success", "action": "IP blocked", "ip": action.parameters.get("ip")}
    elif action.action_type == ActionType.ISOLATE_ENDPOINT:
        return {"status": "success", "action": "Endpoint isolated", "endpoint": action.parameters.get("endpoint_id")}
    elif action.action_type == ActionType.DISABLE_ACCOUNT:
        return {"status": "success", "action": "Account disabled", "account": action.parameters.get("username")}
    elif action.action_type == ActionType.SEND_EMAIL:
        return {"status": "success", "action": "Email sent", "to": action.parameters.get("to")}
    elif action.action_type == ActionType.CREATE_TICKET:
        return {"status": "success", "action": "Ticket created", "ticket_id": "INC-12345"}
    else:
        return {"status": "success", "action": str(action.action_type)}


def load_sample_playbooks():
    """Load sample playbooks"""
    brute_force_playbook = Playbook(
        id=uuid4(),
        name="Brute Force Response",
        description="Automated response to brute force attacks",
        trigger="brute_force_detected",
        actions=[
            PlaybookAction(
                id="action-1",
                action_type=ActionType.BLOCK_IP,
                parameters={"ip": "{source_ip}", "duration": 3600}
            ),
            PlaybookAction(
                id="action-2",
                action_type=ActionType.SEND_EMAIL,
                parameters={"to": "security@company.com", "subject": "Brute Force Attack Blocked"}
            ),
            PlaybookAction(
                id="action-3",
                action_type=ActionType.CREATE_TICKET,
                parameters={"title": "Investigate Brute Force Attack", "priority": "high"}
            )
        ],
        enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    playbooks[brute_force_playbook.id] = brute_force_playbook

    malware_playbook = Playbook(
        id=uuid4(),
        name="Malware Containment",
        description="Isolate infected endpoints",
        trigger="malware_detected",
        actions=[
            PlaybookAction(
                id="action-1",
                action_type=ActionType.ISOLATE_ENDPOINT,
                parameters={"endpoint_id": "{endpoint_id}"}
            ),
            PlaybookAction(
                id="action-2",
                action_type=ActionType.DISABLE_ACCOUNT,
                parameters={"username": "{user_account}"}
            ),
            PlaybookAction(
                id="action-3",
                action_type=ActionType.CREATE_TICKET,
                parameters={"title": "Malware Incident Response", "priority": "critical"}
            )
        ],
        enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    playbooks[malware_playbook.id] = malware_playbook


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8084, reload=False)
