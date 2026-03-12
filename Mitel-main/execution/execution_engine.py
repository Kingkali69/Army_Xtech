"""
GhostAI Execution Engine (Window 3)
Manages tool execution, monitoring, and real-time progress tracking.
"""

import asyncio
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue
import threading


class ExecutionStatus(Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of tool execution."""
    step_id: str
    tool_id: str
    status: ExecutionStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    findings: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class JobStatus:
    """Status of execution job."""
    job_id: str
    engagement_id: str
    status: ExecutionStatus
    current_step: Optional[str] = None
    completed_steps: int = 0
    total_steps: int = 0
    progress_percent: float = 0.0
    results: List[ExecutionResult] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None


class ExecutionEngine:
    """Engine for executing security tools."""

    def __init__(self, max_concurrent_jobs: int = 5):
        """Initialize execution engine.

        Args:
            max_concurrent_jobs: Maximum number of concurrent jobs
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        self.active_jobs: Dict[str, JobStatus] = {}
        self.job_history: List[JobStatus] = []
        self.output_listeners: Dict[str, List[Callable]] = {}
        self.lock = threading.Lock()

    def execute_plan(self, plan: Any, target: Any,
                    engagement_id: str,
                    progress_callback: Optional[Callable] = None) -> str:
        """Execute an execution plan.

        Args:
            plan: ExecutionPlan object
            target: Target object
            engagement_id: Engagement ID
            progress_callback: Optional callback for progress updates

        Returns:
            Job ID
        """
        job_id = f"job_{int(time.time())}_{engagement_id}"

        # Create job status
        job = JobStatus(
            job_id=job_id,
            engagement_id=engagement_id,
            status=ExecutionStatus.PENDING,
            total_steps=len(plan.steps),
            start_time=time.time()
        )

        with self.lock:
            self.active_jobs[job_id] = job

        # Register progress callback
        if progress_callback:
            self.add_output_listener(job_id, progress_callback)

        # Start execution in background thread
        thread = threading.Thread(
            target=self._execute_plan_thread,
            args=(job_id, plan, target),
            daemon=True
        )
        thread.start()

        return job_id

    def _execute_plan_thread(self, job_id: str, plan: Any, target: Any):
        """Execute plan in background thread.

        Args:
            job_id: Job ID
            plan: ExecutionPlan object
            target: Target object
        """
        try:
            with self.lock:
                job = self.active_jobs[job_id]
                job.status = ExecutionStatus.RUNNING

            # Execute each step
            for step in plan.steps:
                # Check if job was cancelled
                with self.lock:
                    if job.status == ExecutionStatus.CANCELLED:
                        break

                # Update current step
                with self.lock:
                    job.current_step = step.step_id

                # Notify listeners
                self._notify_listeners(job_id, {
                    'type': 'step_start',
                    'step_id': step.step_id,
                    'tool_name': step.tool.tool_name
                })

                # Check dependencies
                if not self._check_dependencies(job, step):
                    # Skip if dependencies failed
                    result = ExecutionResult(
                        step_id=step.step_id,
                        tool_id=step.tool.tool_id,
                        status=ExecutionStatus.FAILED,
                        start_time=time.time(),
                        end_time=time.time(),
                        duration=0.0,
                        error="Dependency check failed"
                    )
                    with self.lock:
                        job.results.append(result)
                    continue

                # Execute step
                result = self._execute_step(step, target, job_id)

                # Store result
                with self.lock:
                    job.results.append(result)
                    job.completed_steps += 1
                    job.progress_percent = (job.completed_steps / job.total_steps) * 100

                # Notify listeners
                self._notify_listeners(job_id, {
                    'type': 'step_complete',
                    'step_id': step.step_id,
                    'status': result.status.value,
                    'duration': result.duration
                })

                # Check if step failed and has no alternatives
                if result.status == ExecutionStatus.FAILED:
                    # For now, continue with next step
                    # In production, might want to abort or retry
                    pass

            # Mark job as complete
            with self.lock:
                job.end_time = time.time()
                # Determine overall status
                failed_steps = sum(1 for r in job.results if r.status == ExecutionStatus.FAILED)
                if failed_steps == 0:
                    job.status = ExecutionStatus.SUCCESS
                elif failed_steps == len(job.results):
                    job.status = ExecutionStatus.FAILED
                else:
                    # Partial success
                    job.status = ExecutionStatus.SUCCESS

            # Notify listeners
            self._notify_listeners(job_id, {
                'type': 'job_complete',
                'status': job.status.value,
                'duration': job.end_time - job.start_time
            })

        except Exception as e:
            # Handle unexpected errors
            with self.lock:
                job.status = ExecutionStatus.FAILED
                job.error = str(e)
                job.end_time = time.time()

            self._notify_listeners(job_id, {
                'type': 'job_error',
                'error': str(e)
            })

        finally:
            # Move to history
            with self.lock:
                if job_id in self.active_jobs:
                    completed_job = self.active_jobs.pop(job_id)
                    self.job_history.append(completed_job)

    def _check_dependencies(self, job: JobStatus, step: Any) -> bool:
        """Check if step dependencies are satisfied.

        Args:
            job: Job status
            step: ToolStep object

        Returns:
            True if dependencies satisfied, False otherwise
        """
        if not step.depends_on:
            return True

        # Check if all dependencies succeeded
        for dep_step_id in step.depends_on:
            dep_result = None
            for result in job.results:
                if result.step_id == dep_step_id:
                    dep_result = result
                    break

            if not dep_result or dep_result.status != ExecutionStatus.SUCCESS:
                return False

        return True

    def _execute_step(self, step: Any, target: Any, job_id: str) -> ExecutionResult:
        """Execute a single tool step.

        Args:
            step: ToolStep object
            target: Target object
            job_id: Job ID

        Returns:
            ExecutionResult object
        """
        start_time = time.time()

        try:
            # Simulate tool execution
            # In production, this would call actual security tools
            output, exit_code, findings = self._run_tool(
                step.tool.tool_id,
                target,
                step.parameters,
                step.tool.timeout
            )

            end_time = time.time()
            duration = end_time - start_time

            # Determine status
            if exit_code == 0:
                status = ExecutionStatus.SUCCESS
            elif exit_code == 124:  # Timeout exit code
                status = ExecutionStatus.TIMEOUT
            else:
                status = ExecutionStatus.FAILED

            return ExecutionResult(
                step_id=step.step_id,
                tool_id=step.tool.tool_id,
                status=status,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                output=output,
                exit_code=exit_code,
                findings=findings
            )

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            return ExecutionResult(
                step_id=step.step_id,
                tool_id=step.tool.tool_id,
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                error=str(e)
            )

    def _run_tool(self, tool_id: str, target: Any,
                 parameters: Dict[str, Any],
                 timeout: int) -> tuple[str, int, List[Dict[str, Any]]]:
        """Run actual security tool.

        Args:
            tool_id: Tool ID
            target: Target object
            parameters: Tool parameters
            timeout: Execution timeout in seconds

        Returns:
            Tuple of (output, exit_code, findings)
        """
        # This is a simulation - in production, would execute actual tools
        # based on tool_id and parameters

        # Simulate execution time
        time.sleep(min(2.0, timeout / 100))

        # Simulate different tool outputs
        findings = []

        if tool_id == 'nmap':
            output = f"Nmap scan report for {target.value}\n"
            output += "PORT     STATE SERVICE\n"
            output += "22/tcp   open  ssh\n"
            output += "80/tcp   open  http\n"
            output += "443/tcp  open  https\n"

            findings = [
                {'port': 22, 'service': 'ssh', 'state': 'open'},
                {'port': 80, 'service': 'http', 'state': 'open'},
                {'port': 443, 'service': 'https', 'state': 'open'}
            ]

        elif tool_id == 'nessus':
            output = "Vulnerability scan completed\n"
            output += "Found 3 vulnerabilities:\n"
            output += "- CVE-2024-1234 (High)\n"
            output += "- CVE-2024-5678 (Medium)\n"
            output += "- CVE-2024-9012 (Low)\n"

            findings = [
                {'cve': 'CVE-2024-1234', 'severity': 'high'},
                {'cve': 'CVE-2024-5678', 'severity': 'medium'},
                {'cve': 'CVE-2024-9012', 'severity': 'low'}
            ]

        elif tool_id == 'metasploit':
            output = "Exploitation attempt completed\n"
            output += "Target exploited successfully\n"

            findings = [
                {'type': 'shell', 'access_level': 'user'}
            ]

        else:
            output = f"{tool_id} executed successfully\n"

        return output, 0, findings

    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status.

        Args:
            job_id: Job ID

        Returns:
            JobStatus object or None
        """
        with self.lock:
            # Check active jobs
            if job_id in self.active_jobs:
                return self.active_jobs[job_id]

            # Check history
            for job in self.job_history:
                if job.job_id == job_id:
                    return job

        return None

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled, False otherwise
        """
        with self.lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                if job.status == ExecutionStatus.RUNNING:
                    job.status = ExecutionStatus.CANCELLED
                    return True

        return False

    def add_output_listener(self, job_id: str, callback: Callable):
        """Add output listener for job.

        Args:
            job_id: Job ID
            callback: Callback function
        """
        if job_id not in self.output_listeners:
            self.output_listeners[job_id] = []
        self.output_listeners[job_id].append(callback)

    def _notify_listeners(self, job_id: str, event: Dict[str, Any]):
        """Notify all listeners for a job.

        Args:
            job_id: Job ID
            event: Event data
        """
        if job_id in self.output_listeners:
            for callback in self.output_listeners[job_id]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in listener callback: {e}")

    def get_active_jobs(self) -> List[JobStatus]:
        """Get all active jobs.

        Returns:
            List of JobStatus objects
        """
        with self.lock:
            return list(self.active_jobs.values())

    def get_job_history(self, limit: int = 100) -> List[JobStatus]:
        """Get job history.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of JobStatus objects
        """
        with self.lock:
            return self.job_history[-limit:]

    def get_real_time_output(self, job_id: str) -> List[str]:
        """Get real-time output for a job.

        Args:
            job_id: Job ID

        Returns:
            List of output lines
        """
        job = self.get_job_status(job_id)
        if not job:
            return []

        output_lines = []

        # Add header
        output_lines.append(f"Job: {job.job_id}")
        output_lines.append(f"Status: {job.status.value}")
        output_lines.append(f"Progress: {job.progress_percent:.1f}%")
        output_lines.append("")

        # Add results
        for result in job.results:
            output_lines.append(f"[{result.tool_id}] {result.status.value}")
            if result.output:
                output_lines.append(result.output)
            if result.error:
                output_lines.append(f"Error: {result.error}")
            output_lines.append("")

        return output_lines

    def retry_failed_steps(self, job_id: str) -> Optional[str]:
        """Retry failed steps in a job.

        Args:
            job_id: Job ID

        Returns:
            New job ID or None
        """
        # Get original job
        job = self.get_job_status(job_id)
        if not job:
            return None

        # Find failed steps
        failed_results = [r for r in job.results if r.status == ExecutionStatus.FAILED]
        if not failed_results:
            return None

        # Create new job for retry
        # This is a placeholder - in production would recreate the plan
        # with only failed steps

        return None

    def generate_report(self, job_id: str) -> Dict[str, Any]:
        """Generate execution report for a job.

        Args:
            job_id: Job ID

        Returns:
            Report dictionary
        """
        job = self.get_job_status(job_id)
        if not job:
            return {'error': 'Job not found'}

        # Aggregate findings
        all_findings = []
        for result in job.results:
            for finding in result.findings:
                finding['tool'] = result.tool_id
                all_findings.append(finding)

        # Calculate statistics
        total_duration = 0.0
        for result in job.results:
            if result.duration:
                total_duration += result.duration

        success_count = sum(1 for r in job.results if r.status == ExecutionStatus.SUCCESS)
        failed_count = sum(1 for r in job.results if r.status == ExecutionStatus.FAILED)

        return {
            'job_id': job.job_id,
            'engagement_id': job.engagement_id,
            'status': job.status.value,
            'start_time': datetime.fromtimestamp(job.start_time).isoformat() if job.start_time else None,
            'end_time': datetime.fromtimestamp(job.end_time).isoformat() if job.end_time else None,
            'total_duration': total_duration,
            'statistics': {
                'total_steps': job.total_steps,
                'completed_steps': job.completed_steps,
                'success_count': success_count,
                'failed_count': failed_count,
                'success_rate': (success_count / job.total_steps * 100) if job.total_steps > 0 else 0
            },
            'findings': all_findings,
            'results': [
                {
                    'step_id': r.step_id,
                    'tool_id': r.tool_id,
                    'status': r.status.value,
                    'duration': r.duration,
                    'findings_count': len(r.findings)
                }
                for r in job.results
            ]
        }


# Global execution engine instance
_execution_engine: Optional[ExecutionEngine] = None


def get_execution_engine() -> ExecutionEngine:
    """Get global execution engine instance.

    Returns:
        ExecutionEngine instance
    """
    global _execution_engine
    if _execution_engine is None:
        _execution_engine = ExecutionEngine()
    return _execution_engine
