"""
GhostAI Tool Orchestrator (Window 2)
Manages tool selection, chaining, dependency resolution, and execution planning.
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import re


class ExecutionMode(Enum):
    """Tool execution mode."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass
class ToolDefinition:
    """Definition of a security tool."""
    tool_id: str
    tool_name: str
    category: str  # 'recon', 'scan', 'exploit', 'post_exploit', 'report'
    requires_os: Optional[List[str]] = None  # ['windows', 'linux', 'any']
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300  # seconds
    retry_count: int = 2
    description: str = ""


@dataclass
class ToolStep:
    """Single step in execution plan."""
    step_id: str
    tool: ToolDefinition
    parameters: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    condition: Optional[str] = None  # e.g., "if_previous_success", "if_port_open"


@dataclass
class ExecutionPlan:
    """Complete tool execution plan."""
    plan_id: str
    target_type: str
    target_os: str
    steps: List[ToolStep]
    total_estimated_time: int  # seconds
    risk_level: str  # 'low', 'medium', 'high'
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolOrchestrator:
    """Orchestrates tool selection and execution planning."""

    def __init__(self):
        """Initialize tool orchestrator."""
        self.tools = self._initialize_tools()
        self.tool_chains = self._initialize_tool_chains()

    def _initialize_tools(self) -> Dict[str, ToolDefinition]:
        """Initialize available security tools.

        Returns:
            Dictionary of tool definitions
        """
        tools = {}

        # Reconnaissance tools
        tools['nmap'] = ToolDefinition(
            tool_id='nmap',
            tool_name='Nmap',
            category='recon',
            requires_os=['any'],
            parameters={'scan_type': 'full', 'service_detection': True},
            timeout=30,
            description='Network discovery and port scanning'
        )

        tools['masscan'] = ToolDefinition(
            tool_id='masscan',
            tool_name='Masscan',
            category='recon',
            requires_os=['any'],
            parameters={'scan_rate': 10000},
            timeout=300,
            description='Fast port scanner'
        )

        tools['enum4linux'] = ToolDefinition(
            tool_id='enum4linux',
            tool_name='Enum4Linux',
            category='recon',
            requires_os=['linux'],
            dependencies=['nmap'],
            timeout=300,
            description='SMB enumeration for Linux targets'
        )

        # Vulnerability scanning tools
        tools['nessus'] = ToolDefinition(
            tool_id='nessus',
            tool_name='Nessus',
            category='scan',
            requires_os=['any'],
            dependencies=['nmap'],
            timeout=1800,
            description='Comprehensive vulnerability scanner'
        )

        tools['openvas'] = ToolDefinition(
            tool_id='openvas',
            tool_name='OpenVAS',
            category='scan',
            requires_os=['any'],
            dependencies=['nmap'],
            timeout=1800,
            description='Open-source vulnerability scanner'
        )

        tools['nikto'] = ToolDefinition(
            tool_id='nikto',
            tool_name='Nikto',
            category='scan',
            requires_os=['any'],
            dependencies=['nmap'],
            timeout=900,
            description='Web server vulnerability scanner'
        )

        # Exploitation tools
        tools['metasploit'] = ToolDefinition(
            tool_id='metasploit',
            tool_name='Metasploit',
            category='exploit',
            requires_os=['any'],
            dependencies=['nmap', 'nessus'],
            timeout=30,
            description='Exploitation framework'
        )

        tools['sqlmap'] = ToolDefinition(
            tool_id='sqlmap',
            tool_name='SQLMap',
            category='exploit',
            requires_os=['any'],
            dependencies=['nikto'],
            timeout=900,
            description='SQL injection tool'
        )

        # Post-exploitation tools
        tools['mimikatz'] = ToolDefinition(
            tool_id='mimikatz',
            tool_name='Mimikatz',
            category='post_exploit',
            requires_os=['windows'],
            dependencies=['metasploit'],
            timeout=300,
            description='Windows credential extraction'
        )

        tools['linpeas'] = ToolDefinition(
            tool_id='linpeas',
            tool_name='LinPEAS',
            category='post_exploit',
            requires_os=['linux'],
            dependencies=['metasploit'],
            timeout=300,
            description='Linux privilege escalation scanner'
        )

        # Reporting tools
        tools['report_gen'] = ToolDefinition(
            tool_id='report_gen',
            tool_name='Report Generator',
            category='report',
            requires_os=['any'],
            timeout=60,
            description='Generate final report'
        )

        return tools

    def _initialize_tool_chains(self) -> Dict[str, List[str]]:
        """Initialize predefined tool chains for different scenarios.

        Returns:
            Dictionary of tool chain templates
        """
        return {
            'basic_recon': ['nmap', 'enum4linux'],
            'full_pentest_windows': ['nmap', 'nessus', 'metasploit', 'mimikatz', 'report_gen'],
            'full_pentest_linux': ['nmap', 'nessus', 'metasploit', 'linpeas', 'report_gen'],
            'web_assessment': ['nmap', 'nikto', 'sqlmap', 'report_gen'],
            'vulnerability_scan': ['nmap', 'openvas', 'report_gen'],
            'quick_scan': ['masscan', 'report_gen']
        }

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get tool definition by ID.

        Args:
            tool_id: Tool ID

        Returns:
            ToolDefinition or None
        """
        return self.tools.get(tool_id)

    def list_tools(self, category: Optional[str] = None,
                  os_type: Optional[str] = None) -> List[ToolDefinition]:
        """List available tools with optional filters.

        Args:
            category: Optional category filter
            os_type: Optional OS type filter

        Returns:
            List of ToolDefinition objects
        """
        tools = list(self.tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if os_type:
            tools = [t for t in tools if not t.requires_os or
                    os_type in t.requires_os or 'any' in t.requires_os]

        return tools

    def recommend_tools(self, target_type: str, target_os: str,
                       objectives: List[str]) -> List[str]:
        """Recommend tools based on target and objectives.

        Args:
            target_type: Target type ('ip', 'domain', 'network')
            target_os: Target OS ('windows', 'linux', 'unknown')
            objectives: List of engagement objectives

        Returns:
            List of recommended tool IDs
        """
        recommended = []

        # Always start with reconnaissance
        recommended.append('nmap')

        # Add OS-specific enumeration
        if target_os == 'linux' or target_os == 'unknown':
            recommended.append('enum4linux')

        # Check objectives
        for objective in objectives:
            obj_lower = objective.lower()

            if 'vulnerability' in obj_lower or 'scan' in obj_lower:
                recommended.append('nessus')

            if 'web' in obj_lower or 'application' in obj_lower:
                recommended.append('nikto')
                recommended.append('sqlmap')

            if 'exploit' in obj_lower or 'penetration' in obj_lower:
                recommended.append('metasploit')

                # Add post-exploitation based on OS
                if target_os == 'windows':
                    recommended.append('mimikatz')
                elif target_os == 'linux':
                    recommended.append('linpeas')

        # Always add reporting
        recommended.append('report_gen')

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for tool_id in recommended:
            if tool_id not in seen:
                seen.add(tool_id)
                result.append(tool_id)

        return result

    def create_execution_plan(self, target_type: str, target_os: str,
                             objectives: List[str],
                             tool_ids: Optional[List[str]] = None,
                             scope_restrictions: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """Create execution plan for tools.

        Args:
            target_type: Target type
            target_os: Target OS
            objectives: List of objectives
            tool_ids: Optional list of specific tool IDs to use
            scope_restrictions: Optional scope restrictions (forbidden tools, etc.)

        Returns:
            ExecutionPlan object

        Raises:
            ValueError: If plan cannot be created
        """
        # Get tools to use
        if tool_ids is None:
            tool_ids = self.recommend_tools(target_type, target_os, objectives)

        # Apply scope restrictions
        if scope_restrictions:
            tool_ids = self._apply_scope_restrictions(tool_ids, scope_restrictions)

        # Resolve dependencies
        tool_ids = self._resolve_dependencies(tool_ids)

        # Validate tools
        missing_tools = [tid for tid in tool_ids if tid not in self.tools]
        if missing_tools:
            raise ValueError(f"Unknown tools: {', '.join(missing_tools)}")

        # Create execution steps
        steps = self._create_execution_steps(tool_ids, target_os)

        # Calculate estimated time
        total_time = sum(step.tool.timeout for step in steps)

        # Determine risk level
        risk_level = self._calculate_risk_level(steps)

        # Create plan
        plan = ExecutionPlan(
            plan_id=f"plan_{int(time.time())}",
            target_type=target_type,
            target_os=target_os,
            steps=steps,
            total_estimated_time=total_time,
            risk_level=risk_level,
            metadata={
                'objectives': objectives,
                'tool_count': len(steps)
            }
        )

        return plan

    def _apply_scope_restrictions(self, tool_ids: List[str],
                                  restrictions: Dict[str, Any]) -> List[str]:
        """Apply scope restrictions to tool list.

        Args:
            tool_ids: List of tool IDs
            restrictions: Scope restrictions

        Returns:
            Filtered list of tool IDs
        """
        forbidden_tools = restrictions.get('forbidden_tools', [])
        allowed_tools = restrictions.get('allowed_tools')

        # Remove forbidden tools
        filtered = [tid for tid in tool_ids if tid not in forbidden_tools]

        # If allowed_tools is specified, only keep those
        if allowed_tools:
            filtered = [tid for tid in filtered if tid in allowed_tools]

        return filtered

    def _resolve_dependencies(self, tool_ids: List[str]) -> List[str]:
        """Resolve tool dependencies and return ordered list.

        Args:
            tool_ids: List of requested tool IDs

        Returns:
            Ordered list with dependencies resolved
        """
        resolved = []
        visited = set()

        def resolve_tool(tool_id: str):
            if tool_id in visited:
                return
            visited.add(tool_id)

            tool = self.tools.get(tool_id)
            if not tool:
                return

            # Resolve dependencies first
            for dep in tool.dependencies:
                if dep not in visited:
                    resolve_tool(dep)

            # Add tool
            if tool_id not in resolved:
                resolved.append(tool_id)

        # Resolve each requested tool
        for tool_id in tool_ids:
            resolve_tool(tool_id)

        return resolved

    def _create_execution_steps(self, tool_ids: List[str],
                               target_os: str) -> List[ToolStep]:
        """Create execution steps from tool IDs.

        Args:
            tool_ids: List of tool IDs
            target_os: Target OS

        Returns:
            List of ToolStep objects
        """
        steps = []

        for idx, tool_id in enumerate(tool_ids):
            tool = self.tools[tool_id]

            # Skip tools that don't support target OS
            if tool.requires_os and target_os not in tool.requires_os and 'any' not in tool.requires_os:
                continue

            # Determine dependencies from previous steps
            depends_on = []
            for dep_id in tool.dependencies:
                for prev_step in steps:
                    if prev_step.tool.tool_id == dep_id:
                        depends_on.append(prev_step.step_id)

            # Determine execution mode
            execution_mode = ExecutionMode.SEQUENTIAL
            if tool.category == 'recon' and idx > 0:
                # Recon tools can run in parallel
                execution_mode = ExecutionMode.PARALLEL
            elif tool.category == 'exploit':
                # Exploitation is conditional on vulnerabilities found
                execution_mode = ExecutionMode.CONDITIONAL

            # Create step
            step = ToolStep(
                step_id=f"step_{idx}_{tool_id}",
                tool=tool,
                parameters=tool.parameters.copy(),
                depends_on=depends_on,
                execution_mode=execution_mode,
                condition='if_previous_success' if depends_on else None
            )

            steps.append(step)

        return steps

    def _calculate_risk_level(self, steps: List[ToolStep]) -> str:
        """Calculate risk level of execution plan.

        Args:
            steps: List of execution steps

        Returns:
            Risk level string
        """
        has_exploit = any(step.tool.category == 'exploit' for step in steps)
        has_post_exploit = any(step.tool.category == 'post_exploit' for step in steps)

        if has_post_exploit:
            return 'high'
        elif has_exploit:
            return 'medium'
        else:
            return 'low'

    def get_alternative_tools(self, tool_id: str) -> List[str]:
        """Get alternative tools for a given tool.

        Args:
            tool_id: Tool ID

        Returns:
            List of alternative tool IDs
        """
        tool = self.tools.get(tool_id)
        if not tool:
            return []

        # Find tools in same category
        alternatives = []
        for alt_id, alt_tool in self.tools.items():
            if alt_id != tool_id and alt_tool.category == tool.category:
                alternatives.append(alt_id)

        return alternatives

    def optimize_plan(self, plan: ExecutionPlan,
                     performance_data: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """Optimize execution plan based on performance data.

        Args:
            plan: Execution plan to optimize
            performance_data: Optional historical performance data

        Returns:
            Optimized execution plan
        """
        # If no performance data, return original plan
        if not performance_data:
            return plan

        optimized_steps = []

        for step in plan.steps:
            # Check if tool has poor performance
            tool_stats = performance_data.get(step.tool.tool_id, {})
            success_rate = tool_stats.get('success_rate', 1.0)

            # If tool has low success rate, try to find alternative
            if success_rate < 0.5:
                alternatives = self.get_alternative_tools(step.tool.tool_id)
                if alternatives:
                    # Use first alternative with better success rate
                    for alt_id in alternatives:
                        alt_stats = performance_data.get(alt_id, {})
                        alt_success = alt_stats.get('success_rate', 1.0)
                        if alt_success > success_rate:
                            step.tool = self.tools[alt_id]
                            break

            optimized_steps.append(step)

        plan.steps = optimized_steps
        return plan

    def visualize_plan(self, plan: ExecutionPlan) -> str:
        """Create text visualization of execution plan.

        Args:
            plan: Execution plan

        Returns:
            Text visualization
        """
        lines = []
        lines.append(f"Execution Plan: {plan.plan_id}")
        lines.append(f"Target: {plan.target_type} ({plan.target_os})")
        lines.append(f"Risk Level: {plan.risk_level.upper()}")
        lines.append(f"Estimated Time: {plan.total_estimated_time // 60} minutes")
        lines.append("")
        lines.append("Steps:")

        for idx, step in enumerate(plan.steps, 1):
            mode_icon = "→" if step.execution_mode == ExecutionMode.SEQUENTIAL else "⇉"
            lines.append(f"  {idx}. {mode_icon} {step.tool.tool_name} ({step.tool.category})")

            if step.depends_on:
                lines.append(f"     Depends on: {', '.join(step.depends_on)}")

            if step.condition:
                lines.append(f"     Condition: {step.condition}")

        return "\n".join(lines)


# For testing - fix missing import
import time
