# Create shared Docker Network if it doesn't exist
docker network inspect exw8-networks >/dev/null 2>&1 || docker network create exw8-networks 

# Start Monitoring (Prometheus and Grafana) Services
docker compose -f ./monitoring-logging/setup/docker-compose.yaml down -v
docker compose -f ./monitoring-logging/setup/docker-compose.yaml up --build --detach

# Start Airflow, MinIO and PostgreSQL Service
docker compose down -v
docker compose up --build --detach

sleep 10
# Import connection and variables to Airflow
docker exec -it airflow-webserver airflow connections import /init/connection-variables/connections.yaml
docker exec -it airflow-webserver airflow variables import /init/connection-variables/variables.json 