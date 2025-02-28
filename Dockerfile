FROM postgres

# Set environment variables
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=contrasenya
ENV POSTGRES_DB=Database


# Expose PostgreSQL port
EXPOSE 5432

# Start the PostgreSQL service
CMD ["postgres"]

