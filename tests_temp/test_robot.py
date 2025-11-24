import pytest
import asyncio
from casare_rpa.robot.agent import RobotAgent
from casare_rpa.robot.config import get_robot_id

@pytest.mark.asyncio
async def test_robot_initialization():
    agent = RobotAgent()
    assert agent.robot_id is not None
    assert agent.name is not None
    assert agent.running is False
    assert agent.connected is False

@pytest.mark.asyncio
async def test_robot_id_persistence(tmp_path, monkeypatch):
    # Mock config path to use tmp_path
    monkeypatch.setattr("casare_rpa.robot.config.ROBOT_ID_FILE", tmp_path / "robot_id")
    
    id1 = get_robot_id()
    id2 = get_robot_id()
    
    assert id1 == id2
    assert len(id1) > 0
