import pytest
import asyncio
from PySide6.QtWidgets import QApplication
from casare_rpa.orchestrator.main_window import OrchestratorWindow
from casare_rpa.orchestrator.cloud_service import CloudService

@pytest.fixture
def qapp(qapp):
    return qapp

from unittest.mock import patch, MagicMock

def test_orchestrator_window_creation(qapp):
    # Create a mock event loop to avoid the "no current event loop" error
    mock_loop = MagicMock()

    with patch('asyncio.get_event_loop', return_value=mock_loop):
        with patch('asyncio.create_task'):
            window = OrchestratorWindow()
            assert window.windowTitle() == "CasareRPA Orchestrator"
            window.close()

@pytest.mark.asyncio
async def test_cloud_service():
    service = CloudService()
    assert service.connected is False
    
    await service.connect()
    assert service.connected is True
    
    robots = await service.get_robots()
    assert len(robots) > 0
