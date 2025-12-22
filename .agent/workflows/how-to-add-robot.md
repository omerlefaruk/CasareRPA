---
description: How to add and connect new robots (Local or Client)
---

# How to Add and Connect a New Robot

CasareRPA uses a "pull-based" architecture where robots connect to the central database to claim jobs. Robots auto-register themselves when they successfully connect.

## 1. Local Computer (Development)

If you just want to run robots on your own machine where the Orchestrator is running:

1. **Open a new terminal** (Command Prompt or PowerShell).
2. **Activate the environment**:
   ```powershell
   # Windows
   .venv\Scripts\activate
   ```
3. **Start the Robot Agent**:
   ```powershell
   python -m casare_rpa.robot.cli start
   ```
   *The robot will auto-detect the local database configuration from your project environment.*

4. **Verify**: Open the Fleet Dashboard in Canvas. You should see a new robot with status `ONLINE`.

## 2. client's Computer (Remote / LAN)

To connect a computer on the same network (LAN) or a remote client:

### A. Prerequisites
The client computer needs:
1. **Python 3.12+** installed.
2. **CasareRPA source code** (or installed package).
3. **Network access** to your PostgreSQL database (Port 5432).

### B. Configuration
Create a `.env` file on the client's computer (e.g., in `C:\Users\Client\.casare_rpa\.env`) with the connection details to YOUR central database:

```ini
# Database Connection (Point to YOUR Orchestrator IP)
DB_HOST=192.168.1.50   <-- REPLACE with your computer's IP
DB_PORT=5432
DB_NAME=casare_rpa
DB_USER=casare_user
DB_PASSWORD=your_secure_password
```

### C. Start the Robot
Run the following command on the client's computer:

```powershell
# 1. Install dependencies (first time only)
pip install -e .
playwright install chromium

# 2. Start the robot
python -m casare_rpa.robot.cli start --name "Client-PC-01" --env production
```

### D. Verification
Once the command is running on the client computer:
1. Go back to your **Canvas > Fleet Dashboard**.
2. Refresh the list.
3. You will see "Client-PC-01" appear as `ONLINE`.

## Troubleshooting
- **Connection Refused**: Ensure your computer's Firewall allows inbound traffic on Port 5432 (PostgreSQL).
- **Postgres Config**: Ensure your `postgresql.conf` listens on `*` (not just localhost) and `pg_hba.conf` allows connections from the client's IP.
