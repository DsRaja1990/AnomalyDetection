"""
AI Foundry Client Module (Using Official Azure AI Inference SDK)
Handles communication with Azure AI Foundry using the recommended azure-ai-inference library
"""
import os
import json
import logging
from typing import Dict, List, Optional
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)


class AIFoundryClient:
    """Client for Azure AI Foundry model interactions using official SDK"""
    
    SYSTEM_PROMPT = """You are an expert Azure monitoring AI with deep understanding of application performance patterns, failure modes, and predictive analytics.

ANALYZE the provided metrics data using advanced reasoning to:
1. Detect current anomalies and their root causes
2. Predict future issues before they become critical  
3. Provide actionable recommendations for prevention
4. Assess business impact and urgency

Consider:
- Temporal patterns, trends, and seasonality
- Correlations between metrics  
- Historical context and baselines
- Business hours vs off-hours patterns
- Cascade failure scenarios
- Performance degradation indicators

RESPOND with VALID JSON in this EXACT format:
{
  "isAnomaly": true,
  "severity": "high", 
  "confidence": 0.85,
  "trend": "increasing",
  "nextValue": 250.5,
  "timeToNextAnomaly": 15,
  "rootCause": "Memory leak detected - heap usage growing linearly",
  "businessImpact": "User experience degradation expected",
  "recommendedActions": ["Scale up memory", "Restart affected instances", "Enable memory profiling"],
  "urgency": "high",
  "cascadeRisk": 0.7,
  "prediction": {
    "5min": {"value": 180.2, "anomalyRisk": 0.3},
    "10min": {"value": 195.8, "anomalyRisk": 0.6}, 
    "15min": {"value": 210.4, "anomalyRisk": 0.85}
  },
  "reasoning": "Response times show 40% increase over baseline with accelerating trend. Memory usage correlates strongly (r=0.89), indicating memory pressure. Pattern matches previous incident on 2024-10-15."
}"""
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model_name: str = "Phi-4",
        timeout: int = 30
    ):
        """
        Initialize AI Foundry client using official Azure AI Inference SDK
        
        Args:
            endpoint: Endpoint URL - should be the full models endpoint
            api_key: API key for authentication
            model_name: Model name to use (default: "Phi-4")
            timeout: Request timeout in seconds
        """
        # Handle both endpoint formats for flexibility
        # Format 1: https://resource.services.ai.azure.com/models (preferred)
        # Format 2: https://resource.services.ai.azure.com/models/chat/completions?api-version=xxx
        
        if "/chat/completions" in endpoint:
            # Extract the base endpoint and remove chat/completions path
            base_endpoint = endpoint.split("/chat/completions")[0]
            if not base_endpoint.endswith("/models"):
                base_endpoint = base_endpoint.rstrip("/") + "/models"
            logger.info(f"Converted endpoint from {endpoint} to {base_endpoint}")
            endpoint = base_endpoint
        elif not endpoint.endswith("/models"):
            # Add /models if not present
            endpoint = endpoint.rstrip("/") + "/models"
        
        # Create ChatCompletionsClient using the official Azure AI Inference SDK
        self.client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
            api_version="2024-05-01-preview"  # Required for Phi-4 and newer models
        )
        self.model_name = model_name
        self.timeout = timeout
        logger.info(f"AIFoundryClient initialized with endpoint: {endpoint}, model: {model_name}")
    
    def analyze_metrics(
        self,
        metrics_data: Dict[str, any],
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze metrics data using AI Foundry model
        
        Args:
            metrics_data: Dictionary containing metric statistics
            context: Optional historical context
            
        Returns:
            Parsed JSON response from model
        """
        # Build user prompt with metrics data
        user_prompt = self._build_analysis_prompt(metrics_data, context)
        
        try:
            logger.info(f"Calling Azure AI Inference SDK with model: {self.model_name}")
            
            # Use the official SDK's complete() method
            # Based on Microsoft's Phi-4 example with recommended parameters
            response = self.client.complete(
                messages=[
                    SystemMessage(content=self.SYSTEM_PROMPT),
                    UserMessage(content=f"JSON_ONLY: {user_prompt}")
                ],
                model=self.model_name,  # Required: specify which model to use
                max_tokens=2048,
                temperature=0.8,
                top_p=0.1,
                presence_penalty=0.0,
                frequency_penalty=0.0
            )
            
            # Extract the assistant's message content
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                
                logger.info(f"Raw response length: {len(content)} chars")
                
                # Phi-4 sometimes wraps response in <think> tags - extract JSON only
                json_content = self._extract_json_from_response(content)
                
                if not json_content or not json_content.strip():
                    logger.error("Could not extract JSON from response")
                    logger.error(f"Raw content (first 1000 chars): {content[:1000]}")
                    return self._get_fallback_response()
                
                # Parse the JSON response
                try:
                    parsed_response = json.loads(json_content)
                    
                    # Map and validate enhanced response fields
                    # Ensure backward compatibility while supporting new rich format
                    if "recommendedActions" in parsed_response and "action" not in parsed_response:
                        actions = parsed_response["recommendedActions"]
                        parsed_response["action"] = actions[0] if isinstance(actions, list) and actions else "monitor"
                    
                    # Extract prediction summary for backward compatibility
                    if "prediction" in parsed_response and "nextValue" not in parsed_response:
                        prediction = parsed_response["prediction"]
                        if isinstance(prediction, dict) and "5min" in prediction:
                            parsed_response["nextValue"] = prediction["5min"].get("value", 0)
                    
                    # Ensure required fields exist with defaults
                    defaults = {
                        "isAnomaly": False,
                        "severity": "low", 
                        "confidence": 0.0,
                        "trend": "stable",
                        "nextValue": 0.0,
                        "action": "monitor",
                        "urgency": "low",
                        "cascadeRisk": 0.0,
                        "businessImpact": "minimal",
                        "reasoning": "Normal operation"
                    }
                    
                    for field, default_value in defaults.items():
                        if field not in parsed_response:
                            parsed_response[field] = default_value
                    
                    self._validate_response(parsed_response)
                    
                    logger.info(f"AI Analysis: isAnomaly={parsed_response.get('isAnomaly')}, "
                              f"severity={parsed_response.get('severity')}, "
                              f"confidence={parsed_response.get('confidence')}")
                    
                    return parsed_response
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse model response as JSON: {e}")
                    logger.error(f"Extracted content (first 500 chars): {json_content[:500]}")
                    return self._get_fallback_response()
            else:
                logger.error(f"Unexpected response format from SDK")
                return self._get_fallback_response()
                
        except Exception as e:
            logger.error(f"Error calling Azure AI Inference SDK: {e}", exc_info=True)
            return self._get_fallback_response()
    
    def _build_analysis_prompt(
        self,
        metrics_data: Dict[str, any],
        context: Optional[Dict] = None
    ) -> str:
        """
        Build rich analysis prompt leveraging Phi-4's reasoning capabilities
        """
        from datetime import datetime
        
        # Start with metric analysis
        metric_analyses = []
        
        for metric_name, stats in metrics_data.items():
            # Get the latest value from the correct field structure
            # The metrics_query returns latest_value in central_tendency
            central_tendency = stats.get("central_tendency", {})
            current = central_tendency.get("latest_value", 0)
            mean = central_tendency.get("mean", 0)
            
            # Fallback: if central_tendency is missing, try data_points
            if current == 0 and mean == 0 and "data_points" in stats:
                data_points = stats["data_points"]
                if data_points:
                    current = data_points[-1] if isinstance(data_points, list) else 0
                    mean = sum(data_points) / len(data_points) if isinstance(data_points, list) else 0
            
            # Get std_dev from dispersion section
            dispersion = stats.get("dispersion", {})
            std_dev = dispersion.get("std_dev", 0)
            
            # Calculate deviation
            deviation_pct = ((current - mean) / mean * 100) if mean > 0 else 0
            z_score = ((current - mean) / std_dev) if std_dev > 0 else 0
            
            # Debug logging for data structure issues
            logger.info(f"AI Prompt Data - {metric_name}: current={current:.2f}, mean={mean:.2f}, std_dev={std_dev:.2f}")
            
            metric_analysis = f"METRIC: {metric_name}\n"
            metric_analysis += f"- Current: {current:.2f}, Mean: {mean:.2f}, StdDev: {std_dev:.2f}\n"
            metric_analysis += f"- Deviation: {deviation_pct:.1f}%, Z-score: {z_score:.2f}\n"
            
            # Add enhanced analysis if available
            if context and "enhanced_analysis" in context:
                ea = context["enhanced_analysis"]
                metric_analysis += f"- Trend: {ea.get('trend', 'unknown')} (strength: {ea.get('trend_strength', 0):.2f})\n"
                metric_analysis += f"- Change Rate: {ea.get('change_rate', 0):.1f}%\n"
                metric_analysis += f"- Anomaly Score: {ea.get('score', 0):.3f}\n"
                
                if ea.get('spikes_detected', 0) > 0:
                    metric_analysis += f"- Spikes Detected: {ea.get('spikes_detected')}\n"
                
                if ea.get('seasonality'):
                    seasonality = ea['seasonality']
                    if seasonality.get('detected'):
                        metric_analysis += f"- Seasonality: {seasonality.get('pattern', 'detected')}\n"
                
                # Add predictions if available
                predictions = ea.get('predictions', [])
                if predictions:
                    metric_analysis += f"- Predicted Anomalies: {len(predictions)} in next 15min\n"
            
            metric_analyses.append(metric_analysis)
        
        # Build comprehensive prompt
        prompt = "=== AZURE METRICS ANALYSIS ===\n"
        prompt += f"Timestamp: {datetime.utcnow().isoformat()}\n\n"
        
        # Add metrics data
        for analysis in metric_analyses:
            prompt += analysis + "\n"
        
        # Add historical context
        if context:
            prompt += "=== HISTORICAL CONTEXT ===\n"
            
            if context.get("baseline"):
                baseline = context["baseline"]
                current_avg = mean  # Use current mean as proxy
                baseline_dev = ((current_avg - baseline) / baseline * 100) if baseline > 0 else 0
                prompt += f"Historical Baseline: {baseline:.2f} (current deviation: {baseline_dev:.1f}%)\n"
            
            # Add correlation information
            if context.get("correlations"):
                prompt += "Metric Correlations:\n"
                for corr in context["correlations"]:
                    prompt += f"- {corr.get('metric1')} ↔ {corr.get('metric2')}: r={corr.get('correlation', 0):.2f} ({corr.get('insight', '')})\n"
            
            # Add previous anomalies
            if context.get("previous_anomalies"):
                recent_anomalies = context["previous_anomalies"][-3:]  # Last 3 anomalies
                if recent_anomalies:
                    prompt += "Recent Anomalies:\n"
                    for anomaly in recent_anomalies:
                        prompt += f"- {anomaly.get('timestamp', 'unknown')}: {anomaly.get('metric_name', 'unknown')} ({anomaly.get('severity', 'unknown')})\n"
        
        # Add analysis instructions
        prompt += "\n=== ANALYSIS REQUEST ===\n"
        prompt += "Perform deep analysis considering:\n"
        prompt += "1. Current anomaly status and severity assessment\n"
        prompt += "2. Root cause analysis based on patterns and correlations\n"
        prompt += "3. Predictive forecasting for next 5, 10, and 15 minutes\n"
        prompt += "4. Business impact assessment and urgency level\n"
        prompt += "5. Specific actionable recommendations\n"
        prompt += "6. Cascade failure risk assessment\n\n"
        
        # Add domain-specific context
        current_hour = datetime.utcnow().hour
        if 9 <= current_hour <= 17:
            prompt += "CONTEXT: Business hours - high user activity expected\n"
        elif 22 <= current_hour or current_hour <= 6:
            prompt += "CONTEXT: Off-hours - maintenance window, low user activity\n"
        else:
            prompt += "CONTEXT: Peak usage transition period\n"
        
        return prompt
    
    def _extract_json_from_response(self, content: str) -> str:
        """
        Extract JSON from Phi-4 response - ULTRA SIMPLE VERSION
        If model returns anything without { }, use fallback immediately.
        """
        if not content or not content.strip():
            logger.error("Empty response")
            return ""
        
        # Quick check: is there even a { in the response?
        if '{' not in content:
            logger.error(f"No JSON found (no {{ character). Response: {content[:200]}")
            return ""
        
        # Try to extract JSON by finding { and matching }
        try:
            start_idx = content.find('{')
            if start_idx == -1:
                return ""
            
            # Use bracket counting
            brace_count = 0
            in_string = False
            escape = False
            
            for i in range(start_idx, len(content)):
                ch = content[i]
                
                if escape:
                    escape = False
                    continue
                    
                if ch == '\\':
                    escape = True
                    continue
                    
                if ch == '"':
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if ch == '{':
                        brace_count += 1
                    elif ch == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = content[start_idx:i+1]
                            # Validate it's real JSON
                            try:
                                json.loads(json_str)
                                logger.info("Extracted valid JSON successfully")
                                return json_str
                            except:
                                logger.error(f"Extracted string is not valid JSON: {json_str[:100]}")
                                return ""
            
            logger.error("Unmatched braces - no complete JSON found")
            return ""
            
        except Exception as e:
            logger.error(f"JSON extraction error: {e}")
            return ""
    
    def _validate_response(self, response: Dict) -> None:
        """Validate that response has required fields (supports both old and new names)"""
        # Support both naming conventions
        required_fields = ["isAnomaly", "severity"]  # Minimum required
        for field in required_fields:
            if field not in response:
                logger.warning(f"Response missing required field: {field}")
    
    def _get_fallback_response(self) -> Dict:
        """Return fallback response when AI analysis fails"""
        return {
            "isAnomaly": False,
            "severity": "low",
            "trend": "stable", 
            "confidence": 0.0,
            "nextValue": 0.0,
            "timeToNextAnomaly": None,
            "rootCause": "AI analysis unavailable",
            "businessImpact": "unknown - requires manual review",
            "recommendedActions": ["monitor", "review logs"],
            "urgency": "low",
            "cascadeRisk": 0.0,
            "prediction": {
                "5min": {"value": 0.0, "anomalyRisk": 0.0},
                "10min": {"value": 0.0, "anomalyRisk": 0.0},
                "15min": {"value": 0.0, "anomalyRisk": 0.0}
            },
            "reasoning": "AI model error - falling back to statistical analysis",
            "action": "monitor"  # For backward compatibility
        }


def create_ai_client() -> Optional[AIFoundryClient]:
    """
    Factory function to create AIFoundryClient from environment
    
    Environment variables:
        AI_FOUNDATION_ENDPOINT: Azure AI endpoint URL (e.g., https://assurantpoc-resource.services.ai.azure.com/models)
        AI_FOUNDATION_KEY: API key for authentication
        AI_FOUNDATION_MODEL: Model name (default: Phi-4)
    
    Returns:
        AIFoundryClient instance or None if config missing
    """
    endpoint = os.getenv("AI_FOUNDATION_ENDPOINT")
    api_key = os.getenv("AI_FOUNDATION_KEY")
    model_name = os.getenv("AI_FOUNDATION_MODEL", "Phi-4")  # Default to Phi-4
    
    if not endpoint or not api_key:
        logger.error("AI_FOUNDATION_ENDPOINT and AI_FOUNDATION_KEY must be set")
        return None
    
    logger.info(f"Creating AI client with model: {model_name}")
    return AIFoundryClient(endpoint, api_key, model_name)
