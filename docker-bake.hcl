group "default" {
  targets = [
    "auth",
    "marketplace_backend",
    "events_collector",
    "events_saver",
    "training_features_etl",
    "recommendations",
    "marketplace_frontend",
  ]
}

target "auth" {
  context = "."
  dockerfile = "dockerfiles/Dockerfile.python-service"
  args = {
    REQUIREMENTS_FILE = "dockerfiles/requirements/auth.txt"
    SERVICE_SRC_DIR   = "auth"
    SERVICE_DST_DIR   = "auth"
    PYTHONPATH_VALUE  = "/app:/app/shared-lib"
    APP_WORKDIR       = "/app"
    APP_PORT          = "8001"
    APP_CMD           = "uvicorn auth.cmd:app --host 0.0.0.0 --port 8001"
  }
  tags = ["fastapi-shop/auth:local"]
}

target "marketplace_backend" {
  context = "."
  dockerfile = "dockerfiles/Dockerfile.python-service"
  args = {
    REQUIREMENTS_FILE = "dockerfiles/requirements/marketplace-backend.txt"
    SERVICE_SRC_DIR   = "marketplace-backend"
    SERVICE_DST_DIR   = "marketplace-backend"
    PYTHONPATH_VALUE  = "/app/marketplace-backend:/app/shared-lib"
    APP_WORKDIR       = "/app/marketplace-backend"
    APP_PORT          = "8000"
    APP_CMD           = "uvicorn application.cmd:app --host 0.0.0.0 --port 8000"
  }
  tags = ["fastapi-shop/marketplace-backend:local"]
}

target "events_collector" {
  context = "."
  dockerfile = "dockerfiles/Dockerfile.python-service"
  args = {
    REQUIREMENTS_FILE = "dockerfiles/requirements/events-collector.txt"
    SERVICE_SRC_DIR   = "events-collector"
    SERVICE_DST_DIR   = "events_collector"
    PYTHONPATH_VALUE  = "/app:/app/shared-lib"
    APP_WORKDIR       = "/app"
    APP_PORT          = "8010"
    APP_CMD           = "uvicorn events_collector.cmd:app --host 0.0.0.0 --port 8010"
  }
  tags = ["fastapi-shop/events-collector:local"]
}

target "events_saver" {
  context = "."
  dockerfile = "dockerfiles/Dockerfile.python-service"
  args = {
    REQUIREMENTS_FILE = "dockerfiles/requirements/events-saver.txt"
    SERVICE_SRC_DIR   = "events-saver"
    SERVICE_DST_DIR   = "events-saver"
    PYTHONPATH_VALUE  = "/app/events-saver:/app/shared-lib"
    APP_WORKDIR       = "/app"
    APP_CMD           = "python -m event_saver.main"
  }
  tags = ["fastapi-shop/events-saver:local"]
}

target "training_features_etl" {
  context = "."
  dockerfile = "dockerfiles/Dockerfile.python-service"
  args = {
    REQUIREMENTS_FILE = "dockerfiles/requirements/training-features-etl.txt"
    SERVICE_SRC_DIR   = "training-features-etl"
    SERVICE_DST_DIR   = "training-features-etl"
    PYTHONPATH_VALUE  = "/app/training-features-etl:/app/shared-lib"
    APP_WORKDIR       = "/app"
    APP_CMD           = "python -m training_features_etl.main"
  }
  tags = ["fastapi-shop/training-features-etl:local"]
}

target "recommendations" {
  context = "."
  dockerfile = "dockerfiles/Dockerfile.python-service"
  args = {
    REQUIREMENTS_FILE = "dockerfiles/requirements/recommendations.txt"
    SERVICE_SRC_DIR   = "recommendations"
    SERVICE_DST_DIR   = "recommendations"
    PYTHONPATH_VALUE  = "/app"
    APP_WORKDIR       = "/app"
    APP_PORT          = "8020"
    APP_CMD           = "uvicorn recommendations.main:app --host 0.0.0.0 --port 8020"
  }
  tags = ["fastapi-shop/recommendations:local"]
}

target "marketplace_frontend" {
  context = "."
  dockerfile = "dockerfiles/Dockerfile.marketplace-frontend"
  tags = ["fastapi-shop/marketplace-frontend:local"]
}
