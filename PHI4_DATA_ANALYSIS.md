# Data Sent to Phi-4 Model Analysis

## Overview
This document details the exact data structure and format sent to the Phi-4 model for anomaly analysis, apart from the system prompt.

## Complete Data Structure

### 1. **Metrics Data** (Primary Analysis Data)

Each metric contains the following statistical analysis:

```json
{
  "metric_name": {
    "central_tendency": {
      "mean": 1250.5,
      "median": 1100.0,
      "latest_value": 1850.2,
      "max": 2500.0,
      "min": 800.0
    },
    "dispersion": {
      "std_dev": 425.8,
      "variance": 181305.64,
      "range": 1700.0,
      "cv": 0.34
    },
    "data_points": [1100, 1150, 1200, 1300, 1450, 1600, 1750, 1850.2],
    "trend": "increasing",
    "time_coverage_minutes": 15
  }
}
```

**Metrics Typically Included:**
- `requests_duration` - Response time metrics
- `performance_counters_processor_time` - CPU utilization
- `requests_failed` - Failed request counts
- `performance_counters_memory` - Memory utilization
- `dependencies_duration` - External dependency latency
- `availability_results` - Availability test results
- `exceptions_count` - Exception counts

### 2. **Context Data** (Historical & Analytical Context)

```json
{
  "timestamp": "2025-11-07T11:42:16.386862",
  "lookback_minutes": 15,
  "enhanced_scores": {
    "requests_duration": {
      "score": 0.68,
      "confidence": 0.8,
      "trend": "increasing"
    }
  },
  "metrics_count": 3,
  "analysis_type": "consolidated_multi_metric",
  "previous_anomalies": [
    {
      "timestamp": "2025-11-07T11:37:16",
      "metric_name": "requests_failed",
      "severity": "high",
      "reason": "Spike detected"
    }
  ],
  "baseline": 1100.0,
  "correlations": [
    {
      "metric1": "requests_duration",
      "metric2": "performance_counters_processor_time",
      "correlation": 0.85,
      "insight": "Strong positive correlation - CPU load affecting response times"
    }
  ]
}
```

### 3. **Formatted Prompt Structure**

The data gets formatted into a structured prompt:

```
=== AZURE METRICS ANALYSIS ===
Timestamp: 2025-11-07T11:46:47.472096

METRIC: requests_duration
- Current: 1850.20, Mean: 1250.50, StdDev: 425.80
- Deviation: 48.0%, Z-score: 1.41
- Trend: increasing (strength: 0.75)
- Change Rate: 15.2%
- Anomaly Score: 0.682

METRIC: performance_counters_processor_time
- Current: 92.30, Mean: 75.20, StdDev: 8.50
- Deviation: 22.7%, Z-score: 2.01
- Trend: increasing (strength: 0.75)
- Change Rate: 15.2%
- Anomaly Score: 0.682

=== HISTORICAL CONTEXT ===
Historical Baseline: 1100.00 (current deviation: 13.7%)
Metric Correlations:
- requests_duration ↔ performance_counters_processor_time: r=0.85 (Strong positive correlation)
Recent Anomalies:
- 2025-11-07T11:37:16: requests_failed (high)
- 2025-11-07T11:32:16: performance_counters_processor_time (medium)

=== ANALYSIS REQUEST ===
Perform deep analysis considering:
1. Current anomaly status and severity assessment
2. Root cause analysis based on patterns and correlations
3. Predictive forecasting for next 5, 10, and 15 minutes
4. Business impact assessment and urgency level
5. Specific actionable recommendations
6. Cascade failure risk assessment

CONTEXT: Business hours - high user activity expected
```

## API Call Structure

