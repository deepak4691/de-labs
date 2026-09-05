# de-lab

A small Dockerized data-ingestion lab using PostgreSQL and a Python event producer.

## Architecture

- **PostgreSQL** stores events in the `raw_events` table.
- **Producer** generates one event per second and inserts it into PostgreSQL.
- Inserts are transactional and idempotent through `ON CONFLICT DO NOTHING`.
- Database connection retries use bounded exponential backoff.

## Requirements

- Docker Desktop with the Linux engine running
- Docker Compose

## Start the Lab

From this directory:

```powershell
docker compose up -d --build
```

Check service status:

```powershell
docker compose ps
```

Expected services:

- `lab_postgres`: healthy
- `lab_producer`: running

## View Producer Logs

```powershell
docker logs -f lab_producer
```

Successful output contains messages like:

```text
Inserted event: <event-id>
```

## Connect to PostgreSQL

The Docker PostgreSQL server is published on host port `5433` because another PostgreSQL process uses host port `5432`.

Use these settings in pgAdmin or DBeaver:

```text
Host: 127.0.0.1
Port: 5433
Database: postgres
Username: postgres
Password: postgrespassword
```

The producer uses the internal Docker address `postgres:5432`, so its database connection does not use the host port.

## Connect from the Terminal

Open a PostgreSQL shell inside the container:

```powershell
docker exec -it lab_postgres psql -U postgres -d postgres
```

Useful SQL commands:

```sql
\dt
SELECT COUNT(*) FROM raw_events;
SELECT * FROM raw_events ORDER BY event_time DESC LIMIT 10;
\q
```

Test the published host port directly:

```powershell
docker run --rm -e PGPASSWORD=postgrespassword postgres:15-alpine psql -h host.docker.internal -p 5433 -U postgres -d postgres -c "SELECT current_user, current_database();"
```

## Stop the Lab

Stop containers while preserving database data:

```powershell
docker compose down
```

Stop containers and delete the PostgreSQL data volume:

```powershell
docker compose down -v
```

Deleting the volume removes all stored events. The schema is recreated automatically the next time PostgreSQL starts.

## Project Structure

```text
de-lab/
├── .env
├── docker-compose.yml
├── README.md
├── producer/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
└── scripts/
    └── init.sql
```
