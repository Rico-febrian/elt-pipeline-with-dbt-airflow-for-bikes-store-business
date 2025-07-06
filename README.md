# 🏁 Getting Started: Build an End-to-End ELT Pipeline with Airflow and dbt

**Welcome to my Learning Logs!** 

This project is part of my hands-on learning journey as I transition into Data Engineering. It demonstrates how to build an ELT pipeline using **Apache Airflow**, **DBT**, **PostgreSQL**, and **MinIO**.

---

## Project Overview

This project demonstrates how to:

- **Extract data** from a database and API sources.

- **Load this data** into MinIO (object storage) for a data lake, then into a staging schema in a warehouse database.

- **Transform data** into a final schema using **DBT (Data Build Tool)**.

- **Orchestrate the entire process** with **Apache Airflow** (using the Celery Executor).

- Implement Airflow features like **DBT DAG integration**, variable/connection management, and downstream DAG triggering.

- Set up Airflow **remote logging** and a **monitoring stack** using Prometheus and Grafana.

- Configure **Slack alerts** via webhooks for alerting.
    
---

## How the Pipeline Works

![elt-design]()

- **Extract Task**: Pulls raw data from the source database or API and saves it as CSV files in MinIO.

- **Load Task**: Reads the CSVs from MinIO and loads them into the staging schema of the data warehouse.

- **Transform Task**: Runs DBT to transform the staging data into clean, final tables.

All of this is managed by an Airflow DAG, which:

- Runs the tasks in the correct order

- Sends task logs to MinIO

- Sends metrics to Prometheus and Grafana for monitoring

- Sends Slack alerts if any task fails

---

## ⚙️ Requirements

Before getting started, make sure your machine meets the following:

- Memory:
  Minimum 8GB RAM (Recommended: 16GB+, especially for Windows. On Linux, 8GB should be sufficient.)