### Complete API Payload

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert Azure metrics analyst. Analyze the provided metrics data and return ONLY a valid JSON response with no additional text, markdown, or explanations. The JSON must contain: anomalies_detected (boolean), severity (low/medium/high/critical), confidence (0.0-1.0), summary (string), details (array of findings), recommendations (array of actions), and reasoning (string explaining the analysis)."
    },
    {
      "role": "user",
      "content": "JSON_ONLY: [THE FORMATTED PROMPT ABOVE]"
    }
  ],
  "model": "Phi-4",
  "max_tokens": 2048,
  "temperature": 0.8,
  "top_p": 0.1,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0
}
```

### Model Parameters Explanation

- **`max_tokens: 2048`** - Maximum response length
- **`temperature: 0.8`** - Controls creativity vs consistency (0.8 = balanced)
- **`top_p: 0.1`** - Nucleus sampling (0.1 = focused responses)
- **`presence_penalty: 0.0`** - No penalty for topic repetition
- **`frequency_penalty: 0.0`** - No penalty for word frequency

## Data Processing Pipeline

### 1. **Raw Metrics Collection** (from Application Insights)
```
KQL Queries → Raw Time-Series Data → Statistical Analysis
```

### 2. **Statistical Analysis** (in metrics_query.py)
```python
# Central Tendency
mean = statistics.mean(values)
median = statistics.median(values)
latest_value = values[-1]

# Dispersion
std_dev = statistics.stdev(values)
variance = statistics.variance(values)
cv = std_dev / mean if mean > 0 else 0
```

### 3. **Enhanced Analysis** (in function_app.py)
```python
# Calculate enhanced scores
score = abs(recent_val - avg_val) / max(avg_val, 1)
deviation_pct = ((current - mean) / mean * 100)
z_score = ((current - mean) / std_dev)
```

### 4. **Context Enrichment**
- Historical baselines from state management
- Previous anomaly history (last 5 anomalies)
- Correlation analysis between metrics
- Business context (time of day)

## Cost and Performance Metrics

### **Per API Call:**
- **Input tokens**: ~522 (estimated)
- **Max output tokens**: 2,048
- **Total cost**: ~$0.10 per analysis
- **Response time**: 2-5 seconds typical

### **Payload Size:**
- **Total payload**: ~2,090 characters
- **System prompt**: 407 characters  
- **User prompt**: 1,420 characters
- **Model parameters**: 263 characters

## Key Data Elements Phi-4 Receives

### ✅ **Statistical Analysis**
- Current values vs historical means
- Standard deviations and z-scores
- Percentage deviations from normal
- Min/max ranges and variance

### ✅ **Trend Analysis**  
- Direction (increasing/decreasing/stable)
- Trend strength (0.0 - 1.0)
- Rate of change percentages
- Spike detection results

### ✅ **Contextual Intelligence**
- Previous anomaly patterns
- Metric correlations and relationships
- Historical baselines and deviations
- Business context (time of day)

### ✅ **Enhanced Scoring**
- Anomaly confidence scores (0.0 - 1.0)
- Severity assessments
- Risk level indicators
- Pattern recognition results

### ✅ **Time-Series Data**
- 15-minute lookback window (configurable)
- Data point arrays for trend analysis
- Time coverage statistics
- Temporal pattern recognition

## Analysis Instructions Given to Phi-4

The model is specifically instructed to provide:

1. **Anomaly Status Assessment** - Boolean detection with confidence
2. **Severity Classification** - Low/Medium/High/Critical levels
3. **Root Cause Analysis** - Pattern-based reasoning
4. **Predictive Forecasting** - 5, 10, 15-minute predictions
5. **Business Impact Assessment** - Urgency and impact evaluation
6. **Actionable Recommendations** - Specific remediation steps
7. **Cascade Failure Risk** - Downstream impact analysis

## Response Format Expected

```json
{
  "anomalies_detected": true,
  "severity": "high", 
  "confidence": 0.85,
  "summary": "Critical performance degradation detected",
  "details": ["High CPU usage correlating with response time spikes"],
  "recommendations": ["Scale compute resources", "Review recent deployments"],
  "reasoning": "Z-score analysis shows 2.01 standard deviations above normal..."
}
```

This comprehensive data structure ensures Phi-4 has complete contextual awareness for accurate anomaly detection and actionable recommendations.
