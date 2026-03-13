"""
GhostAI Core Orchestrator
Main entry point that ties all GhostAI components together.
"""

import secrets
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import all GhostAI components
from contract_parser import ContractParser, ParsedContract
from tool_orchestrator import ToolOrchestrator, ExecutionPlan
from execution_engine import ExecutionEngine, JobStatus, ExecutionStatus
from learning_module import LearningModule
from database import GhostAIDatabase, Engagement, LearnedPattern, UserHistory
from error_handling import ErrorHandler, GhostAIError, ErrorCategory, ErrorSeverity
from security_layer import SecurityLayer, User
from performance_monitor import PerformanceMonitor


class GhostAI:
    """Main GhostAI orchestrator class."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize GhostAI orchestrator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

        # Initialize components
        self.contract_parser = ContractParser()
        self.tool_orchestrator = ToolOrchestrator()
        self.execution_engine = ExecutionEngine()
        self.learning_module = LearningModule()
        self.database = GhostAIDatabase()
        self.error_handler = ErrorHandler()
        self.security_layer = SecurityLayer()
        self.performance_monitor = PerformanceMonitor()

    def upload_contract(self, contract_path: str, user_token: str) -> Dict[str, Any]:
        """Upload and parse a contract.

        Args:
            contract_path: Path to contract file
            user_token: User authentication token

        Returns:
            Dictionary with parsed contract and recommendations
        """
        try:
            # Verify user authorization
            authorized, user = self.security_layer.authorize_action(user_token, 'upload_contract')
            if not authorized or not user:
                return self.error_handler.handle_unauthorized_access('upload_contract', 'unknown')

            # Parse contract (Window 1)
            try:
                parsed_contract = self.contract_parser.parse_file(contract_path)
            except Exception as e:
                return self.error_handler.handle_contract_parse_error(e, contract_path)

            # Validate contract
            is_valid, errors = self.contract_parser.validate_contract(parsed_contract)
            if not is_valid:
                return self.error_handler.handle_invalid_contract_format(errors)

            # Verify contract signature
            contract_data = {
                'contract_id': parsed_contract.contract_id,
                'authorized_by': parsed_contract.authorized_by,
                'signature': parsed_contract.signature or ''
            }
            is_verified, contract_obj = self.security_layer.verify_contract(contract_data)

            # Extract contract summary
            summary = self.contract_parser.extract_summary(parsed_contract)

            # Get tool recommendations for each target
            recommendations = []
            for target in parsed_contract.targets:
                target_recs = self.learning_module.get_recommendations(
                    target_type=target.target_type,
                    target_os=target.os_type or 'unknown',
                    objectives=parsed_contract.objectives
                )
                recommendations.extend(target_recs)

            # Create engagement in database
            engagement = Engagement(
                engagement_id=parsed_contract.contract_id,
                contract_data=summary,
                created_at=datetime.now().isoformat(),
                status='pending',
                targets=[t.value for t in parsed_contract.targets]
            )
            self.database.create_engagement(engagement)

            # Log user action
            history = UserHistory(
                history_id=secrets.token_hex(16),
                user_id=user.user_id,
                engagement_id=parsed_contract.contract_id,
                action='upload_contract',
                timestamp=datetime.now().isoformat(),
                details={'contract_name': parsed_contract.contract_name}
            )
            self.database.add_history(history)

            return {
                'success': True,
                'contract_id': parsed_contract.contract_id,
                'contract_name': parsed_contract.contract_name,
                'summary': summary,
                'recommendations': [
                    {
                        'tool_chain': rec.tool_ids,
                        'confidence': rec.confidence,
                        'reasoning': rec.reasoning,
                        'estimated_time': rec.estimated_time,
                        'source': rec.source
                    }
                    for rec in recommendations[:5]  # Top 5 recommendations
                ],
                'verified': is_verified
            }

        except Exception as e:
            return self.error_handler.handle_generic_error(e, 'upload_contract')

    def start_engagement(self, engagement_id: str, user_token: str,
                        selected_tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """Start a security engagement.

        Args:
            engagement_id: Engagement ID
            user_token: User authentication token
            selected_tools: Optional list of tools to use (uses recommendations if None)

        Returns:
            Dictionary with job status
        """
        try:
            # Verify user authorization
            authorized, user = self.security_layer.authorize_action(user_token, 'start_engagement')
            if not authorized or not user:
                return self.error_handler.handle_unauthorized_access('start_engagement', 'unknown')

            # Get engagement from database
            engagement = self.database.get_engagement(engagement_id)
            if not engagement:
                return {
                    'success': False,
                    'error': f'Engagement not found: {engagement_id}'
                }

            # Update engagement status
            self.database.update_engagement(engagement_id, {'status': 'in_progress'})

            # Start performance monitoring
            perf_metrics = self.performance_monitor.start_engagement(engagement_id)

            # Create execution plans for each target
            all_jobs = []

            for target_value in engagement.targets:
                # Determine target type and OS
                target_type = 'ip'  # Simplified for now
                target_os = 'unknown'  # Would be determined from contract or recon

                # Get contract objectives
                objectives = engagement.contract_data.get('objectives', [])

                # Create execution plan (Window 2)
                try:
                    plan = self.tool_orchestrator.create_execution_plan(
                        target_type=target_type,
                        target_os=target_os,
                        objectives=objectives,
                        tool_ids=selected_tools
                    )
                except Exception as e:
                    return self.error_handler.handle_tool_chain_error(e, selected_tools or [])

                # Create simple target object
                class SimpleTarget:
                    def __init__(self, value, os_type='unknown'):
                        self.value = value
                        self.os_type = os_type

                target = SimpleTarget(target_value, target_os)

                # Execute plan (Window 3)
                try:
                    job_id = self.execution_engine.execute_plan(
                        plan=plan,
                        target=target,
                        engagement_id=engagement_id,
                        progress_callback=lambda event: self._handle_progress_event(
                            engagement_id, event
                        )
                    )
                    all_jobs.append(job_id)
                except Exception as e:
                    return self.error_handler.handle_execution_failure('start_engagement', e)

            # Log user action
            history = UserHistory(
                history_id=secrets.token_hex(16),
                user_id=user.user_id,
                engagement_id=engagement_id,
                action='start_engagement',
                timestamp=datetime.now().isoformat(),
                details={'job_count': len(all_jobs)}
            )
            self.database.add_history(history)

            return {
                'success': True,
                'engagement_id': engagement_id,
                'job_ids': all_jobs,
                'status': 'running'
            }

        except Exception as e:
            return self.error_handler.handle_generic_error(e, 'start_engagement')

    def _handle_progress_event(self, engagement_id: str, event: Dict[str, Any]):
        """Handle progress event from execution engine.

        Args:
            engagement_id: Engagement ID
            event: Event data
        """
        # This would be called by the execution engine for real-time updates
        # Could be used to update UI, send notifications, etc.
        pass

    def get_status(self, engagement_id: str, user_token: str) -> Dict[str, Any]:
        """Get engagement status.

        Args:
            engagement_id: Engagement ID
            user_token: User authentication token

        Returns:
            Dictionary with status information
        """
        try:
            # Verify user authorization
            authorized, user = self.security_layer.authorize_action(user_token, 'view_status')
            if not authorized or not user:
                return self.error_handler.handle_unauthorized_access('view_status', 'unknown')

            # Get engagement from database
            engagement = self.database.get_engagement(engagement_id)
            if not engagement:
                return {
                    'success': False,
                    'error': f'Engagement not found: {engagement_id}'
                }

            # Get active jobs for this engagement
            active_jobs = [
                job for job in self.execution_engine.get_active_jobs()
                if job.engagement_id == engagement_id
            ]

            # Get job history
            job_history = [
                job for job in self.execution_engine.get_job_history()
                if job.engagement_id == engagement_id
            ]

            all_jobs = active_jobs + job_history

            # Calculate overall progress
            if all_jobs:
                total_progress = sum(job.progress_percent for job in all_jobs) / len(all_jobs)
            else:
                total_progress = 0.0

            # Get performance metrics
            perf_metrics = self.performance_monitor.get_engagement_stats()

            return {
                'success': True,
                'engagement_id': engagement_id,
                'status': engagement.status,
                'progress': total_progress,
                'active_jobs': len(active_jobs),
                'completed_jobs': len(job_history),
                'jobs': [
                    {
                        'job_id': job.job_id,
                        'status': job.status.value,
                        'progress': job.progress_percent,
                        'current_step': job.current_step
                    }
                    for job in all_jobs
                ],
                'performance': perf_metrics
            }

        except Exception as e:
            return self.error_handler.handle_generic_error(e, 'get_status')

    def get_report(self, engagement_id: str, user_token: str) -> Dict[str, Any]:
        """Get engagement report.

        Args:
            engagement_id: Engagement ID
            user_token: User authentication token

        Returns:
            Dictionary with report data
        """
        try:
            # Verify user authorization
            authorized, user = self.security_layer.authorize_action(user_token, 'view_report')
            if not authorized or not user:
                return self.error_handler.handle_unauthorized_access('view_report', 'unknown')

            # Get engagement from database
            engagement = self.database.get_engagement(engagement_id)
            if not engagement:
                return {
                    'success': False,
                    'error': f'Engagement not found: {engagement_id}'
                }

            # Get all jobs for this engagement
            all_jobs = [
                job for job in self.execution_engine.get_job_history()
                if job.engagement_id == engagement_id
            ]

            # Generate reports for each job
            job_reports = []
            for job in all_jobs:
                report = self.execution_engine.generate_report(job.job_id)
                job_reports.append(report)

            # Aggregate findings
            all_findings = []
            for report in job_reports:
                all_findings.extend(report.get('findings', []))

            # End performance monitoring
            perf_metrics = self.performance_monitor.end_engagement(engagement_id)

            # Create final report
            final_report = {
                'engagement_id': engagement_id,
                'contract_name': engagement.contract_data.get('contract_name'),
                'client_name': engagement.contract_data.get('client_name'),
                'generated_at': datetime.now().isoformat(),
                'executive_summary': {
                    'total_targets': len(engagement.targets),
                    'total_findings': len(all_findings),
                    'critical_findings': sum(1 for f in all_findings if f.get('severity') == 'critical'),
                    'high_findings': sum(1 for f in all_findings if f.get('severity') == 'high'),
                    'medium_findings': sum(1 for f in all_findings if f.get('severity') == 'medium'),
                    'low_findings': sum(1 for f in all_findings if f.get('severity') == 'low')
                },
                'findings': all_findings,
                'job_reports': job_reports,
                'performance': {
                    'total_time': perf_metrics.total_time if perf_metrics else 0,
                    'tools_executed': perf_metrics.tools_executed if perf_metrics else 0,
                    'tools_succeeded': perf_metrics.tools_succeeded if perf_metrics else 0,
                    'tools_failed': perf_metrics.tools_failed if perf_metrics else 0
                }
            }

            # Update engagement with results
            self.database.update_engagement(engagement_id, {
                'status': 'completed',
                'results': final_report,
                'execution_time': perf_metrics.total_time if perf_metrics else 0,
                'findings': all_findings
            })

            # Learn from execution (Window 4)
            for job in all_jobs:
                engagement_data = {
                    'target_type': 'ip',  # Simplified
                    'target_os': 'unknown',
                    'conditions': {}
                }
                self.learning_module.learn_from_execution(engagement_data, job.results)

            return {
                'success': True,
                'report': final_report
            }

        except Exception as e:
            return self.error_handler.handle_generic_error(e, 'get_report')

    def get_learned_patterns(self, user_token: str,
                           target_type: Optional[str] = None) -> Dict[str, Any]:
        """Get learned patterns.

        Args:
            user_token: User authentication token
            target_type: Optional target type filter

        Returns:
            Dictionary with learned patterns
        """
        try:
            # Verify user authorization
            authorized, user = self.security_layer.authorize_action(user_token, 'view_patterns')
            if not authorized or not user:
                return self.error_handler.handle_unauthorized_access('view_patterns', 'unknown')

            # Get patterns from learning module
            patterns = self.learning_module.get_learned_patterns(target_type=target_type)

            # Get patterns from database
            db_patterns = self.database.get_best_patterns(limit=10)

            # Get tool effectiveness analysis
            tool_effectiveness = self.learning_module.analyze_tool_effectiveness()

            # Get optimization suggestions
            optimizations = self.learning_module.suggest_optimizations()

            return {
                'success': True,
                'patterns': [
                    {
                        'pattern_id': p.pattern_id,
                        'target_type': p.target_type,
                        'target_os': p.target_os,
                        'tool_chain': p.tool_chain,
                        'success_rate': p.success_rate,
                        'avg_execution_time': p.avg_execution_time,
                        'sample_size': p.sample_size
                    }
                    for p in patterns
                ],
                'tool_effectiveness': tool_effectiveness,
                'optimizations': optimizations
            }

        except Exception as e:
            return self.error_handler.handle_generic_error(e, 'get_learned_patterns')

    def get_system_stats(self, user_token: str) -> Dict[str, Any]:
        """Get system statistics.

        Args:
            user_token: User authentication token

        Returns:
            Dictionary with system statistics
        """
        try:
            # Verify user authorization
            authorized, user = self.security_layer.authorize_action(user_token, 'view_status')
            if not authorized or not user:
                return self.error_handler.handle_unauthorized_access('view_status', 'unknown')

            # Get various statistics
            engagement_stats = self.database.get_engagement_stats()
            tool_performance = self.database.get_tool_performance()
            error_stats = self.error_handler.get_error_stats()
            security_stats = self.security_layer.get_security_stats()
            perf_stats = self.performance_monitor.get_engagement_stats()
            system_metrics = self.performance_monitor.get_system_metrics()
            performance_alerts = self.performance_monitor.get_alerts()

            return {
                'success': True,
                'engagement_stats': engagement_stats,
                'tool_performance': tool_performance,
                'error_stats': error_stats,
                'security_stats': security_stats,
                'performance_stats': perf_stats,
                'system_metrics': system_metrics,
                'alerts': [
                    {
                        'type': a.alert_type,
                        'severity': a.severity,
                        'message': a.message,
                        'timestamp': a.timestamp
                    }
                    for a in performance_alerts
                ]
            }

        except Exception as e:
            return self.error_handler.handle_generic_error(e, 'get_system_stats')


# Convenience function
def create_ghostai(config: Optional[Dict[str, Any]] = None) -> GhostAI:
    """Create GhostAI instance.

    Args:
        config: Optional configuration

    Returns:
        GhostAI instance
    """
    return GhostAI(config)
