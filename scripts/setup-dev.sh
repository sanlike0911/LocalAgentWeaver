#!/bin/bash

set -e

echo "🚀 LocalAgentWeaver Development Environment Setup"
echo "==============================================="

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check port availability
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        echo "⚠️  Port $port is already in use. Please stop the service using this port."
        return 1
    fi
    return 0
}

echo "🔍 Checking port availability..."
ports=(5432 6379 8000 3000 11434 1234)
for port in "${ports[@]}"; do
    if ! check_port $port && [[ $port == 5432 || $port == 6379 || $port == 8000 || $port == 3000 ]]; then
        echo "❌ Required port $port is in use. Please stop the conflicting service."
        exit 1
    fi
done

# LLM Environment Selection
echo ""
echo "🤖 Which LLM execution environment would you like to use?"
echo "1) Ollama (Docker auto-setup)"
echo "2) LM Studio (manual app startup required)"
echo "3) Skip (manual configuration later)"
echo ""
read -p "Enter your choice [1-3]: " llm_choice

case $llm_choice in
    1)
        echo "✅ Selected: Ollama (Docker auto-setup)"
        llm_env="ollama"
        llm_url="http://localhost:11434"
        use_ollama_profile=true
        ;;
    2)
        echo "✅ Selected: LM Studio (manual startup required)"
        llm_env="lmstudio"
        llm_url="http://localhost:1234"
        use_ollama_profile=false
        ;;
    3)
        echo "✅ Selected: Skip (manual configuration)"
        llm_env="skip"
        llm_url="http://localhost:11434"
        use_ollama_profile=false
        ;;
    *)
        echo "❌ Invalid choice. Defaulting to skip."
        llm_env="skip"
        llm_url="http://localhost:11434"
        use_ollama_profile=false
        ;;
esac

# Check NVIDIA Container Toolkit for Ollama
if [ "$llm_env" = "ollama" ]; then
    if ! docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu20.04 nvidia-smi > /dev/null 2>&1; then
        echo "⚠️  NVIDIA Container Toolkit not detected. Ollama will run on CPU only."
        echo "   For GPU acceleration, install NVIDIA Container Toolkit."
    else
        echo "✅ NVIDIA Container Toolkit detected. GPU support available."
    fi
fi

# Create/update .env file
if [ ! -f .env.example ]; then
    echo "❌ .env.example not found. Creating one..."
    exit 1
fi

echo "📝 Generating .env file..."
cp .env.example .env

# Generate random JWT secret
jwt_secret=$(openssl rand -hex 32)
sed -i "s/your-super-secret-jwt-key-change-in-production/$jwt_secret/" .env

# Set LLM URL based on selection
sed -i "s|OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=$llm_url|" .env
if [ "$llm_env" = "lmstudio" ]; then
    sed -i "s|LM_STUDIO_BASE_URL=.*|LM_STUDIO_BASE_URL=$llm_url|" .env
fi

echo "✅ .env file configured with random secrets and LLM settings."

# Start Docker services
echo ""
echo "🐳 Starting Docker environment..."
docker compose down --remove-orphans

if [ "$use_ollama_profile" = true ]; then
    echo "🚀 Starting services with Ollama profile..."
    docker compose --profile ollama up --build -d
else
    echo "🚀 Starting basic services..."
    docker compose up --build -d
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check database connection
echo "🔍 Testing database connection..."
if docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL connection confirmed"
else
    echo "❌ PostgreSQL connection failed"
fi

# Check Redis connection
echo "🔍 Testing Redis connection..."
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis connection confirmed"
else
    echo "❌ Redis connection failed"
fi

# Run database migrations if backend is running
if docker compose ps backend | grep -q "Up"; then
    echo "🔄 Running database migrations..."
    docker compose exec -T backend python -c "
from app.core.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
" 2>/dev/null || echo "⚠️  Database migration skipped (backend not ready)"
fi

# LLM Connection Test
echo ""
echo "🤖 Testing LLM connection..."
test_llm_connection() {
    local url=$1
    local name=$2
    
    if curl -s --connect-timeout 5 "$url/api/tags" > /dev/null 2>&1; then
        models=$(curl -s "$url/api/tags" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    models = [model['name'] for model in data.get('models', [])]
    print(', '.join(models[:3]) + ('...' if len(models) > 3 else ''))
except:
    print('Unable to parse models')
")
        echo "  - $name ($url): ✅ Connection successful"
        echo "    Available models: $models"
        return 0
    else
        echo "  - $name ($url): ❌ Connection failed"
        return 1
    fi
}

case $llm_env in
    "ollama")
        if test_llm_connection "http://localhost:11434" "Ollama"; then
            echo "🎉 Ollama connection successful!"
            
            # Check if llama3 model is available
            echo "🔍 Checking for llama3 model..."
            model_exists=$(curl -s "http://localhost:11434/api/tags" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    models = [model['name'] for model in data.get('models', [])]
    print('true' if any('llama3' in model for model in models) else 'false')
except:
    print('false')
")
            
            if [ "$model_exists" = "true" ]; then
                echo "✅ llama3 model is already available"
            else
                echo "📥 llama3 model not found. Downloading..."
                echo "   This may take several minutes depending on your internet connection."
                docker compose exec -T ollama ollama pull llama3
                if [ $? -eq 0 ]; then
                    echo "✅ llama3 model downloaded successfully!"
                else
                    echo "❌ Failed to download llama3 model. You can download it later with:"
                    echo "   docker compose exec ollama ollama pull llama3"
                fi
            fi
        else
            echo "⚠️  Ollama connection failed. Check logs: docker compose logs ollama"
        fi
        ;;
    "lmstudio")
        echo "📱 Testing LM Studio connection..."
        if test_llm_connection "http://localhost:1234" "LM Studio"; then
            echo "🎉 LM Studio connection successful!"
        else
            echo "⚠️  LM Studio connection failed. Please ensure:"
            echo "   1. LM Studio application is running"
            echo "   2. Local server is started on port 1234"
            echo "   3. A model is loaded and ready"
        fi
        ;;
    "skip")
        echo "⏭️  LLM connection test skipped."
        ;;
esac

echo ""
echo "🎉 Development environment setup completed!"
echo ""
echo "🌐 Application URLs:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
if [ "$use_ollama_profile" = true ]; then
    echo "   - Ollama API: http://localhost:11434"
fi
echo ""
echo "📋 Next steps:"
echo "1. The services should now be running"
echo "2. Check service status: docker compose ps"
echo "3. View logs: docker compose logs [service-name]"
echo "4. Stop services: docker compose down"
echo ""
echo "🛠️  Happy coding with LocalAgentWeaver!"