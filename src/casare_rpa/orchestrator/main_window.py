"""
CasareRPA Orchestrator Dashboard
"""
import sys
import asyncio
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                               QPushButton, QHeaderView, QTabWidget)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
import qasync
from loguru import logger

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
        self.robots_table.setColumnCount(4)
        self.robots_table.setHorizontalHeaderLabels(["ID", "Name", "Status", "Last Seen"])
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

    def update_jobs_table(self, jobs):
        self.jobs_table.setRowCount(len(jobs))
        for i, job in enumerate(jobs):
            self.jobs_table.setItem(i, 0, QTableWidgetItem(job["id"]))
            self.jobs_table.setItem(i, 1, QTableWidgetItem(job["robot_id"]))
            self.jobs_table.setItem(i, 2, QTableWidgetItem(job["workflow"]))
            self.jobs_table.setItem(i, 3, QTableWidgetItem(job["status"]))
            self.jobs_table.setItem(i, 4, QTableWidgetItem(job["time"]))

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
