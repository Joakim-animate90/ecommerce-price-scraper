FROM postgres:15-alpine

# Install additional extensions if needed
RUN apk add --no-cache postgresql-contrib

# Copy initialization scripts
COPY init.sql /docker-entrypoint-initdb.d/

# Set environment variables (will be overridden by docker-compose)
ENV POSTGRES_DB=ecommerce_prices
ENV POSTGRES_USER=scraper_user
ENV POSTGRES_PASSWORD=change_me_in_production

# Expose PostgreSQL port
EXPOSE 5432
