services:
  timescaledb:
    image: timescale/timescaledb:latest-pg14
    container_name: pondmonitor-timescaledb-1
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: pond_user
      POSTGRES_PASSWORD: secretpassword
      POSTGRES_DB: pond_data
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d  # <<< Add this line

volumes:
  db_data:
