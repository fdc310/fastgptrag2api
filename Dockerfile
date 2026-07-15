FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies (no project, just deps, using China PyPI mirror)
RUN uv sync --frozen --no-dev --no-install-project --index-url https://mirrors.aliyun.com/pypi/simple/ --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple/

# Copy application code
COPY app/ ./app/
COPY run.py ./

# Default port and workers (overridable via env)
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV APP_WORKERS=4

EXPOSE 8000

CMD ["uv", "run", "python", "run.py"]
