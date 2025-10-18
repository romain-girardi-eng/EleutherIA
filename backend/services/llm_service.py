#!/usr/bin/env python3
"""
Unified LLM Service - Supports both local Ollama and cloud Gemini models
Provides fallback and model selection capabilities
"""

import logging
import os
import json
from typing import Dict, Any, Optional, List
from enum import Enum
import requests
from dotenv import load_dotenv

import google.generativeai as genai

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """Available LLM providers"""
    OLLAMA = "ollama"
    GEMINI = "gemini"

class LLMService:
    """Unified LLM service supporting multiple providers with fallback"""
    
    def __init__(self, preferred_provider: ModelProvider = ModelProvider.OLLAMA):
        """Initialize LLM service with preferred provider"""
        env_provider = os.getenv("LLM_PREFERRED_PROVIDER")
        if env_provider:
            try:
                preferred_provider = ModelProvider(env_provider.lower())
            except ValueError:
                logger.warning(f"Unrecognized LLM_PREFERRED_PROVIDER '{env_provider}', defaulting to {preferred_provider.value}")

        self.preferred_provider = preferred_provider
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Configure Gemini if API key is available
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            logger.info("✅ Gemini API configured")
        else:
            logger.warning("⚠️ GEMINI_API_KEY not found - Gemini will be unavailable")
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        provider: Optional[ModelProvider] = None
    ) -> Dict[str, Any]:
        """
        Generate response using specified or preferred provider with fallback
        
        Args:
            prompt: User prompt
            system_prompt: System instruction (optional)
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            provider: Specific provider to use (None = use preferred)
        
        Returns:
            Dict with response, provider used, and metadata
        """
        # Determine which provider to use
        target_provider = provider or self.preferred_provider
        
        # Try preferred provider first
        try:
            if target_provider == ModelProvider.OLLAMA:
                return await self._generate_with_ollama(prompt, system_prompt, temperature, max_tokens)
            elif target_provider == ModelProvider.GEMINI:
                return await self._generate_with_gemini(prompt, system_prompt, temperature, max_tokens)
        except Exception as e:
            logger.warning(f"❌ {target_provider.value} failed: {e}")
            
            # Fallback to other provider
            fallback_provider = ModelProvider.GEMINI if target_provider == ModelProvider.OLLAMA else ModelProvider.OLLAMA
            
            try:
                logger.info(f"🔄 Falling back to {fallback_provider.value}")
                if fallback_provider == ModelProvider.OLLAMA:
                    return await self._generate_with_ollama(prompt, system_prompt, temperature, max_tokens)
                else:
                    return await self._generate_with_gemini(prompt, system_prompt, temperature, max_tokens)
            except Exception as fallback_error:
                logger.error(f"❌ Fallback to {fallback_provider.value} also failed: {fallback_error}")
                return {
                    "response": f"Error: Both LLM providers failed. Primary: {e}, Fallback: {fallback_error}",
                    "provider": "error",
                    "error": str(e),
                    "fallback_error": str(fallback_error)
                }
    
    async def _generate_with_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate response using Ollama (Mistral 7B)"""
        logger.debug("🤖 Generating with Ollama (Mistral 7B)")
        
        # Check if Ollama is running
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise Exception("Ollama server not responding")
        except Exception as e:
            raise Exception(f"Ollama server unavailable: {e}")
        
        # Prepare the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        # Ollama API request
        payload = {
            "model": "mistral:7b",
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120  # 2 minutes timeout for local inference
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            result = response.json()
            
            if "response" not in result:
                raise Exception("No response in Ollama result")
            
            logger.info(f"✅ Ollama response: {len(result['response'])} characters")
            
            return {
                "response": result["response"].strip(),
                "provider": "ollama",
                "model": "mistral:7b",
                "tokens_used": result.get("eval_count", 0),
                "generation_time": result.get("total_duration", 0) / 1e9,  # Convert to seconds
                "metadata": {
                    "prompt_eval_duration": result.get("prompt_eval_duration", 0) / 1e9,
                    "eval_duration": result.get("eval_duration", 0) / 1e9
                }
            }
            
        except requests.exceptions.Timeout:
            raise Exception("Ollama request timeout - model may be too slow")
        except Exception as e:
            raise Exception(f"Ollama generation failed: {e}")
    
    async def _generate_with_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate response using Gemini"""
        logger.debug("🤖 Generating with Gemini")
        
        if not self.gemini_api_key:
            raise Exception("Gemini API key not configured")
        
        try:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            
            if response.text:
                logger.info(f"✅ Gemini response: {len(response.text)} characters")
                return {
                    "response": response.text.strip(),
                    "provider": "gemini",
                    "model": "gemini-2.0-flash-exp",
                    "tokens_used": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
                    "generation_time": 0,  # Gemini doesn't provide timing
                    "metadata": {
                        "finish_reason": response.candidates[0].finish_reason.name if response.candidates else "unknown"
                    }
                }
            else:
                raise Exception("Empty response from Gemini")
                
        except Exception as e:
            raise Exception(f"Gemini generation failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all available providers"""
        health_status = {
            "ollama": {"available": False, "error": None},
            "gemini": {"available": False, "error": None}
        }
        
        # Check Ollama
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                mistral_available = any("mistral" in model.get("name", "") for model in models)
                health_status["ollama"] = {
                    "available": mistral_available,
                    "models": [model["name"] for model in models],
                    "error": None if mistral_available else "Mistral 7B not found"
                }
        except Exception as e:
            health_status["ollama"]["error"] = str(e)
        
        # Check Gemini
        if self.gemini_api_key:
            try:
                # Simple test generation
                model = genai.GenerativeModel("gemini-2.0-flash-exp")
                test_response = model.generate_content("Test", generation_config=genai.GenerationConfig(max_output_tokens=10))
                health_status["gemini"] = {
                    "available": bool(test_response.text),
                    "error": None
                }
            except Exception as e:
                health_status["gemini"]["error"] = str(e)
        else:
            health_status["gemini"]["error"] = "API key not configured"
        
        return health_status
    
    async def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        available = []
        health = await self.health_check()
        
        if health["ollama"]["available"]:
            available.append("ollama")
        if health["gemini"]["available"]:
            available.append("gemini")
        
        return available
