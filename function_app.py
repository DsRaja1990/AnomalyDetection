"""
Azure Functions AI Detection Timer - Clean Version
Simplified logging for better readability
"""

import azure.functions as func
import logging
import json
import traceback
from datetime import datetime, timedelta
import os

app = func.FunctionApp()

@app.function_name(name="AIDetectionTimer")
@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=True, use_monitor=False)
def AIDetectionTimer(timer: func.TimerRequest) -> None:
    """
    Enhanced AI-powered anomaly detection with clean logging
    """
    
    # Prevent concurrent runs (simple file-based lock)
    lock_file = "/tmp/anomaly_detection.lock"
    
    if os.path.exists(lock_file):
        logging.info("Another instance is running. Skipping.")
        return
    
    # Remove stale locks
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
    except:
        pass
    
    # Create lock file
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    logger.info("=== ANOMALY DETECTION STARTING ===")
    
    try:
        # Import shared modules
        from shared.metrics_query import create_metrics_service
        from shared.ai_foundry_client import create_ai_client
        from shared.state_manager import create_state_manager
        from shared.anomaly_detection import create_prefilter
        from shared.enhanced_anomaly_detection import create_enhanced_detector
        from shared.logic_app_client import create_logic_app_client
        
        timestamp = datetime.utcnow()
        logger.info(f"Anomaly detection started at {timestamp.isoformat()}")
        
        # Initialize services
        metrics_service = create_metrics_service()
        ai_client = create_ai_client()
        state_manager = create_state_manager()
        prefilter = create_prefilter()
        enhanced_detector = create_enhanced_detector()
        logic_app_client = create_logic_app_client()
        
        # Validation
        if not metrics_service or not ai_client:
            logger.error("Failed to initialize core services.")
            return
        
        # Query metrics
        lookback_minutes = int(os.getenv("METRICS_LOOKBACK_MINUTES", "15"))
        logger.info(f"Querying metrics for last {lookback_minutes} minutes...")
        
        try:
            metrics_data = metrics_service.query_all_metrics(timespan_minutes=lookback_minutes)
            
            if not metrics_data:
                logger.warning("No metrics data retrieved. Skipping analysis.")
                return
                
            logger.info(f"Retrieved metrics data for {len(metrics_data)} metrics")
            
        except Exception as query_error:
            logger.error(f"Metrics query failed: {query_error}")
            return
        
        # Process metrics statistics
        metrics_stats = {}
        for metric_name, metric_info in metrics_data.items():
            if metric_info and metric_info.get("data_points"):
                # Preserve the complete statistics structure from metrics_query
                stats = metric_info["statistics"]
                data_points = metric_info["data_points"]
                
                # Add raw data points for backward compatibility
                stats["data_points"] = [dp["value"] for dp in data_points]
                
                # Ensure latest_value is correctly set in central_tendency if missing
                if "central_tendency" in stats:
                    ct = stats["central_tendency"]
                    if "latest_value" not in ct or ct.get("latest_value", 0) == 0:
                        # Use the last data point as latest_value if missing
                        if data_points:
                            latest_value = data_points[-1]["value"]
                            ct["latest_value"] = latest_value
                            logger.info(f"Fixed latest_value for {metric_name}: {latest_value}")
                
                metrics_stats[metric_name] = stats
        
        logger.info(f"Processed statistics for {len(metrics_stats)} metrics")
        
        # Save metrics snapshot
        if state_manager:
            state_manager.save_metrics_snapshot(timestamp, metrics_stats)
        
        # Pre-filter analysis
        metrics_to_analyze = []
        if prefilter:
            logger.info("Running pre-filter analysis...")
            prefilter_results = {}
            
            # Check each metric with the prefilter
            for metric_name, stats in metrics_stats.items():
                should_analyze, reason = prefilter.should_trigger_ai_analysis(metric_name, stats)
                prefilter_results[metric_name] = {
                    'needs_analysis': should_analyze,
                    'reason': reason
                }
                if should_analyze:
                    logger.info(f"Pre-filter: {metric_name} flagged - {reason}")
            
            # Get metrics that need analysis
            metrics_to_analyze = [
                metric for metric, result in prefilter_results.items()
                if result.get('needs_analysis')
            ]
            
            if not metrics_to_analyze:
                logger.info("Pre-filter: No immediate anomalies. Analyzing key metrics anyway...")
                metrics_to_analyze = ['request_failed', 'exception_count', 'request_duration']
        else:
            metrics_to_analyze = list(metrics_stats.keys())
        
        logger.info(f"Analyzing {len(metrics_to_analyze)} metrics: {metrics_to_analyze}")
        
        # Show key metrics summary with enhanced debugging
        logger.info("📊 KEY METRICS SUMMARY:")
        for metric_name in ['request_failed', 'exception_count', 'request_count']:
            if metric_name in metrics_stats:
                stats = metrics_stats[metric_name]
                values = stats.get("data_points", [])
                if values:
                    total = sum(values)
                    max_val = max(values)
                    avg_val = sum(values) / len(values)
                    latest_val = values[-1] if values else 0
                    logger.info(f"   {metric_name}: total={total:.0f}, max={max_val:.0f}, avg={avg_val:.1f}, latest={latest_val:.1f}")
                    
                    # Also show central_tendency data for comparison
                    if "central_tendency" in stats:
                        ct = stats["central_tendency"]
                        ct_latest = ct.get("latest_value", 0)
                        ct_mean = ct.get("mean", 0)
                        logger.info(f"     central_tendency: latest_value={ct_latest:.1f}, mean={ct_mean:.1f}")
                else:
                    logger.warning(f"   {metric_name}: no data_points found")
        
        # 🎯 CONSOLIDATED AI ANALYSIS - Single Call for Cost Optimization
        logger.info("🤖 Performing CONSOLIDATED AI analysis for cost optimization...")
        
        try:
            # Prepare consolidated metrics data for single AI call
            consolidated_metrics = {}
            enhanced_scores = {}
            
            for metric_name in metrics_to_analyze:
                metric_data = metrics_stats.get(metric_name, {})
                
                # Try to get values from either data_points or central_tendency structure
                values = metric_data.get("data_points", [])
                if not values and "central_tendency" in metric_data:
                    # Extract latest value from central_tendency if data_points is missing
                    ct = metric_data["central_tendency"]
                    latest_val = ct.get("latest_value", 0)
                    mean_val = ct.get("mean", 0)
                    if latest_val > 0 or mean_val > 0:
                        values = [latest_val]  # At minimum we have the latest value
                
                if values or "central_tendency" in metric_data:
                    # Calculate basic enhanced score without external dependencies
                    try:
                        if values:
                            # Use actual data points for scoring
                            avg_val = sum(values) / len(values)
                            max_val = max(values)
                            recent_val = values[-1] if values else 0
                        else:
                            # Use central_tendency data
                            ct = metric_data.get("central_tendency", {})
                            avg_val = ct.get("mean", 0)
                            max_val = ct.get("max", 0)
                            recent_val = ct.get("latest_value", 0)
                        
                        score = abs(recent_val - avg_val) / max(avg_val, 1) if avg_val > 0 else 0
                        
                        enhanced_scores[metric_name] = {
                            "score": min(score, 1.0),  # Cap at 1.0
                            "confidence": 0.8,
                            "trend": "increasing" if recent_val > avg_val else "stable"
                        }
                        
                        logger.info(f"Enhanced score for {metric_name}: recent={recent_val:.1f}, avg={avg_val:.1f}, score={score:.3f}")
                        
                    except Exception as e:
                        logger.warning(f"Enhanced scoring failed for {metric_name}: {e}")
                        enhanced_scores[metric_name] = {"score": 0.0, "confidence": 0.0, "trend": "unknown"}
                    
                    consolidated_metrics[metric_name] = metric_data
            
            if not consolidated_metrics:
                logger.warning("No metrics data for AI analysis")
                return
            
            # Prepare consolidated context
            context = {
                "timestamp": timestamp.isoformat(),
                "lookback_minutes": lookback_minutes,
                "enhanced_scores": enhanced_scores,
                "metrics_count": len(consolidated_metrics),
                "analysis_type": "consolidated_multi_metric"
            }
            
            # Get recent anomalies for context
            if state_manager:
                recent_anomalies = state_manager.get_recent_anomalies(lookback_minutes=int(os.getenv("METRICS_LOOKBACK_MINUTES", "15")))
                context["previous_anomalies"] = recent_anomalies[:5]  # Limit to last 5
            
            logger.info(f"  Sending {len(consolidated_metrics)} metrics to AI in single call...")
            
            # 🚀 SINGLE AI CALL - Cost Optimized
            analysis_result = ai_client.analyze_metrics(consolidated_metrics, context)
            
            if not analysis_result:
                logger.error("Consolidated AI analysis failed")
                return
            
            # Process consolidated results
            logger.info("🎯 CONSOLIDATED AI RESULTS:")
            overall_anomaly = analysis_result.get('isAnomaly', False)
            overall_confidence = float(analysis_result.get('confidence', 0))
            overall_severity = analysis_result.get('severity', 'unknown')
            overall_reasoning = analysis_result.get('reasoning', 'No reasoning provided')
            
            logger.info(f"📊 Overall Anomaly: {overall_anomaly}")
            logger.info(f"🎯 Overall Confidence: {overall_confidence:.2f}")
            logger.info(f"⚡ Overall Severity: {overall_severity}")
            logger.info(f"💭 AI Reasoning: {overall_reasoning}")
            
            # Extract individual metric results if available
            metric_results = analysis_result.get('metric_details', {})
            
            # Save consolidated results
            if state_manager:
                state_manager.save_anomaly_detection(timestamp, "consolidated_analysis", analysis_result)
            
            # 🚨 CONSOLIDATED ALERT DECISION
            # Dynamic confidence threshold based on severity
            base_confidence_threshold = float(os.getenv("ANOMALY_CONFIDENCE_THRESHOLD", "0.85"))
            
            # Lower threshold for medium/high severity issues to catch performance degradation
            if overall_severity in ["medium", "high", "critical"]:
                confidence_threshold = max(0.65, base_confidence_threshold - 0.15)
                logger.info(f"🎯 Adjusted confidence threshold for {overall_severity} severity: {confidence_threshold:.2f}")
            else:
                confidence_threshold = base_confidence_threshold
            
            logger.info("🎯 CONSOLIDATED ALERT DECISION:")
            logger.info(f"📊 Anomaly detected: {overall_anomaly}")
            logger.info(f"🎯 Confidence: {overall_confidence:.2f} (threshold: {confidence_threshold})")
            logger.info(f"⚡ Severity: {overall_severity}")
            
            if overall_anomaly and overall_confidence >= confidence_threshold:
                logger.info("🚨 SENDING CONSOLIDATED ALERT")
                
                # Send consolidated alert via Logic App
                if logic_app_client:
                    alert_payload = {
                        "analysis_type": "consolidated_multi_metric",
                        "metrics_analyzed": list(consolidated_metrics.keys()),
                        "anomaly_detected": overall_anomaly,
                        "confidence": overall_confidence,
                        "severity": overall_severity,
                        "reasoning": overall_reasoning,
                        "timestamp": timestamp.isoformat(),
                        "enhanced_scores": enhanced_scores,
                        "metric_details": metric_results,
                        "key_metrics_summary": {
                            "request_failed_total": sum(metrics_stats.get("request_failed", {}).get("data_points", [0])),
                            "exception_count_total": sum(metrics_stats.get("exception_count", {}).get("data_points", [0])),
                            "request_count_total": sum(metrics_stats.get("request_count", {}).get("data_points", [0]))
                        }
                    }
                    
                    try:
                        # Extract the main metric for the alert (first one analyzed)
                        main_metric = list(consolidated_metrics.keys())[0] if consolidated_metrics else "unknown"
                        main_metric_stats = metrics_stats.get(main_metric, {})
                        
                        # Get current value from central_tendency or data_points
                        if "central_tendency" in main_metric_stats:
                            current_value = main_metric_stats["central_tendency"].get("latest_value", 0)
                        else:
                            data_points = main_metric_stats.get("data_points", [])
                            current_value = data_points[-1] if data_points else 0
                        
                        # Send alert with correct signature
                        logic_app_client.send_alert(
                            metric_name=main_metric,
                            current_value=current_value,
                            analysis=analysis_result,
                            historical_context=alert_payload  # Send the full payload as historical context
                        )
                        logger.info("✅ Consolidated alert sent successfully")
                    except Exception as alert_error:
                        logger.error(f"❌ Consolidated alert sending failed: {alert_error}")
                        import traceback
                        logger.error(f"Alert error traceback: {traceback.format_exc()}")
            else:
                reason = "low confidence" if overall_confidence < confidence_threshold else "no anomaly"
                logger.info(f"Skipping alert: {reason}")
                
        except Exception as analysis_error:
            logger.error(f"Consolidated AI analysis failed: {analysis_error}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
        
        logger.info("Anomaly detection cycle completed successfully")
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR in anomaly detection: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        
    finally:
        # Clean up lock file
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except:
            pass
