"""
CasareRPA Orchestrator Dashboard
"""
import sys
import asyncio
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                               QPushButton, QHeaderView, QTabWidget, QFileDialog, QMessageBox)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
import qasync
from loguru import logger
from pathlib import Path

from .cloud_service import CloudService

class OrchestratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CasareRPA Orchestrator")
        self.resize(1000, 700)
        
        self.cloud = CloudService()
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("Orchestrator Dashboard")
        header.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Robots Tab
        self.robots_tab = QWidget()
        self.setup_robots_tab()
        self.tabs.addTab(self.robots_tab, "Robots")
        
        # Jobs Tab
        self.jobs_tab = QWidget()
        self.setup_jobs_tab()
        self.tabs.addTab(self.jobs_tab, "Jobs")
        
        # Refresh Timer
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: asyncio.get_event_loop().create_task(self.refresh_data()))
        self.timer.start(5000)
        
        # Initial Load
        asyncio.get_event_loop().create_task(self.refresh_data())

    def setup_robots_tab(self):
        layout = QVBoxLayout(self.robots_tab)
        
        # Toolbar
        toolbar = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(lambda: asyncio.get_event_loop().create_task(self.refresh_data()))
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Table
        self.robots_table = QTableWidget()
        self.robots_table.setColumnCount(5)
        self.robots_table.setHorizontalHeaderLabels(["ID", "Name", "Status", "Last Seen", "Actions"])
        self.robots_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.robots_table)

    def setup_jobs_tab(self):
        layout = QVBoxLayout(self.jobs_tab)
        
        self.jobs_table = QTableWidget()
        self.jobs_table.setColumnCount(5)
        self.jobs_table.setHorizontalHeaderLabels(["Job ID", "Robot", "Workflow", "Status", "Time"])
        self.jobs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.jobs_table)

    async def refresh_data(self):
        """Fetch data from cloud."""
        try:
            robots = await self.cloud.get_robots()
            self.update_robots_table(robots)
            
            jobs = await self.cloud.get_jobs()
            self.update_jobs_table(jobs)
        except Exception as e:
            logger.error(f"Failed to refresh data: {e}")

    def update_robots_table(self, robots):
        self.robots_table.setRowCount(len(robots))
        for i, robot in enumerate(robots):
            self.robots_table.setItem(i, 0, QTableWidgetItem(robot["id"]))
            self.robots_table.setItem(i, 1, QTableWidgetItem(robot["name"]))
            self.robots_table.setItem(i, 2, QTableWidgetItem(robot["status"]))
            self.robots_table.setItem(i, 3, QTableWidgetItem(robot["last_seen"]))
            
            # Dispatch button
            dispatch_btn = QPushButton("Dispatch")
            dispatch_btn.clicked.connect(lambda checked, r=robot: self.dispatch_workflow(r))
            self.robots_table.setCellWidget(i, 4, dispatch_btn)

    def update_jobs_table(self, jobs):
        self.jobs_table.setRowCount(len(jobs))
        for i, job in enumerate(jobs):
            self.jobs_table.setItem(i, 0, QTableWidgetItem(str(job["id"])))
            self.jobs_table.setItem(i, 1, QTableWidgetItem(job.get("robot_id", "N/A")))
            # Truncate workflow JSON for display
            workflow_preview = job.get("workflow", "")[:50] + "..." if len(job.get("workflow", "")) > 50 else job.get("workflow", "")
            self.jobs_table.setItem(i, 2, QTableWidgetItem(workflow_preview))
            self.jobs_table.setItem(i, 3, QTableWidgetItem(job.get("status", "unknown")))
            self.jobs_table.setItem(i, 4, QTableWidgetItem(job.get("created_at", "N/A")))
    
    def dispatch_workflow(self, robot):
        """Open file dialog and dispatch workflow to robot."""
        robot_id = robot["id"]
        robot_name = robot["name"]
        
        # Open file dialog to select workflow
        workflows_dir = Path("workflows")
        if not workflows_dir.exists():
            workflows_dir = Path.cwd()
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select Workflow for {robot_name}",
            str(workflows_dir),
            "Workflow Files (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            # Read workflow file
            with open(file_path, 'r', encoding='utf-8') as f:
                workflow_json = f.read()
            
            # Dispatch asynchronously
            asyncio.get_event_loop().create_task(self._dispatch_job(robot_id, workflow_json, Path(file_path).name))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read workflow file: {e}")
    
    async def _dispatch_job(self, robot_id, workflow_json, filename):
        """Dispatch job to robot."""
        try:
            success = await self.cloud.dispatch_job(robot_id, workflow_json)
            if success:
                QMessageBox.information(self, "Success", f"Workflow '{filename}' dispatched to robot {robot_id}")
                await self.refresh_data()
            else:
                QMessageBox.warning(self, "Failed", "Failed to dispatch workflow")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Dispatch error: {e}")

def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = OrchestratorWindow()
    window.show()
    
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
