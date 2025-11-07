# Azure Anomaly Detection System

An enterprise-grade AI-powered anomaly detection system for Azure Applications using Phi-4 and Azure AI Inference.

## 🚀 Quick Start

1. **Configuration**: Copy `local.settings.json.template` to `local.settings.json` and configure:
   - `AI_FOUNDATION_ENDPOINT`: Your Azure AI endpoint (e.g., `https://assurantpoc-resource.services.ai.azure.com/models`)
   - `AI_FOUNDATION_KEY`: Your Azure AI API key
   - `AI_FOUNDATION_MODEL`: Set to `Phi-4`
   - `APPINSIGHTS_RESOURCE_ID`: Application Insights resource to monitor
   - `LOGIC_APP_URL`: Webhook URL for alert notifications

2. **Deploy**: Use Azure Functions Core Tools:
   ```bash
   func azure functionapp publish YOUR_FUNCTION_APP_NAME
   ```

## 📋 Features

- **Real-time Monitoring**: Continuous 5-minute interval checks
- **20 Metrics Tracked**: Comprehensive application health monitoring 
- **AI-Powered Analysis**: Uses Microsoft Phi-4 for intelligent anomaly detection
- **Automated Alerting**: Instant notifications via Logic Apps
- **Cost-Optimized**: Pre-filtering reduces AI calls by ~80%

## 🏗️ Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for detailed system architecture and data flow.

## 🤖 AI Integration

See [`AI_ROLE_EXPLAINED.md`](AI_ROLE_EXPLAINED.md) for detailed explanation of Phi-4's role in anomaly detection.

## 📁 Project Structure

```
├── function_app.py          # Main Azure Function entry point
├── host.json               # Function app configuration  
├── requirements.txt        # Python dependencies
├── local.settings.json     # Local configuration (create from template)
├── shared/
│   ├── ai_foundry_client.py      # Phi-4 Azure AI Inference client
│   ├── anomaly_detection.py      # Core anomaly detection algorithms
│   ├── metrics_query.py          # Application Insights data querying
│   ├── logic_app_client.py       # Alert notification handler
│   └── state_manager.py          # Historical data management
├── ARCHITECTURE.md         # System architecture documentation
└── AI_ROLE_EXPLAINED.md    # AI integration explanation
```

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AI_FOUNDATION_ENDPOINT` | Azure AI models endpoint | `https://your-resource.services.ai.azure.com/models` |
| `AI_FOUNDATION_KEY` | Azure AI API key | `your-api-key` |
| `AI_FOUNDATION_MODEL` | Model name | `Phi-4` |
| `APPINSIGHTS_RESOURCE_ID` | Target Application Insights resource | `/subscriptions/.../components/app-name` |
| `LOGIC_APP_URL` | Alert webhook URL | `https://prod-xx.eastus.logic.azure.com/...` |

### Optional Tuning Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `ANOMALY_CONFIDENCE_THRESHOLD` | `0.85` | Minimum confidence to trigger alert |
| `METRICS_LOOKBACK_MINUTES` | `10` | Historical data window |
| `TIMER_INTERVAL_MINUTES` | `5` | Check frequency |
| `ENABLE_PREFILTER` | `true` | Enable cost-saving pre-filter |

## 🧠 Phi-4 Integration

This system uses Microsoft's Phi-4 model via Azure AI Inference for intelligent anomaly analysis:

- **Authentication**: API Key based authentication
- **Endpoint**: Serverless API deployment
- **Model**: Phi-4 optimized for reasoning tasks
- **SDK**: `azure-ai-inference` official Microsoft SDK

The AI provides:
- Anomaly classification (true/false)
- Severity assessment (low/medium/high)  
- Confidence scoring (0.0-1.0)
- Trend prediction and next value estimation
- Actionable recommendations

## 🔍 Monitored Metrics

1. **Request Metrics**: Requests/sec, Success rate, Failed requests
2. **Performance**: Response times, Server response time
3. **Dependencies**: Dependency calls, SQL queries, Redis operations  
4. **Resources**: CPU usage, Memory usage, Disk I/O
5. **Availability**: Uptime percentage, Health check results
6. **Custom**: Business-specific KPIs

## 📊 Statistical Analysis

Each metric undergoes 43 statistical calculations:
- Central tendency (mean, median, mode)
- Variability (std dev, variance, range)  
- Distribution analysis (skewness, kurtosis)
- Trend detection (linear regression, momentum)
- Outlier identification (z-score, IQR)

## 🚨 Alert Flow

1. **Data Collection**: Query Application Insights every 5 minutes
2. **Statistical Analysis**: Calculate 43 measures per metric
3. **Pre-filtering**: Fast statistical checks to reduce AI calls
4. **AI Analysis**: Phi-4 analyzes suspicious patterns only  
5. **Alert Decision**: Confidence threshold determines alerting
6. **Notification**: Logic App sends alerts to configured channels

## 🔐 Security

- API keys stored in Azure Key Vault (recommended) or App Settings
- Managed Identity for Azure service authentication
- HTTPS-only communication
- Audit logging enabled

## 📈 Performance

- **Cost Optimized**: Pre-filter reduces AI calls by ~80%
- **Fast Response**: <30 seconds end-to-end analysis
- **Scalable**: Handles 100+ metrics across multiple applications
- **Reliable**: Built-in retry logic and fallback responses