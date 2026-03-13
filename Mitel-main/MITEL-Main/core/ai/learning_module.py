"""
GhostAI Learning Module (Window 4)
Learns from execution results and provides AI-powered recommendations.
"""

import json
import time
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import secrets


@dataclass
class ExecutionPattern:
    """Learned execution pattern."""
    pattern_id: str
    target_type: str
    target_os: str
    tool_chain: List[str]
    success_rate: float
    avg_execution_time: float
    avg_findings_count: float
    conditions: Dict[str, Any]
    sample_size: int
    last_updated: str


@dataclass
class Recommendation:
    """Tool recommendation."""
    recommendation_id: str
    tool_ids: List[str]
    confidence: float
    reasoning: str
    estimated_time: float
    estimated_success_rate: float
    source: str  # 'ai', 'rule_based', 'historical'


class LearningModule:
    """Module for learning from executions and making recommendations."""

    def __init__(self, use_ai: bool = True):
        """Initialize learning module.

        Args:
            use_ai: Whether to use AI for recommendations (fallback to rule-based if False)
        """
        self.use_ai = use_ai
        self.patterns: Dict[str, ExecutionPattern] = {}
        self.execution_history: List[Dict[str, Any]] = []

        # Rule-based patterns for fallback
        self.rule_based_patterns = self._initialize_rule_based_patterns()

    def _initialize_rule_based_patterns(self) -> Dict[str, List[str]]:
        """Initialize rule-based tool patterns.

        Returns:
            Dictionary of patterns
        """
        return {
            'windows_pentest': ['nmap', 'nessus', 'metasploit', 'mimikatz', 'report_gen'],
            'linux_pentest': ['nmap', 'nessus', 'metasploit', 'linpeas', 'report_gen'],
            'web_assessment': ['nmap', 'nikto', 'sqlmap', 'report_gen'],
            'vulnerability_scan': ['nmap', 'openvas', 'report_gen'],
            'network_recon': ['nmap', 'masscan', 'enum4linux', 'report_gen'],
            'quick_assessment': ['masscan', 'nessus', 'report_gen']
        }

    def learn_from_execution(self, engagement_data: Dict[str, Any],
                            execution_results: List[Any]) -> bool:
        """Learn from an execution.

        Args:
            engagement_data: Engagement metadata
            execution_results: List of ExecutionResult objects

        Returns:
            True if learning succeeded, False otherwise
        """
        try:
            # Extract key information
            target_type = engagement_data.get('target_type', 'unknown')
            target_os = engagement_data.get('target_os', 'unknown')

            # Extract tool chain
            tool_chain = [r.tool_id for r in execution_results]

            # Calculate metrics
            success_count = sum(1 for r in execution_results
                              if hasattr(r, 'status') and r.status.value == 'success')
            success_rate = success_count / len(execution_results) if execution_results else 0.0

            execution_times = [r.duration for r in execution_results
                             if hasattr(r, 'duration') and r.duration is not None]
            avg_execution_time = statistics.mean(execution_times) if execution_times else 0.0

            findings_counts = [len(r.findings) for r in execution_results
                             if hasattr(r, 'findings')]
            avg_findings_count = statistics.mean(findings_counts) if findings_counts else 0.0

            # Create or update pattern
            pattern_key = f"{target_type}_{target_os}_{'-'.join(tool_chain)}"

            if pattern_key in self.patterns:
                # Update existing pattern
                pattern = self.patterns[pattern_key]

                # Calculate running average
                old_weight = pattern.sample_size
                new_weight = 1
                total_weight = old_weight + new_weight

                pattern.success_rate = (
                    (pattern.success_rate * old_weight + success_rate * new_weight) / total_weight
                )
                pattern.avg_execution_time = (
                    (pattern.avg_execution_time * old_weight + avg_execution_time * new_weight) / total_weight
                )
                pattern.avg_findings_count = (
                    (pattern.avg_findings_count * old_weight + avg_findings_count * new_weight) / total_weight
                )

                pattern.sample_size += 1
                pattern.last_updated = datetime.now().isoformat()
            else:
                # Create new pattern
                pattern = ExecutionPattern(
                    pattern_id=secrets.token_hex(16),
                    target_type=target_type,
                    target_os=target_os,
                    tool_chain=tool_chain,
                    success_rate=success_rate,
                    avg_execution_time=avg_execution_time,
                    avg_findings_count=avg_findings_count,
                    conditions=engagement_data.get('conditions', {}),
                    sample_size=1,
                    last_updated=datetime.now().isoformat()
                )
                self.patterns[pattern_key] = pattern

            # Store in execution history
            self.execution_history.append({
                'timestamp': datetime.now().isoformat(),
                'target_type': target_type,
                'target_os': target_os,
                'tool_chain': tool_chain,
                'success_rate': success_rate,
                'execution_time': avg_execution_time,
                'findings_count': avg_findings_count
            })

            return True

        except Exception as e:
            print(f"Error learning from execution: {e}")
            return False

    def get_recommendations(self, target_type: str, target_os: str,
                          objectives: List[str],
                          use_ai: Optional[bool] = None) -> List[Recommendation]:
        """Get tool recommendations.

        Args:
            target_type: Target type
            target_os: Target OS
            objectives: List of objectives
            use_ai: Override default AI usage

        Returns:
            List of Recommendation objects
        """
        use_ai_inference = use_ai if use_ai is not None else self.use_ai

        recommendations = []

        # Try AI-based recommendations first
        if use_ai_inference:
            try:
                ai_recs = self._get_ai_recommendations(target_type, target_os, objectives)
                recommendations.extend(ai_recs)
            except Exception as e:
                print(f"AI recommendation failed: {e}")
                # Fall through to rule-based

        # If no AI recommendations, use rule-based
        if not recommendations:
            rule_recs = self._get_rule_based_recommendations(target_type, target_os, objectives)
            recommendations.extend(rule_recs)

        # Add historical recommendations
        hist_recs = self._get_historical_recommendations(target_type, target_os)
        recommendations.extend(hist_recs)

        # Sort by confidence
        recommendations.sort(key=lambda r: r.confidence, reverse=True)

        return recommendations

    def _get_ai_recommendations(self, target_type: str, target_os: str,
                               objectives: List[str]) -> List[Recommendation]:
        """Get AI-powered recommendations using Mistral.

        Args:
            target_type: Target type
            target_os: Target OS
            objectives: List of objectives

        Returns:
            List of Recommendation objects

        Raises:
            Exception: If AI inference fails
        """
        # This is a placeholder for actual Mistral AI integration
        # In production, would call Mistral API with context

        # Simulated AI recommendation
        # Would actually analyze patterns and make intelligent suggestions

        # For now, raise exception to trigger fallback
        raise Exception("Mistral AI not configured")

    def _get_rule_based_recommendations(self, target_type: str, target_os: str,
                                       objectives: List[str]) -> List[Recommendation]:
        """Get rule-based recommendations (fallback).

        Args:
            target_type: Target type
            target_os: Target OS
            objectives: List of objectives

        Returns:
            List of Recommendation objects
        """
        recommendations = []

        # Determine scenario based on OS and objectives
        scenario_key = None

        if target_os == 'windows':
            if any('pentest' in obj.lower() or 'penetration' in obj.lower() for obj in objectives):
                scenario_key = 'windows_pentest'
            elif any('vulnerability' in obj.lower() or 'scan' in obj.lower() for obj in objectives):
                scenario_key = 'vulnerability_scan'
        elif target_os == 'linux':
            if any('pentest' in obj.lower() or 'penetration' in obj.lower() for obj in objectives):
                scenario_key = 'linux_pentest'
            elif any('vulnerability' in obj.lower() or 'scan' in obj.lower() for obj in objectives):
                scenario_key = 'vulnerability_scan'

        # Check for web assessment
        if any('web' in obj.lower() or 'application' in obj.lower() for obj in objectives):
            scenario_key = 'web_assessment'

        # Check for quick assessment
        if any('quick' in obj.lower() or 'fast' in obj.lower() for obj in objectives):
            scenario_key = 'quick_assessment'

        # Default to network recon
        if scenario_key is None:
            scenario_key = 'network_recon'

        # Get tool chain for scenario
        tool_chain = self.rule_based_patterns.get(scenario_key, ['nmap', 'report_gen'])

        # Estimate time (rough estimate based on tool count)
        estimated_time = len(tool_chain) * 300  # 5 minutes per tool

        recommendation = Recommendation(
            recommendation_id=secrets.token_hex(8),
            tool_ids=tool_chain,
            confidence=0.7,  # Rule-based has moderate confidence
            reasoning=f"Rule-based recommendation for {scenario_key}",
            estimated_time=estimated_time,
            estimated_success_rate=0.8,  # Conservative estimate
            source='rule_based'
        )

        recommendations.append(recommendation)

        return recommendations

    def _get_historical_recommendations(self, target_type: str,
                                       target_os: str) -> List[Recommendation]:
        """Get recommendations based on historical data.

        Args:
            target_type: Target type
            target_os: Target OS

        Returns:
            List of Recommendation objects
        """
        recommendations = []

        # Find patterns matching target
        matching_patterns = [
            p for p in self.patterns.values()
            if p.target_type == target_type and p.target_os == target_os
        ]

        # Sort by success rate and sample size
        matching_patterns.sort(
            key=lambda p: (p.success_rate, p.sample_size),
            reverse=True
        )

        # Create recommendations from top patterns
        for pattern in matching_patterns[:3]:  # Top 3 patterns
            confidence = min(0.9, pattern.success_rate * (1 + min(pattern.sample_size / 10, 0.2)))

            recommendation = Recommendation(
                recommendation_id=secrets.token_hex(8),
                tool_ids=pattern.tool_chain,
                confidence=confidence,
                reasoning=f"Based on {pattern.sample_size} successful executions with {pattern.success_rate*100:.1f}% success rate",
                estimated_time=pattern.avg_execution_time,
                estimated_success_rate=pattern.success_rate,
                source='historical'
            )

            recommendations.append(recommendation)

        return recommendations

    def get_learned_patterns(self, target_type: Optional[str] = None,
                           min_success_rate: float = 0.0) -> List[ExecutionPattern]:
        """Get learned patterns.

        Args:
            target_type: Optional target type filter
            min_success_rate: Minimum success rate filter

        Returns:
            List of ExecutionPattern objects
        """
        patterns = list(self.patterns.values())

        if target_type:
            patterns = [p for p in patterns if p.target_type == target_type]

        if min_success_rate > 0:
            patterns = [p for p in patterns if p.success_rate >= min_success_rate]

        # Sort by success rate and sample size
        patterns.sort(key=lambda p: (p.success_rate, p.sample_size), reverse=True)

        return patterns

    def analyze_tool_effectiveness(self) -> Dict[str, Any]:
        """Analyze tool effectiveness across all executions.

        Returns:
            Dictionary with analysis results
        """
        tool_stats = defaultdict(lambda: {
            'usage_count': 0,
            'success_count': 0,
            'total_time': 0.0,
            'total_findings': 0
        })

        # Aggregate statistics
        for history_item in self.execution_history:
            tool_chain = history_item['tool_chain']
            success_rate = history_item['success_rate']
            exec_time = history_item['execution_time']
            findings = history_item['findings_count']

            for tool_id in tool_chain:
                stats = tool_stats[tool_id]
                stats['usage_count'] += 1
                stats['success_count'] += success_rate
                stats['total_time'] += exec_time / len(tool_chain)  # Distribute time
                stats['total_findings'] += findings / len(tool_chain)  # Distribute findings

        # Calculate averages
        results = {}
        for tool_id, stats in tool_stats.items():
            if stats['usage_count'] > 0:
                results[tool_id] = {
                    'usage_count': stats['usage_count'],
                    'success_rate': stats['success_count'] / stats['usage_count'],
                    'avg_execution_time': stats['total_time'] / stats['usage_count'],
                    'avg_findings': stats['total_findings'] / stats['usage_count']
                }

        return results

    def suggest_optimizations(self) -> List[Dict[str, Any]]:
        """Suggest optimizations based on learned patterns.

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # Analyze tool effectiveness
        tool_effectiveness = self.analyze_tool_effectiveness()

        # Find underperforming tools
        for tool_id, stats in tool_effectiveness.items():
            if stats['success_rate'] < 0.5 and stats['usage_count'] >= 3:
                suggestions.append({
                    'type': 'replace_tool',
                    'tool_id': tool_id,
                    'message': f"Tool '{tool_id}' has low success rate ({stats['success_rate']*100:.1f}%)",
                    'suggestion': "Consider using alternative tools"
                })

            if stats['avg_execution_time'] > 1000:  # More than ~16 minutes
                suggestions.append({
                    'type': 'optimize_tool',
                    'tool_id': tool_id,
                    'message': f"Tool '{tool_id}' has high execution time ({stats['avg_execution_time']:.0f}s)",
                    'suggestion': "Consider adjusting parameters or using faster alternatives"
                })

        # Find high-performing patterns
        high_performers = [
            p for p in self.patterns.values()
            if p.success_rate >= 0.8 and p.sample_size >= 3
        ]

        if high_performers:
            best_pattern = max(high_performers, key=lambda p: (p.success_rate, p.sample_size))
            suggestions.append({
                'type': 'use_pattern',
                'pattern_id': best_pattern.pattern_id,
                'message': f"Pattern for {best_pattern.target_type}/{best_pattern.target_os} has {best_pattern.success_rate*100:.1f}% success rate",
                'suggestion': f"Recommended tools: {', '.join(best_pattern.tool_chain)}"
            })

        return suggestions

    def export_patterns(self) -> str:
        """Export learned patterns to JSON.

        Returns:
            JSON string
        """
        patterns_data = []

        for pattern in self.patterns.values():
            patterns_data.append({
                'pattern_id': pattern.pattern_id,
                'target_type': pattern.target_type,
                'target_os': pattern.target_os,
                'tool_chain': pattern.tool_chain,
                'success_rate': pattern.success_rate,
                'avg_execution_time': pattern.avg_execution_time,
                'avg_findings_count': pattern.avg_findings_count,
                'conditions': pattern.conditions,
                'sample_size': pattern.sample_size,
                'last_updated': pattern.last_updated
            })

        return json.dumps(patterns_data, indent=2)

    def import_patterns(self, patterns_json: str) -> bool:
        """Import learned patterns from JSON.

        Args:
            patterns_json: JSON string with patterns

        Returns:
            True if successful, False otherwise
        """
        try:
            patterns_data = json.loads(patterns_json)

            for data in patterns_data:
                pattern = ExecutionPattern(
                    pattern_id=data['pattern_id'],
                    target_type=data['target_type'],
                    target_os=data['target_os'],
                    tool_chain=data['tool_chain'],
                    success_rate=data['success_rate'],
                    avg_execution_time=data['avg_execution_time'],
                    avg_findings_count=data['avg_findings_count'],
                    conditions=data['conditions'],
                    sample_size=data['sample_size'],
                    last_updated=data['last_updated']
                )

                pattern_key = f"{pattern.target_type}_{pattern.target_os}_{'-'.join(pattern.tool_chain)}"
                self.patterns[pattern_key] = pattern

            return True

        except Exception as e:
            print(f"Error importing patterns: {e}")
            return False


# Global learning module instance
_learning_module: Optional[LearningModule] = None


def get_learning_module() -> LearningModule:
    """Get global learning module instance.

    Returns:
        LearningModule instance
    """
    global _learning_module
    if _learning_module is None:
        _learning_module = LearningModule()
    return _learning_module
