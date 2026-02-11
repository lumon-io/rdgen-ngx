FROM python:3.13-alpine

# Install system dependencies
RUN apk add --no-cache curl

# Create non-root user
RUN adduser -D user

WORKDIR /opt/rdgen

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=user:user . .

# Create directories for data
RUN mkdir -p exe db temp_zips png \
    && chown -R user:user /opt/rdgen

USER user

# Run migrations (will also run at startup via entrypoint)
RUN python manage.py migrate

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Entrypoint runs migrations then starts gunicorn
CMD python manage.py migrate --noinput && \
    /home/user/.local/bin/gunicorn -c gunicorn.conf.py rdgen.wsgi:application
