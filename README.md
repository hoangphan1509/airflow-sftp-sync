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
