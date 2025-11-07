# Metrics Lookback Configuration Complete

## Summary
Successfully converted the hardcoded 60-minute lookback period to use the configurable `METRICS_LOOKBACK_MINUTES` environment variable and reduced it to 15 minutes as requested.

## Changes Made

### 1. Updated `local.settings.json`
- **Changed** `METRICS_LOOKBACK_MINUTES` from "25" to "15"
- This sets the default lookback period to 15 minutes for local development

### 2. Updated `function_app.py`
- **Replaced** hardcoded `lookback_minutes = 60` with `lookback_minutes = int(os.getenv("METRICS_LOOKBACK_MINUTES", "15"))`
- **Updated** the `get_recent_anomalies()` call to use environment variable instead of hardcoded 60
- Now dynamically reads the lookback period from configuration

### 3. Updated `shared/state_manager.py` 
- **Modified** `get_recent_metrics()` method:
  - Changed default parameter from `lookback_minutes: int = 60` to `lookback_minutes: int = None`
  - Added logic to read from environment variable when None: `lookback_minutes = int(os.getenv("METRICS_LOOKBACK_MINUTES", "15"))`
- **Modified** `get_recent_anomalies()` method:
  - Changed default parameter from `lookback_minutes: int = 60` to `lookback_minutes: int = None`  
  - Added logic to read from environment variable when None
- **Updated** method documentation to reflect the new behavior

### 4. Updated Azure Function App Settings
- **Set** `METRICS_LOOKBACK_MINUTES` to "15" in the Azure Function App environment

## Environment Variable Configuration

### Current Value
```json
"METRICS_LOOKBACK_MINUTES": "15"
```

### Usage Pattern
```python
# In function_app.py
lookback_minutes = int(os.getenv("METRICS_LOOKBACK_MINUTES", "15"))

# In state_manager.py methods
if lookback_minutes is None:
    lookback_minutes = int(os.getenv("METRICS_LOOKBACK_MINUTES", "15"))
```

## Benefits

### ✅ **No More Hardcoded Values**
- Removed all hardcoded 60-minute lookback periods
- System now uses configurable environment variable

### ✅ **Reduced Lookback Period**
- Changed from 60 minutes to 15 minutes as requested
- More responsive anomaly detection with recent data focus

### ✅ **Flexible Configuration**
- Easy to adjust lookback period without code changes
- Can be different for development vs production environments

### ✅ **Consistent Behavior**
- All components use the same lookback configuration
- Single source of truth for metrics analysis window

### ✅ **Environment-Specific Settings**
- Local development: 15 minutes (via `local.settings.json`)
- Azure production: 15 minutes (via Function App settings)
- Can be easily adjusted for different environments

## Impact on Anomaly Detection

### **Faster Response Time**
- 15-minute window provides more recent data analysis
- Quicker detection of emerging issues

### **Reduced Noise**
- Smaller time window focuses on current state
- Less historical data dilution

### **Cost Optimization**
- Smaller query window reduces Application Insights query costs
- Faster query execution times

### **More Targeted Analysis**
- Focused on immediate operational state
- Better for real-time monitoring scenarios

## Usage

To modify the lookback period:

**Local Development:**
```json
// In local.settings.json
"METRICS_LOOKBACK_MINUTES": "15"
```

**Azure Production:**
```bash
az functionapp config appsettings set --name anamolypoc --resource-group RG-AssurantMonitoring --settings METRICS_LOOKBACK_MINUTES="15"
```

**Supported Values:**
- Any positive integer (in minutes)
- Examples: "5", "10", "15", "30", "60"
- Default fallback: "15" if not specified

## Testing Results

✅ **Environment Variable Configuration**: PASS  
✅ **Default Value Logic**: PASS  
✅ **Configurable Values**: PASS  
✅ **Function App Integration**: PASS  

All components now correctly use the 15-minute configurable lookback period instead of the hardcoded 60-minute value.
