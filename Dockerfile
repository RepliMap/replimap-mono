# RepliMap Docker Image
# Build: docker build -t replimap/replimap .
# Run:   docker run -v ~/.aws:/root/.aws replimap/replimap scan --profile prod

FROM python:3.11-slim

LABEL maintainer="RepliMap Team <team@replimap.dev>"
LABEL description="AWS Infrastructure Staging Cloner"
LABEL org.opencontainers.image.source="https://github.com/replimap/replimap"

# Install replimap
RUN pip install --no-cache-dir replimap

# Create non-root user for security (optional, can run as root for AWS creds)
# RUN useradd -m -s /bin/bash replimap
# USER replimap

# Set working directory
WORKDIR /workspace

# Default command shows help
ENTRYPOINT ["replimap"]
CMD ["--help"]
