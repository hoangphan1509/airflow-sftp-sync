# SFTP Sync

## Run the project locally

### Prerequisites
- **Docker**: Install Docker Engine (https://docs.docker.com/get-docker/)
- **Docker Compose**: Install Docker Compose V2 (https://docs.docker.com/compose/install/)
- **Podman**: (Alternative to Docker) Install Podman (https://podman.io/getting-started/installation)
- **podman-compose**: (If using Podman) Install podman-compose (https://github.com/containers/podman-compose)
- **just**: Install just (https://just.systems/)

### Start airflow cluster
```bash
just start-airflow
```

### Start sftp server (for local testing)
```bash
just start-sftp
```

## Solution:

### Use rclone to sync file from source to destination sftp
1. Install rclone
2. Config source and target SFTP connection
3. Add cronjob to run rclone sync source:~/ target:~/

### Use airflow DAG to sync file from source to target
1. Start airflow server
2. Config source and target SFTP connection
Go to http://localhost:8080/connections:
- Create new SFTP connection with name source-sftp and target-sftp
- Active the [DAG](http://localhost:8080/dags/sftp_sync) to run the sync process
