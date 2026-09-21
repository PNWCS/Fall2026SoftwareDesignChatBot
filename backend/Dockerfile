# Start from a small official Python image. The image contains Python and Linux
# libraries, but not our application dependencies yet.
FROM python:3.12-slim

# Create a non-root account for the application. Running as a non-root user means
# a bug in the web app cannot automatically grant the process administrator access
# inside the container.
RUN groupadd --system app && useradd --system --gid app --create-home app

WORKDIR /app

# Install uv, the dependency manager used by this repository, from its official
# image. Copying only the dependency files first lets Docker reuse this layer when
# application source files change but dependencies do not.
COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the backend package after dependency installation. The source is currently
# only a scaffold; later tasks add the FastAPI application and its modules.
COPY src ./src

# Install this project into the environment without downloading dependencies again.
RUN uv sync --frozen --no-dev

# The app user owns the files it needs to read, and the process runs as that user.
RUN chown -R app:app /app
USER app

# This documents the port used by Uvicorn inside the container. Compose maps it to
# port 8000 on the host.
EXPOSE 8000

# T019 will add src/main.py. Keeping the command here makes the image ready for
# the FastAPI service once that task is implemented.
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
