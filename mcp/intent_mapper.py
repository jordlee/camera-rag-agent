#!/usr/bin/env python3
"""
LLM-based intent mapping system for Sony Camera SDK queries.
Uses Phi-3-mini for natural language understanding with semantic similarity fallback.
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import time

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning("Transformers not available, falling back to semantic matching only")

from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class IntentMatch:
    """Represents a matched intent with confidence and reasoning."""
    api_function: str
    confidence: float
    reasoning: str
    category: str
    description: str
    related_functions: List[str] = None
    
    def to_dict(self):
        return asdict(self)

class LLMIntentMapper:
    """LLM-based intent mapping using Phi-3-mini for natural language understanding."""
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize the LLM intent mapper.
        
        Args:
            use_gpu: Whether to use GPU acceleration (if available)
        """
        self.use_gpu = use_gpu and torch.cuda.is_available() if HAS_TRANSFORMERS else False
        self.device = "cuda" if self.use_gpu else "cpu"
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Initialize models
        self._load_llm_model()
        self._load_semantic_model()
        self._build_api_knowledge_base()
        
        logger.info(f"Intent mapper initialized (device: {self.device}, LLM: {HAS_TRANSFORMERS})")
    
    def _load_llm_model(self):
        """Load Phi-3-mini model for natural language understanding."""
        if not HAS_TRANSFORMERS:
            self.llm_model = None
            self.llm_tokenizer = None
            logger.warning("LLM model not available, using semantic fallback only")
            return
        
        try:
            model_name = "microsoft/Phi-3-mini-4k-instruct"
            logger.info(f"Loading LLM model: {model_name}")
            
            self.llm_tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self.llm_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.use_gpu else torch.float32,
                device_map="auto" if self.use_gpu else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            if not self.use_gpu:
                self.llm_model = self.llm_model.to(self.device)
            
            logger.info("LLM model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            self.llm_model = None
            self.llm_tokenizer = None
    
    def _load_semantic_model(self):
        """Load sentence transformer for semantic similarity matching."""
        try:
            # Use a small, fast model for semantic similarity
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Semantic model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load semantic model: {e}")
            self.semantic_model = None
    
    def _build_api_knowledge_base(self) -> Dict[str, Dict]:
        """Build comprehensive knowledge base of Sony Camera SDK API functions."""
        return {
            # Connection Management
            "SCRSDK::Connect": {
                "description": "Establishes connection to Sony camera device",
                "category": "connection",
                "use_cases": [
                    "connect to camera", "establish connection", "pair with camera",
                    "link camera to application", "attach camera device"
                ],
                "parameters": ["CrSdkControlMode", "CrReconnectingSet"],
                "related": ["EnumCameraObjects", "SCRSDK::Disconnect", "SCRSDK::Release"],
                "example_usage": "Connect to camera before performing any operations"
            },
            
            "SCRSDK::Disconnect": {
                "description": "Disconnects from Sony camera device",
                "category": "connection", 
                "use_cases": [
                    "disconnect camera", "close connection", "detach camera",
                    "end session", "stop communication"
                ],
                "related": ["SCRSDK::Connect", "SCRSDK::Release"],
                "example_usage": "Disconnect when finished with camera operations"
            },
            
            "EnumCameraObjects": {
                "description": "Enumerates available Sony camera devices",
                "category": "connection",
                "use_cases": [
                    "list cameras", "find cameras", "discover devices", 
                    "enumerate cameras", "scan for cameras"
                ],
                "related": ["SCRSDK::Connect"],
                "example_usage": "Find available cameras before connecting"
            },
            
            # File Operations
            "SetSaveInfo": {
                "description": "Sets file save location and naming options",
                "category": "file_operations",
                "use_cases": [
                    "save file location", "set save path", "change download folder",
                    "specify save directory", "configure file destination",
                    "set download location", "save images to folder"
                ],
                "parameters": ["save_path", "file_format", "naming_options"],
                "related": ["DownloadContents"],
                "example_usage": "Set where captured images should be saved"
            },
            
            "DownloadContents": {
                "description": "Downloads captured images from camera",
                "category": "file_operations",
                "use_cases": [
                    "download image", "transfer photo", "get captured image",
                    "retrieve file", "save image to computer", "transfer pictures"
                ],
                "related": ["SetSaveInfo"],
                "example_usage": "Download images after capture"
            },
            
            # Camera Settings
            "GetDeviceProperties": {
                "description": "Retrieves current camera settings and status",
                "category": "camera_settings",
                "use_cases": [
                    "get camera settings", "read camera properties", "check camera status",
                    "retrieve device properties", "get current settings", "camera configuration"
                ],
                "related": ["SetDeviceProperty", "GetSelectDeviceProperties"],
                "example_usage": "Read current camera configuration"
            },
            
            "SetDeviceProperty": {
                "description": "Changes camera settings and properties",
                "category": "camera_settings",
                "use_cases": [
                    "set camera property", "change camera setting", "configure device",
                    "adjust camera parameter", "modify settings"
                ],
                "related": ["GetDeviceProperties"],
                "example_usage": "Change camera settings like exposure, ISO, etc."
            },
            
            # Focus Control
            "CrDeviceProperty_ZoomAndFocusPosition_Save": {
                "description": "Saves current zoom and focus position as preset",
                "category": "focus_control",
                "use_cases": [
                    "save focus position", "store focus preset", "remember focus setting",
                    "save zoom position", "create focus memory", "store lens position"
                ],
                "related": ["CrDeviceProperty_Zoom_Operation", "CrDeviceProperty_AF_AreaPosition"],
                "example_usage": "Save current focus position for quick recall"
            },
            
            "CrDeviceProperty_AF_AreaPosition": {
                "description": "Controls autofocus area position",
                "category": "focus_control",
                "use_cases": [
                    "autofocus control", "focus area selection", "AF point control",
                    "focus zone setting"
                ],
                "related": ["CrDeviceProperty_FocusMode"],
                "example_usage": "Set focus area for autofocus operation"
            },
            
            # Zoom Operations
            "CrDeviceProperty_Zoom_Operation": {
                "description": "Controls camera zoom functionality",
                "category": "zoom_control",
                "use_cases": [
                    "zoom control", "optical zoom", "zoom in out", "lens zoom",
                    "magnification control", "zoom operation"
                ],
                "related": ["CrDeviceProperty_ZoomAndFocusPosition_Save"],
                "example_usage": "Control camera zoom level"
            },
            
            # Exposure Settings
            "CrDeviceProperty_ExposureMode": {
                "description": "Sets camera exposure mode",
                "category": "exposure_control",
                "use_cases": [
                    "set exposure mode", "change exposure setting", "manual exposure",
                    "auto exposure", "exposure control"
                ],
                "related": ["CrDeviceProperty_ShutterSpeed", "CrDeviceProperty_FNumber"],
                "example_usage": "Set exposure mode (manual, auto, etc.)"
            },
            
            "CrDeviceProperty_ShutterSpeed": {
                "description": "Controls camera shutter speed",
                "category": "exposure_control",
                "use_cases": ["shutter speed", "exposure time", "shutter control"],
                "related": ["CrDeviceProperty_ExposureMode"],
                "example_usage": "Set shutter speed for exposure control"
            },
            
            "CrDeviceProperty_FNumber": {
                "description": "Controls camera aperture (F-number)",
                "category": "exposure_control", 
                "use_cases": ["aperture setting", "f number", "f stop", "depth of field"],
                "related": ["CrDeviceProperty_ExposureMode"],
                "example_usage": "Set aperture for depth of field control"
            },
            
            "CrDeviceProperty_IsoSensitivity": {
                "description": "Controls camera ISO sensitivity",
                "category": "exposure_control",
                "use_cases": ["iso setting", "sensitivity", "gain", "noise control"],
                "related": ["CrDeviceProperty_ExposureMode"],
                "example_usage": "Set ISO for light sensitivity"
            },
            
            # Error Codes
            "CrError_Connect_TimeOut": {
                "description": "Connection timeout error",
                "category": "error_handling",
                "use_cases": ["connection timeout", "connection failed", "timeout error"],
                "example_usage": "Occurs when camera connection times out"
            },
            
            "CrError_Busy": {
                "description": "Camera busy error", 
                "category": "error_handling",
                "use_cases": ["camera busy", "device busy", "operation in progress"],
                "example_usage": "Camera is currently processing another operation"
            },
            
            "CrWarning_BatteryLow": {
                "description": "Low battery warning",
                "category": "error_handling",
                "use_cases": ["low battery", "battery warning", "power low"],
                "example_usage": "Camera battery is running low"
            }
        }
    
    def _create_llm_prompt(self, query: str) -> str:
        """Create structured prompt for LLM intent extraction."""
        api_list = []
        for api_func, info in self.api_knowledge_base.items():
            use_cases = ", ".join(info["use_cases"][:3])  # First 3 use cases
            api_list.append(f"- {api_func}: {info['description']} (use cases: {use_cases})")
        
        api_functions = "\n".join(api_list)
        
        prompt = f"""<|system|>
You are an expert in Sony Camera Remote SDK. Your task is to map user queries to the most relevant API functions.

Available API Functions:
{api_functions}

Instructions:
1. Analyze the user query for intent and technical requirements
2. Select the most relevant API function(s)
3. Provide confidence score (0.0-1.0)
4. Explain your reasoning
5. Respond in valid JSON format only

<|end|>
<|user|>
User query: "{query}"

Please map this query to the most relevant API function and respond with JSON in this exact format:
{{
  "api_function": "function_name",
  "confidence": 0.85,
  "reasoning": "explanation of why this function matches",
  "category": "category_name"
}}
<|end|>
<|assistant|>"""
        
        return prompt
    
    async def _query_llm_async(self, query: str) -> Optional[IntentMatch]:
        """Query LLM for intent extraction asynchronously."""
        if not self.llm_model or not self.llm_tokenizer:
            return None
        
        try:
            prompt = self._create_llm_prompt(query)
            
            # Run LLM inference in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_llm_inference,
                prompt
            )
            
            return self._parse_llm_response(result)
            
        except Exception as e:
            logger.error(f"LLM query error: {e}")
            return None
    
    def _run_llm_inference(self, prompt: str) -> str:
        """Run LLM inference in thread."""
        try:
            inputs = self.llm_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            inputs = inputs.to(self.device)
            
            with torch.no_grad():
                outputs = self.llm_model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.1,  # Low temperature for consistent results
                    do_sample=True,
                    pad_token_id=self.llm_tokenizer.eos_token_id
                )
            
            response = self.llm_tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            return response.strip()
            
        except Exception as e:
            logger.error(f"LLM inference error: {e}")
            return ""
    
    def _parse_llm_response(self, response: str) -> Optional[IntentMatch]:
        """Parse LLM JSON response into IntentMatch."""
        try:
            # Extract JSON from response (handle any extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                return None
            
            json_str = response[json_start:json_end]
            parsed = json.loads(json_str)
            
            api_function = parsed.get("api_function", "")
            if api_function not in self.api_knowledge_base:
                return None
            
            api_info = self.api_knowledge_base[api_function]
            
            return IntentMatch(
                api_function=api_function,
                confidence=float(parsed.get("confidence", 0.0)),
                reasoning=parsed.get("reasoning", ""),
                category=api_info["category"],
                description=api_info["description"],
                related_functions=api_info.get("related", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None
    
    def _semantic_similarity_search(self, query: str) -> List[IntentMatch]:
        """Fallback semantic similarity search."""
        if not self.semantic_model:
            return []
        
        try:
            query_embedding = self.semantic_model.encode([query])
            matches = []
            
            # Create embeddings for all use cases
            for api_func, info in self.api_knowledge_base.items():
                use_cases = info["use_cases"]
                use_case_embeddings = self.semantic_model.encode(use_cases)
                
                # Calculate similarity scores
                similarities = np.dot(query_embedding, use_case_embeddings.T).flatten()
                max_similarity = np.max(similarities)
                
                if max_similarity > 0.3:  # Minimum threshold
                    matches.append(IntentMatch(
                        api_function=api_func,
                        confidence=float(max_similarity),
                        reasoning=f"Semantic similarity with: {use_cases[np.argmax(similarities)]}",
                        category=info["category"],
                        description=info["description"],
                        related_functions=info.get("related", [])
                    ))
            
            # Sort by confidence and return top 3
            matches.sort(key=lambda x: x.confidence, reverse=True)
            return matches[:3]
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    async def extract_intent(self, query: str) -> List[IntentMatch]:
        """
        Extract API function intents from natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            List of IntentMatch objects sorted by confidence
        """
        query = query.strip()
        if not query:
            return []
        
        start_time = time.time()
        matches = []
        
        # Try LLM first (most accurate but slower)
        llm_match = await self._query_llm_async(query)
        if llm_match and llm_match.confidence > 0.6:
            matches.append(llm_match)
            logger.info(f"LLM match: {llm_match.api_function} (confidence: {llm_match.confidence:.2f})")
        
        # Add semantic similarity matches
        semantic_matches = self._semantic_similarity_search(query)
        
        # Combine results, avoiding duplicates
        seen_functions = {match.api_function for match in matches}
        for match in semantic_matches:
            if match.api_function not in seen_functions:
                matches.append(match)
        
        # Sort by confidence
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        elapsed = time.time() - start_time
        logger.info(f"Intent extraction completed in {elapsed:.3f}s, found {len(matches)} matches")
        
        return matches[:5]  # Return top 5 matches
    
    def get_api_info(self, api_function: str) -> Optional[Dict]:
        """Get detailed information about an API function."""
        return self.api_knowledge_base.get(api_function)
    
    def suggest_related_functions(self, api_function: str) -> List[str]:
        """Get related API functions for a given function."""
        info = self.api_knowledge_base.get(api_function, {})
        return info.get("related", [])
    
    def health_check(self) -> Dict[str, any]:
        """Check health of intent mapper components."""
        return {
            "llm_available": self.llm_model is not None,
            "semantic_available": self.semantic_model is not None,
            "api_functions_loaded": len(self.api_knowledge_base),
            "device": self.device,
            "gpu_available": torch.cuda.is_available() if HAS_TRANSFORMERS else False
        }

# Global instance
_intent_mapper = None

def get_intent_mapper() -> LLMIntentMapper:
    """Get global intent mapper instance (singleton)."""
    global _intent_mapper
    if _intent_mapper is None:
        _intent_mapper = LLMIntentMapper()
    return _intent_mapper