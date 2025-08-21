"""
Model configuration management for LocalAgentWeaver
"""
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel
from app.features.chat.schemas import LLMProvider


class ModelInfo(BaseModel):
    """Model information from configuration"""
    name: str
    display_name: str
    description: str
    category: str
    tags: List[str]
    recommended: bool
    size_estimate: str


class ModelCategory(BaseModel):
    """Model category information"""
    name: str
    description: str


class ProviderConfig(BaseModel):
    """Provider-specific model configuration"""
    popular_models: List[ModelInfo]
    categories: Dict[str, ModelCategory]


class ModelPresets(BaseModel):
    """Complete model presets configuration"""
    ollama: ProviderConfig
    lm_studio: ProviderConfig
    metadata: Dict[str, Any]


class ModelConfigManager:
    """Manager for model configuration loading and caching"""
    
    def __init__(self):
        self._config: Optional[ModelPresets] = None
        self._config_path = Path(__file__).parent.parent.parent / "config" / "model_presets.json"
    
    def _load_config(self) -> ModelPresets:
        """Load configuration from JSON file"""
        try:
            if not self._config_path.exists():
                raise FileNotFoundError(f"Model config file not found: {self._config_path}")
            
            with open(self._config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return ModelPresets(**config_data)
        except Exception as e:
            # Fallback to default configuration
            return self._get_default_config()
    
    def _get_default_config(self) -> ModelPresets:
        """Return default configuration as fallback"""
        return ModelPresets(
            ollama=ProviderConfig(
                popular_models=[
                    ModelInfo(
                        name="llama3.2:1b",
                        display_name="Llama 3.2 1B",
                        description="Meta の軽量 Llama 3.2 モデル",
                        category="general",
                        tags=["lightweight", "fast"],
                        recommended=True,
                        size_estimate="1.3GB"
                    )
                ],
                categories={
                    "general": ModelCategory(
                        name="汎用モデル",
                        description="幅広い用途に使用できる汎用的なモデル"
                    )
                }
            ),
            lm_studio=ProviderConfig(
                popular_models=[
                    ModelInfo(
                        name="llama-3-8b-instruct",
                        display_name="Llama 3 8B Instruct",
                        description="Meta Llama 3 8B Instruction-tuned モデル",
                        category="general",
                        tags=["instruction-tuned", "chat"],
                        recommended=True,
                        size_estimate="4.7GB"
                    )
                ],
                categories={
                    "general": ModelCategory(
                        name="汎用モデル",
                        description="幅広い用途に使用できる汎用的なモデル"
                    )
                }
            ),
            metadata={
                "version": "1.0.0",
                "description": "Default model configuration"
            }
        )
    
    def get_config(self, force_reload: bool = False) -> ModelPresets:
        """Get model configuration with caching"""
        if self._config is None or force_reload:
            self._config = self._load_config()
        return self._config
    
    def get_popular_models(self, provider: LLMProvider) -> List[ModelInfo]:
        """Get popular models for a specific provider"""
        config = self.get_config()
        provider_key = provider.value.replace('_', '_')  # Handle 'lm_studio'
        
        if provider == LLMProvider.OLLAMA:
            return config.ollama.popular_models
        elif provider == LLMProvider.LM_STUDIO:
            return config.lm_studio.popular_models
        else:
            return []
    
    def get_categories(self, provider: LLMProvider) -> Dict[str, ModelCategory]:
        """Get categories for a specific provider"""
        config = self.get_config()
        
        if provider == LLMProvider.OLLAMA:
            return config.ollama.categories
        elif provider == LLMProvider.LM_STUDIO:
            return config.lm_studio.categories
        else:
            return {}
    
    def get_recommended_models(self, provider: LLMProvider) -> List[ModelInfo]:
        """Get recommended models for a specific provider"""
        models = self.get_popular_models(provider)
        return [model for model in models if model.recommended]
    
    def get_models_by_category(self, provider: LLMProvider, category: str) -> List[ModelInfo]:
        """Get models filtered by category"""
        models = self.get_popular_models(provider)
        return [model for model in models if model.category == category]
    
    def reload_config(self) -> bool:
        """Reload configuration from file"""
        try:
            self._config = self._load_config()
            return True
        except Exception:
            return False


# Global instance
model_config_manager = ModelConfigManager()