- Docker (with WSL2 enabled if you're on Windows)

- Python 3.7+ (for generating Fernet key)

- Database Client (DBeaver or any PostgreSQL-compatible SQL client)

---

## 📁 Project Structure

```
elt-airflow-project/
├── dags/
│   └── bikes_store_staging/         # Main DAG script
|   |   └── tasks/                   # Main task scripts
|   |       └── components           # Core task scripts (extract, load, transform)
│   └── bikes_store_warehouse/       # Main DAG script
│   |   └── flights_dbt/             # Main DBT DAG
│   └── helper/                      # Helper functions (callbacks, utils, etc.)
├── dataset/
│   ├── source/                      # Source database init SQL
│   └── warehouse/                   # Warehouse schema init SQL (staging and final schema)
├── monitoring-logging/              # Setup to run monitoring stack
├── Dockerfile                       # Custom Airflow image
├── docker-compose.yml               # Docker Compose config
├── dbt-requirements.txt             # DBT packages for Airflow
├── requirements.txt                 # Python packages for Airflow
├── fernet.py                        # Python script to generate fernet key
└── README.md                        # This guide
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone git@github.com:Rico-febrian/elt-pipeline-with-dbt-airflow-for-bikes-store-business.git
cd elt-pipeline-with-dbt-airflow-for-bikes-store-business
```

### 2. Generate Fernet Key

This key encrypts credentials in Airflow connections.

```bash
pip install cryptography==45.0.2
python3 fernet.py
```

**Copy the output key** to the `.env` file.

### 3. Create `.env` File for Main Service (Run Airflow, MinIO and PostgreSQL)

Use the following template and update with your actual configuration:

```ini
# --- Airflow Core Configuration ---
AIRFLOW_UID=50000

# Fernet key for encrypting Airflow connections (generated using fernet.py script)
AIRFLOW_FERNET_KEY=YOUR_GENERATED_FERNET_KEY_HERE

# Secret key for Airflow Webserver session management (generate a strong random string)
AIRFLOW_WEBSERVER_SECRET_KEY=YOUR_AIRFLOW_WEBSERVER_SECRET_KEY_HERE

# Celery Executor backend and broker URLs (usually don't need to change unless you modify docker-compose.yml)
AIRFLOW_CELERY_RESULT_BACKEND=db+postgresql://airflow:airflow@airflow-metadata:5433/airflow
AIRFLOW_CELERY_BROKER_URL=redis://:@redis:6379/0

# Airflow metadata database connection URI (eg: postgresql+psycopg2://airflow:airflow@airflow_metadata:5433/airflow)
AIRFLOW_DB_URI=postgresql+psycopg2://<AIRFLOW_DB_USER>:<AIRFLOW_DB_PASSWORD>@<AIRFLOW_METADATA_CONTAINER_NAME>:<AIRFLOW_DB_PORT>/<AIRFLOW_DB_NAME>

# --- Airflow Remote Logging Configuration
AIRFLOW_LOGGING_REMOTE_BASE_LOG_FOLDER=s3://airflow-logs/ # MiNIO/S3 bucket name to store the DAGs log
AIRFLOW_LOGGING_REMOTE_LOG_CONN_ID=s3-conn                # MinIO/S3 coneection name in Airflow  

AIRFLOW_METRICS_STATSD_HOST=statsd-exporter               # Statsd-exporter service name in docker compose 
AIRFLOW_METRICS_STATSD_PORT=8125                          # Statsd-exporter udp port in docker compose 

# --- Airflow DB User & Password (used by Airflow itself) ---
AIRFLOW_DB_USER=airflow
AIRFLOW_DB_PASSWORD=airflow
AIRFLOW_DB_NAME=airflow
AIRFLOW_DB_PORT=5433

# --- Source Database Configuration ---
BIKES_DB_USER=postgres
BIKES_DB_PASSWORD=postgres
BIKES_DB_NAME=bikes-store
BIKES_DB_PORT=5434

# --- Data Warehouse (DWH) Configuration (for staging and final schemas) ---
DWH_DB_USER=postgres
DWH_DB_PASSWORD=postgres
DWH_DB_NAME=warehouse
DWH_DB_PORT=5435

# --- MinIO Configuration ---
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123
MINIO_API_PORT=9000
MINIO_CONS_PORT=9001
LOGS_BUCKET=airflow-logs
EXTRACTED_BUCKET=bikes-store
```
### 4. Create `.env` File for Monitoring Service (Run Stasd-exporter, Grafana and Prometheus)
Change directory to `monitoring-logging/` then create `.env` with these following template and update with your actual configuration:

```ini
--- Grafana configuration ---
GRAFANA_USERNAME=grafana
GRAFANA_PASSWORD=grafana
```

### 5. Setup Airflow Variable and Connections
Airflow needs some variables and connections to run the pipeline properly. You can:

- Set them manually through the Airflow UI

- Or use the preconfigured template:
  - [Airflow variable and connections config]()

For the Slack notifier you can following these steps:
  - **Log in** to your existing Slack account or **create** a new one if you don’t have it yet.
  - **Create a workspace** (if you don’t already have one) and create a dedicated Slack channel where you want to receive alerts.
  - **Create a Slack App**:

    - Go to https://api.slack.com/apps
    - Click **Create New App**
    - Choose **From scratch**
    - Enter your app name and select the workspace you just created or want to use
    - Click **Create App**

  - **Set up an Incoming Webhook** for your app:

    - In the app settings, find and click on **Incoming Webhooks**
    - **Enable Incoming Webhooks** if it’s not already enabled
    - Click **Add New Webhook to Workspace**
    - Select the Slack channel you want alerts to go to and authorize
  
  - **Copy the generated Webhook URL**

    <img src="https://github.com/Rico-febrian/flight-bookings-elt-pipeline-with-airflow/blob/main/pict/slack-webhook.png" alt="webhook-url" width="600"/>


### 5. Build and Start Services

After setting up the `.env` files, Airflow connections, and variables, you can start all the services.

You can either:

- Run each `docker-compose` file manually, or
- Just use the provided `setup.sh` script to spin up everything at once.

Make the script executable:
```bash
chmod 700 setup.sh
```
then, run the script
```bash
./setup.sh
```
What this script does:

- **Cleans up** any previous Docker volumes

- Starts the **main services** (Airflow, DBs, MinIO, Redis)

- Starts the **monitoring stack** (Prometheus + Grafana)

- Automatically imports all required **Airflow variables and connections**
  
You can re-run this script anytime to reset and restart everything from scratch.

### 5. Open Airflow UI

Access the UI at: [http://localhost:8080](http://localhost:8080) (or your defined port).

Log in with the default credentials:

- Username: `airflow`
- Password: `airflow`
(These are defined in the `airflow-init` service within your `docker-compose.yml`).

---
---

## ▶️ Run the DAG

- Open the Airflow UI (http://localhost:8080)

- Locate these two DAGs and run the DAG:

  - `bikes_store_staging`
  - `bikes_store_warehouse`

> [!Note]
> You don’t need to manually run `bikes_store_warehouse` DAG. It will be triggered automatically after the staging pipeline completes.

---

## DAG Behavior (What to Expect)

This pipeline runs in **two DAGs**, managed by Airflow:

- `bikes_store_staging` DAG:

  - Extract tasks **run in parallel**
  - Load tasks **run sequentially** after extract task finished
  - After load task is completed, it **automatically triggers** the next DAG: `bikes_store_warehouse`

    <img src="" alt="dag-result" width="800"/>

- In `bikes_store_warehouse` DAG:
  This DAG handles the **transformation process using DBT**. It includes **three main tasks**:

  - `check_is_warehouse_init`
     Decides which transformation path to run, based on the Airflow variable `BIKES_STORE_WAREHOUSE_INIT`

    - If it's set to **True**, the pipeline runs `init_warehouse` task
    - If it's **False**, it runs `warehouse` task

  - `init_warehouse`
    Runs the full DBT transformation, including:

    - Seeding the `dim_date` table
    - Running all models
    - Running DBT tests to validate results
      
    <img src="" alt="init-warehouse-result" width="800"/>

  - `init_warehouse`
    Runs only the regular DBT models (no seed) and DBT tests

    <img src="" alt="init-warehouse-result" width="800"/>

---

## Verify the Results

Since incremental mode and catchup are disabled (set to `False`), the pipeline will runs the **full load** process. So, you can just verify the result by open the database.

### Extracted Data in MinIO Bucket

- Log in to the MinIO console (eg. localhost:9000) using the username and password defined in your `.env` file.
- Navigate to the selected bucket.
- You should see the extracted data files in CSV format.

  <img src="" alt="minio-result" width="600"/>

### Staging and Transformed data in Data Warehouse

To verify the data in your data warehouse:

- Open your database client (e.g., DBeaver).
- Connect to your warehouse database.
- Look for these schemas:

  - bikes_store_staging → contains raw, loaded data
  - warehouse → contains clean, transformed tables from DBT

You can explore the tables, run simple queries, and check the row counts to confirm everything worked as expected.
        
---

## Feedback & Articles

**Thank you for exploring this project!** If you have any feedback, feel free to share, I'm always open to suggestions.

Additionally, I write about my learning journey on Medium. You can check out my articles [here](https://medium.com/@ricofebrian731). Let’s also connect on [LinkedIn](https://www.linkedin.com/in/ricofebrian).

---

Happy learning! 🚀
