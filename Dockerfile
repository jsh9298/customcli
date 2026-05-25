# Unified Hybrid Backend Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# [Critical Fix] Core dependencies를 먼저 최신 버전으로 강제 설치
# 이는 Antigravity SDK의 Protobuf Edition UNKNOWN 에러를 방지하기 위함입니다.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "protobuf>=5.29.1" "grpcio>=1.70.0"

# Copy project configuration
COPY pyproject.toml README.md GEMINI.md MAINTENANCE.md agent_config.yaml masking_config.yaml agents.md ./

# [Critical Fix] COPY source code BEFORE pip install
COPY src/ ./src/

# Install dependencies and package (Both Antigravity and GenAI)
RUN pip install --no-cache-dir .

# [Standard] 마운트 포인트 선언
VOLUME ["/app/workspace", "/app/sessions", "/app/debug_payload.log"]

# Set entry point to the installed script
ENTRYPOINT ["custom-cli"]
