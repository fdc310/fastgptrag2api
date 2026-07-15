FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml uv.lock ./

# Configure uv to use Alibaba Cloud PyPI mirror (for faster downloads in China)
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV UV_EXTRA_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/

# Install dependencies (no project, just deps)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY app/ ./app/
COPY run.py ./

# Default port and workers (overridable via env)
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV APP_WORKERS=4

EXPOSE 8000

CMD ["uv", "run", "python", "run.py"]
