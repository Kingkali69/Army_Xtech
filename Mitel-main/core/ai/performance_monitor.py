"""
GhostAI Performance Monitor
Tracks execution performance, resource usage, and provides optimization insights.
"""

import time
import psutil
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ToolMetrics:
    """Metrics for a single tool execution."""
    tool_name: str
    start_time: float
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    success: bool = False
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    error: Optional[str] = None


@dataclass
class EngagementMetrics:
    """Metrics for an entire engagement."""
    engagement_id: str
    start_time: float
    end_time: Optional[float] = None
    total_time: Optional[float] = None
    tools_executed: int = 0
    tools_succeeded: int = 0
    tools_failed: int = 0
    tool_metrics: List[ToolMetrics] = field(default_factory=list)
    avg_cpu_usage: Optional[float] = None
    avg_memory_usage: Optional[float] = None
    peak_memory: Optional[float] = None


@dataclass
class PerformanceAlert:
    """Performance alert."""
    alert_type: str  # 'slow_execution', 'high_resource', 'low_success_rate'
    severity: str  # 'info', 'warning', 'critical'
    message: str
    details: Dict[str, Any]
    timestamp: str


class PerformanceMonitor:
    """Performance monitoring and optimization system."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize performance monitor.

        Args:
            config: Optional configuration
        """
        self.config = config or {}

        # Performance thresholds
        self.slow_tool_threshold = self.config.get('slow_tool_threshold', 60.0)  # seconds
        self.slow_engagement_threshold = self.config.get('slow_engagement_threshold', 300.0)  # seconds
        self.high_cpu_threshold = self.config.get('high_cpu_threshold', 80.0)  # percent
        self.high_memory_threshold = self.config.get('high_memory_threshold', 80.0)  # percent
        self.low_success_rate_threshold = self.config.get('low_success_rate_threshold', 0.5)  # 50%

        # Tracking data
        self.active_engagements: Dict[str, EngagementMetrics] = {}
        self.completed_engagements: List[EngagementMetrics] = []
        self.tool_stats: Dict[str, List[ToolMetrics]] = defaultdict(list)
        self.alerts: List[PerformanceAlert] = []

        # System metrics
        self.process = psutil.Process()

    # Engagement tracking
    def start_engagement(self, engagement_id: str) -> EngagementMetrics:
        """Start tracking an engagement.

        Args:
            engagement_id: Engagement ID

        Returns:
            EngagementMetrics object
        """
        metrics = EngagementMetrics(
            engagement_id=engagement_id,
            start_time=time.time()
        )
        self.active_engagements[engagement_id] = metrics
        return metrics

    def end_engagement(self, engagement_id: str) -> Optional[EngagementMetrics]:
        """End tracking an engagement.

        Args:
            engagement_id: Engagement ID

        Returns:
            EngagementMetrics object or None
        """
        if engagement_id not in self.active_engagements:
            return None

        metrics = self.active_engagements[engagement_id]
        metrics.end_time = time.time()
        metrics.total_time = metrics.end_time - metrics.start_time

        # Calculate average resource usage
        if metrics.tool_metrics:
            cpu_values = [m.cpu_usage for m in metrics.tool_metrics if m.cpu_usage is not None]
            memory_values = [m.memory_usage for m in metrics.tool_metrics if m.memory_usage is not None]

            if cpu_values:
                metrics.avg_cpu_usage = statistics.mean(cpu_values)

            if memory_values:
                metrics.avg_memory_usage = statistics.mean(memory_values)
                metrics.peak_memory = max(memory_values)

        # Check for performance issues
        self._check_engagement_performance(metrics)

        # Move to completed
        del self.active_engagements[engagement_id]
        self.completed_engagements.append(metrics)

        return metrics

    # Tool tracking
    def start_tool(self, engagement_id: str, tool_name: str) -> Optional[ToolMetrics]:
        """Start tracking a tool execution.

        Args:
            engagement_id: Engagement ID
            tool_name: Tool name

        Returns:
            ToolMetrics object or None
        """
        if engagement_id not in self.active_engagements:
            return None

        metrics = ToolMetrics(
            tool_name=tool_name,
            start_time=time.time()
        )

        engagement = self.active_engagements[engagement_id]
        engagement.tool_metrics.append(metrics)
        engagement.tools_executed += 1

        return metrics

    def end_tool(self, engagement_id: str, tool_name: str, success: bool,
                error: Optional[str] = None) -> Optional[ToolMetrics]:
        """End tracking a tool execution.

        Args:
            engagement_id: Engagement ID
            tool_name: Tool name
            success: Whether execution succeeded
            error: Optional error message

        Returns:
            ToolMetrics object or None
        """
        if engagement_id not in self.active_engagements:
            return None

        engagement = self.active_engagements[engagement_id]

        # Find the most recent matching tool metric
        tool_metric = None
        for metric in reversed(engagement.tool_metrics):
            if metric.tool_name == tool_name and metric.end_time is None:
                tool_metric = metric
                break

        if not tool_metric:
            return None

        # Update metrics
        tool_metric.end_time = time.time()
        tool_metric.execution_time = tool_metric.end_time - tool_metric.start_time
        tool_metric.success = success
        tool_metric.error = error

        # Capture resource usage
        try:
            tool_metric.cpu_usage = self.process.cpu_percent(interval=0.1)
            tool_metric.memory_usage = self.process.memory_percent()
        except:
            pass

        # Update engagement counters
        if success:
            engagement.tools_succeeded += 1
        else:
            engagement.tools_failed += 1

        # Store in tool stats
        self.tool_stats[tool_name].append(tool_metric)

        # Check for performance issues
        self._check_tool_performance(tool_metric)

        return tool_metric

    # Performance analysis
    def _check_tool_performance(self, metrics: ToolMetrics):
        """Check tool performance and generate alerts.

        Args:
            metrics: Tool metrics to check
        """
        # Check execution time
        if metrics.execution_time and metrics.execution_time > self.slow_tool_threshold:
            self._add_alert(
                alert_type='slow_execution',
                severity='warning',
                message=f"Tool '{metrics.tool_name}' took {metrics.execution_time:.2f}s to execute",
                details={
                    'tool_name': metrics.tool_name,
                    'execution_time': metrics.execution_time,
                    'threshold': self.slow_tool_threshold
                }
            )

        # Check CPU usage
        if metrics.cpu_usage and metrics.cpu_usage > self.high_cpu_threshold:
            self._add_alert(
                alert_type='high_resource',
                severity='warning',
                message=f"Tool '{metrics.tool_name}' used {metrics.cpu_usage:.1f}% CPU",
                details={
                    'tool_name': metrics.tool_name,
                    'cpu_usage': metrics.cpu_usage,
                    'threshold': self.high_cpu_threshold
                }
            )

        # Check memory usage
        if metrics.memory_usage and metrics.memory_usage > self.high_memory_threshold:
            self._add_alert(
                alert_type='high_resource',
                severity='warning',
                message=f"Tool '{metrics.tool_name}' used {metrics.memory_usage:.1f}% memory",
                details={
                    'tool_name': metrics.tool_name,
                    'memory_usage': metrics.memory_usage,
                    'threshold': self.high_memory_threshold
                }
            )

    def _check_engagement_performance(self, metrics: EngagementMetrics):
        """Check engagement performance and generate alerts.

        Args:
            metrics: Engagement metrics to check
        """
        # Check total execution time
        if metrics.total_time and metrics.total_time > self.slow_engagement_threshold:
            self._add_alert(
                alert_type='slow_execution',
                severity='info',
                message=f"Engagement took {metrics.total_time:.2f}s to complete",
                details={
                    'engagement_id': metrics.engagement_id,
                    'total_time': metrics.total_time,
                    'threshold': self.slow_engagement_threshold
                }
            )

        # Check success rate
        if metrics.tools_executed > 0:
            success_rate = metrics.tools_succeeded / metrics.tools_executed
            if success_rate < self.low_success_rate_threshold:
                self._add_alert(
                    alert_type='low_success_rate',
                    severity='warning',
                    message=f"Low success rate: {success_rate*100:.1f}% ({metrics.tools_succeeded}/{metrics.tools_executed})",
                    details={
                        'engagement_id': metrics.engagement_id,
                        'success_rate': success_rate,
                        'tools_succeeded': metrics.tools_succeeded,
                        'tools_failed': metrics.tools_failed,
                        'threshold': self.low_success_rate_threshold
                    }
                )

        # Check peak memory
        if metrics.peak_memory and metrics.peak_memory > self.high_memory_threshold:
            self._add_alert(
                alert_type='high_resource',
                severity='warning',
                message=f"Peak memory usage: {metrics.peak_memory:.1f}%",
                details={
                    'engagement_id': metrics.engagement_id,
                    'peak_memory': metrics.peak_memory,
                    'threshold': self.high_memory_threshold
                }
            )

    def _add_alert(self, alert_type: str, severity: str, message: str, details: Dict[str, Any]):
        """Add a performance alert.

        Args:
            alert_type: Type of alert
            severity: Severity level
            message: Alert message
            details: Alert details
        """
        alert = PerformanceAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat()
        )
        self.alerts.append(alert)

    # Statistics
    def get_tool_stats(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Get tool performance statistics.

        Args:
            tool_name: Optional tool name filter

        Returns:
            Dictionary with statistics
        """
        if tool_name:
            tools_to_analyze = {tool_name: self.tool_stats.get(tool_name, [])}
        else:
            tools_to_analyze = dict(self.tool_stats)

        stats = {}

        for tool, metrics_list in tools_to_analyze.items():
            if not metrics_list:
                continue

            execution_times = [m.execution_time for m in metrics_list if m.execution_time is not None]
            successes = sum(1 for m in metrics_list if m.success)
            failures = len(metrics_list) - successes

            tool_stats = {
                'total_executions': len(metrics_list),
                'successes': successes,
                'failures': failures,
                'success_rate': successes / len(metrics_list) if metrics_list else 0.0
            }

            if execution_times:
                tool_stats.update({
                    'avg_execution_time': statistics.mean(execution_times),
                    'min_execution_time': min(execution_times),
                    'max_execution_time': max(execution_times),
                    'median_execution_time': statistics.median(execution_times)
                })

            stats[tool] = tool_stats

        return stats

    def get_engagement_stats(self) -> Dict[str, Any]:
        """Get engagement statistics.

        Returns:
            Dictionary with statistics
        """
        all_engagements = self.completed_engagements + list(self.active_engagements.values())

        if not all_engagements:
            return {
                'total_engagements': 0,
                'active_engagements': 0,
                'completed_engagements': 0
            }

        completed = [e for e in all_engagements if e.end_time is not None]
        total_times = [e.total_time for e in completed if e.total_time is not None]

        stats = {
            'total_engagements': len(all_engagements),
            'active_engagements': len(self.active_engagements),
            'completed_engagements': len(self.completed_engagements)
        }

        if total_times:
            stats.update({
                'avg_engagement_time': statistics.mean(total_times),
                'min_engagement_time': min(total_times),
                'max_engagement_time': max(total_times),
                'median_engagement_time': statistics.median(total_times)
            })

        # Overall success rate
        total_tools = sum(e.tools_executed for e in all_engagements)
        total_successes = sum(e.tools_succeeded for e in all_engagements)

        if total_tools > 0:
            stats['overall_success_rate'] = total_successes / total_tools

        return stats

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics.

        Returns:
            Dictionary with system metrics
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'memory_total_mb': memory.total / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'disk_total_gb': disk.total / (1024 * 1024 * 1024)
            }
        except Exception as e:
            return {'error': str(e)}

    def get_alerts(self, severity: Optional[str] = None, limit: int = 100) -> List[PerformanceAlert]:
        """Get performance alerts.

        Args:
            severity: Optional severity filter
            limit: Maximum number of alerts

        Returns:
            List of alerts
        """
        alerts = self.alerts

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts[-limit:]

    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts = []

    # Optimization recommendations
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on performance data.

        Returns:
            List of recommendations
        """
        recommendations = []

        # Analyze tool performance
        tool_stats = self.get_tool_stats()

        for tool_name, stats in tool_stats.items():
            # Recommend alternatives for slow tools
            if stats.get('avg_execution_time', 0) > self.slow_tool_threshold:
                recommendations.append({
                    'type': 'slow_tool',
                    'priority': 'medium',
                    'tool': tool_name,
                    'message': f"Tool '{tool_name}' is slow (avg: {stats['avg_execution_time']:.2f}s)",
                    'suggestion': "Consider using a faster alternative or optimizing parameters"
                })

            # Recommend avoiding unreliable tools
            if stats.get('success_rate', 1.0) < self.low_success_rate_threshold:
                recommendations.append({
                    'type': 'unreliable_tool',
                    'priority': 'high',
                    'tool': tool_name,
                    'message': f"Tool '{tool_name}' has low success rate ({stats['success_rate']*100:.1f}%)",
                    'suggestion': "Consider using a more reliable alternative or fixing configuration"
                })

        # Analyze resource usage
        system_metrics = self.get_system_metrics()

        if system_metrics.get('memory_percent', 0) > self.high_memory_threshold:
            recommendations.append({
                'type': 'high_memory',
                'priority': 'high',
                'message': f"High memory usage ({system_metrics['memory_percent']:.1f}%)",
                'suggestion': "Consider running fewer parallel tools or increasing system memory"
            })

        if system_metrics.get('cpu_percent', 0) > self.high_cpu_threshold:
            recommendations.append({
                'type': 'high_cpu',
                'priority': 'medium',
                'message': f"High CPU usage ({system_metrics['cpu_percent']:.1f}%)",
                'suggestion': "Consider adjusting tool concurrency or scheduling"
            })

        # Analyze engagement patterns
        engagement_stats = self.get_engagement_stats()

        if engagement_stats.get('overall_success_rate', 1.0) < self.low_success_rate_threshold:
            recommendations.append({
                'type': 'low_overall_success',
                'priority': 'high',
                'message': f"Overall success rate is low ({engagement_stats['overall_success_rate']*100:.1f}%)",
                'suggestion': "Review tool configurations and target compatibility"
            })

        return recommendations

    def get_fastest_path(self, target_type: str) -> Optional[List[str]]:
        """Get fastest tool path for a target type based on historical data.

        Args:
            target_type: Target type

        Returns:
            List of tool names or None
        """
        # This would analyze historical data to find the fastest successful path
        # For now, return None as placeholder
        # In production, this would query the database for patterns
        return None


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance.

    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
