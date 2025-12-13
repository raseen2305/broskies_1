"""
Monitoring and alerting system for the GitHub Repository Evaluator
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from app.core.logging_config import get_logger, log_performance_metric, log_security_event

logger = get_logger("app.monitoring")

class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(str, Enum):
    """Types of metrics to monitor"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class Metric:
    """Metric data structure"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

class HealthCheck:
    """Health check for system components"""
    
    def __init__(self, name: str, check_func: Callable, interval: int = 60):
        self.name = name
        self.check_func = check_func
        self.interval = interval
        self.last_check = None
        self.last_result = None
        self.consecutive_failures = 0
    
    async def run_check(self) -> Dict[str, Any]:
        """Run the health check"""
        try:
            start_time = time.time()
            result = await self.check_func()
            duration = (time.time() - start_time) * 1000  # milliseconds
            
            self.last_check = datetime.utcnow()
            self.last_result = {
                "status": "healthy" if result.get("healthy", True) else "unhealthy",
                "duration_ms": duration,
                "details": result,
                "timestamp": self.last_check.isoformat()
            }
            
            if self.last_result["status"] == "healthy":
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
            
            return self.last_result
            
        except Exception as e:
            self.consecutive_failures += 1
            self.last_check = datetime.utcnow()
            self.last_result = {
                "status": "unhealthy",
                "error": str(e),
                "consecutive_failures": self.consecutive_failures,
                "timestamp": self.last_check.isoformat()
            }
            
            logger.error(f"Health check failed for {self.name}: {e}")
            return self.last_result

class MonitoringSystem:
    """Comprehensive monitoring system"""
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[Alert] = []
        self.health_checks: Dict[str, HealthCheck] = {}
        self.alert_handlers: List[Callable] = []
        self.running = False
        self.monitor_task = None
        
        # Performance thresholds
        self.thresholds = {
            "response_time_ms": 5000,  # 5 seconds
            "error_rate_percent": 5,   # 5%
            "memory_usage_percent": 85, # 85%
            "cpu_usage_percent": 80,   # 80%
            "disk_usage_percent": 90,  # 90%
            "cache_hit_rate_percent": 70, # 70%
            "database_connection_count": 50
        }
        
        # Rate limiting for alerts (prevent spam)
        self.alert_cooldown = defaultdict(lambda: datetime.min)
        self.alert_cooldown_duration = timedelta(minutes=5)
    
    def add_health_check(self, name: str, check_func: Callable, interval: int = 60):
        """Add a health check"""
        self.health_checks[name] = HealthCheck(name, check_func, interval)
        logger.info(f"Added health check: {name}")
    
    def add_alert_handler(self, handler: Callable):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
    
    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE, 
                     labels: Dict[str, str] = None, unit: str = ""):
        """Record a metric"""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            unit=unit
        )
        
        self.metrics[name].append(metric)
        
        # Log performance metric
        log_performance_metric(name, value, unit, **labels or {})
        
        # Check thresholds and generate alerts
        self._check_metric_thresholds(metric)
    
    def _check_metric_thresholds(self, metric: Metric):
        """Check if metric exceeds thresholds and generate alerts"""
        threshold_key = metric.name.lower().replace(" ", "_")
        threshold = self.thresholds.get(threshold_key)
        
        if threshold is None:
            return
        
        # Check if threshold is exceeded
        exceeded = False
        if "rate" in threshold_key or "usage" in threshold_key:
            exceeded = metric.value > threshold
        elif "time" in threshold_key:
            exceeded = metric.value > threshold
        
        if exceeded:
            alert_key = f"threshold_{threshold_key}"
            
            # Check cooldown
            if datetime.utcnow() - self.alert_cooldown[alert_key] < self.alert_cooldown_duration:
                return
            
            self.alert_cooldown[alert_key] = datetime.utcnow()
            
            # Generate alert
            alert = Alert(
                id=f"{alert_key}_{int(time.time())}",
                level=AlertLevel.WARNING if metric.value < threshold * 1.2 else AlertLevel.ERROR,
                title=f"Metric Threshold Exceeded: {metric.name}",
                message=f"{metric.name} is {metric.value}{metric.unit}, exceeding threshold of {threshold}{metric.unit}",
                timestamp=datetime.utcnow(),
                source="monitoring_system",
                details={
                    "metric_name": metric.name,
                    "metric_value": metric.value,
                    "threshold": threshold,
                    "labels": metric.labels
                }
            )
            
            self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: Alert):
        """Trigger an alert"""
        self.alerts.append(alert)
        
        # Log the alert
        logger.warning(
            f"Alert triggered: {alert.title}",
            extra={
                "alert_id": alert.id,
                "alert_level": alert.level,
                "alert_message": alert.message,
                "alert_details": alert.details
            }
        )
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                asyncio.create_task(handler(alert))
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def get_metrics(self, name: str, since: datetime = None) -> List[Metric]:
        """Get metrics by name, optionally filtered by time"""
        metrics = list(self.metrics.get(name, []))
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics
    
    def get_metric_summary(self, name: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        since = datetime.utcnow() - timedelta(minutes=duration_minutes)
        metrics = self.get_metrics(name, since)
        
        if not metrics:
            return {"name": name, "count": 0}
        
        values = [m.value for m in metrics]
        
        return {
            "name": name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1] if values else None,
            "unit": metrics[-1].unit if metrics else "",
            "duration_minutes": duration_minutes
        }
    
    def get_alerts(self, level: AlertLevel = None, resolved: bool = None) -> List[Alert]:
        """Get alerts, optionally filtered by level and resolution status"""
        alerts = self.alerts
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                logger.info(f"Alert resolved: {alert_id}")
                return True
        
        return False
    
    async def run_health_checks(self):
        """Run all health checks"""
        results = {}
        
        for name, health_check in self.health_checks.items():
            # Check if it's time to run this health check
            if (health_check.last_check is None or 
                datetime.utcnow() - health_check.last_check >= timedelta(seconds=health_check.interval)):
                
                result = await health_check.run_check()
                results[name] = result
                
                # Generate alerts for unhealthy services
                if result["status"] == "unhealthy" and health_check.consecutive_failures >= 3:
                    alert_key = f"health_check_{name}"
                    
                    # Check cooldown
                    if datetime.utcnow() - self.alert_cooldown[alert_key] < self.alert_cooldown_duration:
                        continue
                    
                    self.alert_cooldown[alert_key] = datetime.utcnow()
                    
                    alert = Alert(
                        id=f"{alert_key}_{int(time.time())}",
                        level=AlertLevel.ERROR,
                        title=f"Health Check Failed: {name}",
                        message=f"Health check for {name} has failed {health_check.consecutive_failures} times",
                        timestamp=datetime.utcnow(),
                        source="health_check",
                        details=result
                    )
                    
                    self._trigger_alert(alert)
        
        return results
    
    async def start_monitoring(self):
        """Start the monitoring system"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting monitoring system")
        
        async def monitor_loop():
            while self.running:
                try:
                    # Run health checks
                    await self.run_health_checks()
                    
                    # Clean up old metrics (keep last 24 hours)
                    cutoff_time = datetime.utcnow() - timedelta(hours=24)
                    for name, metric_deque in self.metrics.items():
                        # Remove old metrics
                        while metric_deque and metric_deque[0].timestamp < cutoff_time:
                            metric_deque.popleft()
                    
                    # Clean up old alerts (keep last 7 days)
                    alert_cutoff = datetime.utcnow() - timedelta(days=7)
                    self.alerts = [a for a in self.alerts if a.timestamp >= alert_cutoff]
                    
                    # Wait before next iteration
                    await asyncio.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(60)  # Wait longer on error
        
        self.monitor_task = asyncio.create_task(monitor_loop())
    
    async def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping monitoring system")
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        # Get health check results
        health_status = {}
        overall_healthy = True
        
        for name, health_check in self.health_checks.items():
            if health_check.last_result:
                health_status[name] = health_check.last_result
                if health_check.last_result["status"] != "healthy":
                    overall_healthy = False
            else:
                health_status[name] = {"status": "unknown", "message": "Not checked yet"}
                overall_healthy = False
        
        # Get recent alerts
        recent_alerts = self.get_alerts(resolved=False)
        critical_alerts = [a for a in recent_alerts if a.level == AlertLevel.CRITICAL]
        error_alerts = [a for a in recent_alerts if a.level == AlertLevel.ERROR]
        
        # Determine overall status
        if critical_alerts:
            overall_status = "critical"
        elif error_alerts or not overall_healthy:
            overall_status = "degraded"
        elif recent_alerts:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "health_checks": health_status,
            "alerts": {
                "total": len(recent_alerts),
                "critical": len(critical_alerts),
                "error": len(error_alerts),
                "warning": len([a for a in recent_alerts if a.level == AlertLevel.WARNING])
            },
            "monitoring": {
                "running": self.running,
                "metrics_tracked": len(self.metrics),
                "health_checks": len(self.health_checks)
            }
        }

