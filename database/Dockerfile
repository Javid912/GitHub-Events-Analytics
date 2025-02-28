FROM postgres:13-alpine

# Copy initialization scripts
COPY schema.sql /docker-entrypoint-initdb.d/

# Set environment variables
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=github_events

# Expose PostgreSQL port
EXPOSE 5432 