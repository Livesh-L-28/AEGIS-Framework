FROM python:3.12-slim

# Avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root system user
RUN groupadd -r aegis && useradd -r -g aegis -u 1000 -m -s /bin/bash aegis

WORKDIR /home/aegis/app

# Install dependencies and framework
COPY pyproject.toml README.md ./
COPY aegis ./aegis
COPY benchmarks ./benchmarks

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .[all]

USER aegis

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD aegis doctor || exit 1

ENTRYPOINT ["aegis"]
CMD ["doctor"]