# Global monitoring instance
monitoring_system = MonitoringSystem()

# Convenience functions

def record_metric(name: str, value: float, metric_type: MetricType = MetricType.GAUGE, 
                 labels: Dict[str, str] = None, unit: str = ""):
    """Record a metric in the global monitoring system"""
    monitoring_system.record_metric(name, value, metric_type, labels, unit)

def record_response_time(endpoint: str, duration_ms: float, status_code: int = 200):
    """Record API response time"""
    record_metric(
        "api_response_time",
        duration_ms,
        MetricType.HISTOGRAM,
        {"endpoint": endpoint, "status_code": str(status_code)},
        "ms"
    )

def record_error(error_type: str, endpoint: str = None):
    """Record an error occurrence"""
    labels = {"error_type": error_type}
    if endpoint:
        labels["endpoint"] = endpoint
    
    record_metric("error_count", 1, MetricType.COUNTER, labels)

def record_user_action(action: str, user_type: str = "unknown"):
    """Record a user action"""
    record_metric(
        "user_actions",
        1,
        MetricType.COUNTER,
        {"action": action, "user_type": user_type}
    )

def record_cache_hit(cache_type: str, hit: bool):
    """Record cache hit/miss"""
    record_metric(
        "cache_operations",
        1,
        MetricType.COUNTER,
        {"cache_type": cache_type, "result": "hit" if hit else "miss"}
    )

def record_database_operation(operation: str, duration_ms: float, success: bool = True):
    """Record database operation"""
    record_metric(
        "database_operation_time",
        duration_ms,
        MetricType.HISTOGRAM,
        {"operation": operation, "success": str(success)},
        "ms"
    )

# Alert handlers

async def log_alert_handler(alert: Alert):
    """Log alert to application logs"""
    log_level = {
        AlertLevel.INFO: logger.info,
        AlertLevel.WARNING: logger.warning,
        AlertLevel.ERROR: logger.error,
        AlertLevel.CRITICAL: logger.critical
    }.get(alert.level, logger.info)
    
    log_level(
        f"ALERT: {alert.title}",
        extra={
            "alert_id": alert.id,
            "alert_level": alert.level,
            "alert_message": alert.message,
            "alert_source": alert.source,
            "alert_details": alert.details
        }
    )

# Add default alert handler
monitoring_system.add_alert_handler(log_alert_handler)