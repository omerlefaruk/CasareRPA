import pytest
from unittest.mock import MagicMock, patch
from casare_rpa.orchestrator.cloud_service import CloudService
from casare_rpa.robot.agent import RobotAgent

@pytest.mark.asyncio
async def test_cloud_service_get_robots():
    with patch("casare_rpa.orchestrator.cloud_service.create_client") as mock_create:
        # Mock Client
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        
        # Mock Response
        mock_response = MagicMock()
        mock_response.data = [{"id": "robot-1", "name": "Test Bot"}]
        
        # Mock Chain: table().select().order().execute()
        mock_client.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        service = CloudService()
        # Inject mock client directly to bypass connect() env check if needed, 
        # but connect() handles it. Let's mock env vars too if needed, 
        # but here we just want to test the logic after connection.
        service.client = mock_client
        service.connected = True
        
        robots = await service.get_robots()
        assert len(robots) == 1
        assert robots[0]["id"] == "robot-1"

@pytest.mark.asyncio
async def test_robot_agent_check_jobs():
    with patch("casare_rpa.robot.agent.create_client") as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.data = [{"id": "job-1", "workflow": "test-flow"}]
        
        # Mock Chain: table().select().eq().eq().execute()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
        
        agent = RobotAgent()
        agent.client = mock_client
        agent.connected = True
        agent.robot_id = "test-robot"
        
        # Mock process_job to avoid actual execution logic
        with patch.object(agent, "process_job") as mock_process:
            await agent.check_for_jobs()
            mock_process.assert_called_once()
