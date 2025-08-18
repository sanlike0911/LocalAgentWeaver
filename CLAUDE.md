# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LocalAgentWeaver (ローカル・エージェント・ウィーバー) is a local AI chat application that provides knowledge base-enhanced conversations using RAG (Retrieval-Augmented Generation). The application runs entirely locally for privacy and security, using Ollama for LLM inference and ChromaDB for vector storage.

## Technology Stack

- **Framework**: Chainlit for UI and backend integration
- **LLM Orchestration**: LangChain for RAG pipeline and LLM management
- **Local LLM**: Ollama (supports models like Llama 3)
- **Vector Database**: ChromaDB for document embeddings
- **Database**: SQLite for project and metadata management
- **Language**: Python 3.10+

## Development Commands

The following commands are used for development and running the application:

```bash
# Setup development environment (creates .venv and installs dependencies automatically)
python setup_dev.py

# Activate virtual environment when needed (Windows)
.venv\Scripts\activate

# Activate virtual environment when needed (Unix/Linux/macOS)
source .venv/bin/activate

# Start Ollama service (required)
ollama serve

# Pull Llama 3 model (first time only)
ollama pull llama3

# Run the application
chainlit run main.py
# OR use the convenience script
python run.py

# Code quality checks
black src/ tests/ --check    # Code formatting
flake8 src/ tests/           # Linting  
mypy src/                    # Type checking
pytest                       # Run tests
```

## Architecture

The application follows a modular architecture:

```
Backend (main.py)
├── Chainlit Server (UI and WebSocket handling)
├── Project Manager (core/project_manager.py) - SQLite CRUD operations
└── RAG Engine (core/rag_engine.py) - LangChain RAG implementation
```

### Key Components (IMPLEMENTED):
- **Project Management**: Each conversation context (chat history + knowledge base) is organized by project
- **Knowledge Base**: Users upload documents (PDF, TXT, MD) that are embedded and stored per-project
- **RAG Chat**: AI responses are generated using relevant knowledge base content with source citations
- **Local Processing**: All AI inference happens locally via Ollama
- **File Upload**: Drag & drop interface for document upload
- **UI Actions**: Project switching and knowledge management buttons

### Current Status: Phase 1 (MVP) COMPLETED ✅
- ✅ Chainlit UI with project management
- ✅ File upload and document processing
- ✅ RAG implementation with Ollama + ChromaDB
- ✅ SQLite database for project persistence
- ✅ Interactive UI with action buttons
- ✅ Error handling and logging

## Future Development Phases

### Phase 2: Multi-Agent system
- Multiple AI agents with different roles per project
- Agent team collaboration features
- Advanced UI for agent management

### Phase 3: Tool integration
- Web search capabilities
- File I/O operations
- Code execution in sandboxed environments

### Phase 4: Hybrid cloud/local deployment
- Optional cloud LLM integration (OpenAI, Anthropic)
- Agent template sharing system

## File Structure Conventions

The project follows a simple flat structure:
- `main.py` - Main application entry point
- `core/` - Core business logic modules (project_manager, rag_engine)
- `ui/` - UI handlers and components  
- `config/` - Configuration and settings
- `tests/` - Test files
- `data/` - Runtime data directory (gitignored)
- `logs/` - Application logs (gitignored)
- `vector_db/` - ChromaDB storage (gitignored)

## Environment Setup

The project uses standard Python tooling:
- Virtual environment management (venv)
- Ollama installation required for local LLM inference
- Git hooks enforce code quality (black, flake8, mypy, pytest)

## Special Considerations

- **Privacy-focused**: Designed to run entirely offline after initial setup
- **Japanese context**: Documentation is in Japanese, targeting Japanese developers
- **Security**: Sandboxed execution planned for code tools in later phases
- **Modular design**: Each phase builds incrementally on the previous foundation