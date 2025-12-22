from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator
import datetime
from loguru import logger


class GeminiParams(BaseModel):
    """Gemini API integration parameters."""

    model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.0
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192
    safety_settings: str = "BLOCK_NONE"
    response_mime_type: str = "text/plain"


class AgentCapability(BaseModel):
    """Agent capability definition."""

    name: str
    description: str
    skills: List[str]


class SkillDefinition(BaseModel):
    """Skill definition with schema."""

    name: str
    description: str
    schema_def: Dict[str, Any]


class SkillExecution(BaseModel):
    """Request to execute a skill."""

    skill_name: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v: Dict[str, Any], info: Any) -> Dict[str, Any]:
        # Logic to validate against skill schema will be handled in SkillManager
        return v


class AgentActivity(BaseModel):
    """Log entry for agent activity."""

    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    agent: str
    action: str
    status: str
    details: Optional[str] = None


class GeminiConfig(BaseModel):
    """Complete Gemini configuration."""

    params: GeminiParams
    agents: List[AgentCapability]
    skills: List[SkillDefinition]


class SkillManager:
    """Manages skill registration and execution."""

    def __init__(self, config: GeminiConfig):
        self.config = config
        self.skills = {s.name: s for s in config.skills}
        self.logger = logger.bind(component="SkillManager")

    def validate_execution(self, execution: SkillExecution):
        """Validate skill execution against its schema."""
        if execution.skill_name not in self.skills:
            raise ValueError(f"Unknown skill: {execution.skill_name}")

        self.skills[execution.skill_name]
        # In a real implementation, we would use jsonschema.validate
        # For now, we log the validation attempt
        self.logger.info(
            f"Validating skill {execution.skill_name} with params {execution.parameters}"
        )

    def log_activity(self, agent: str, action: str, status: str, details: Optional[str] = None):
        """Log agent activity."""
        activity = AgentActivity(agent=agent, action=action, status=status, details=details)
        self.logger.info(f"Agent Activity: {activity.model_dump_json()}")

    async def execute_skill(self, execution: SkillExecution, agent_name: str):
        """Execute a skill with logging and error handling."""
        try:
            self.validate_execution(execution)
            self.log_activity(agent_name, f"execute_skill:{execution.skill_name}", "pending")

            # Actual execution logic would go here
            # result = await self._run_skill(execution)

            self.log_activity(agent_name, f"execute_skill:{execution.skill_name}", "success")
            return {"status": "success", "skill": execution.skill_name}
        except Exception as e:
            self.log_activity(
                agent_name, f"execute_skill:{execution.skill_name}", "failure", str(e)
            )
            logger.error(f"Skill execution failed: {e}")
            raise
