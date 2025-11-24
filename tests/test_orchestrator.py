import pytest
from PySide6.QtWidgets import QApplication
from casare_rpa.orchestrator.main_window import OrchestratorWindow
from casare_rpa.orchestrator.cloud_service import CloudService

@pytest.fixture
def qapp(qapp):
    return qapp

from unittest.mock import patch

def test_orchestrator_window_creation(qapp):
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
