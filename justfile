
start-airflow:
    docker compose up -d
    @echo "Airflow started successfully."

stop-airflow:
    docker compose down
    @echo "Airflow stopped successfully."

start-sftp:
    docker compose -f docker-compose.sftp.yaml up -d
    @echo "SFTP server started successfully."

stop-sftp:
    docker compose -f docker-compose.sftp.yaml down
    @echo "SFTP server stopped successfully."