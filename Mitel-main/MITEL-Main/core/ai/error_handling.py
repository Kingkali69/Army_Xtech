"""
GhostAI Error Handling Module
Comprehensive error handling for all GhostAI components with user-friendly messages.
"""

import logging
import traceback
from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories."""
    CONTRACT_PARSER = "contract_parser"
    TOOL_ORCHESTRATOR = "tool_orchestrator"
    EXECUTION_ENGINE = "execution_engine"
    LEARNING_MODULE = "learning_module"
    NETWORK = "network"
    DATABASE = "database"
    SECURITY = "security"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    SYSTEM = "system"


@dataclass
class GhostAIError:
    """Structured error object."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    technical_details: Optional[str] = None
    timestamp: Optional[str] = None
    suggested_action: Optional[str] = None
    error_code: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'user_message': self.user_message,
            'technical_details': self.technical_details,
            'timestamp': self.timestamp,
            'suggested_action': self.suggested_action,
            'error_code': self.error_code
        }


class ErrorHandler:
    """Central error handler for GhostAI."""

    def __init__(self, log_file: Optional[str] = None):
        """Initialize error handler.

        Args:
            log_file: Optional log file path
        """
        self.log_file = log_file
        self._setup_logging()
        self.error_history = []

    def _setup_logging(self):
        """Setup logging configuration."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        if self.log_file:
            logging.basicConfig(
                level=logging.INFO,
                format=log_format,
                handlers=[
                    logging.FileHandler(self.log_file),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format=log_format,
                handlers=[logging.StreamHandler()]
            )

        self.logger = logging.getLogger('GhostAI')

    def handle_error(self, error: GhostAIError) -> Dict[str, Any]:
        """Handle an error.

        Args:
            error: GhostAIError object

        Returns:
            Error response dictionary
        """
        # Log the error
        log_message = f"[{error.category.value}] {error.message}"
        if error.technical_details:
            log_message += f" | Details: {error.technical_details}"

        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        # Store in history
        self.error_history.append(error)

        # Return user-friendly response
        return {
            'success': False,
            'error': error.to_dict()
        }

    # Contract Parser Errors
    def handle_contract_parse_error(self, exception: Exception, contract_data: Any) -> Dict[str, Any]:
        """Handle contract parsing errors.

        Args:
            exception: The exception that occurred
            contract_data: The contract data that failed to parse

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.CONTRACT_PARSER,
            severity=ErrorSeverity.ERROR,
            message=f"Failed to parse contract: {str(exception)}",
            user_message="We couldn't parse the uploaded contract. Please check the format and try again.",
            technical_details=traceback.format_exc(),
            suggested_action="Ensure the contract is in valid YAML or JSON format with required fields: scope, targets, timeline.",
            error_code="CP001"
        )
        return self.handle_error(error)

    def handle_invalid_contract_format(self, missing_fields: list) -> Dict[str, Any]:
        """Handle invalid contract format.

        Args:
            missing_fields: List of missing required fields

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.CONTRACT_PARSER,
            severity=ErrorSeverity.ERROR,
            message=f"Contract missing required fields: {', '.join(missing_fields)}",
            user_message=f"The contract is missing required fields: {', '.join(missing_fields)}",
            suggested_action="Add the missing fields to your contract and upload again.",
            error_code="CP002"
        )
        return self.handle_error(error)

    # Tool Orchestrator Errors
    def handle_tool_not_found(self, tool_name: str, alternatives: Optional[list] = None) -> Dict[str, Any]:
        """Handle tool not found error.

        Args:
            tool_name: Name of the tool that wasn't found
            alternatives: Optional list of alternative tools

        Returns:
            Error response
        """
        user_message = f"Tool '{tool_name}' is not available."
        suggested_action = f"Please choose a different tool."

        if alternatives:
            user_message += f" Available alternatives: {', '.join(alternatives)}"
            suggested_action = f"Try using one of these alternatives: {', '.join(alternatives)}"

        error = GhostAIError(
            category=ErrorCategory.TOOL_ORCHESTRATOR,
            severity=ErrorSeverity.WARNING,
            message=f"Tool not found: {tool_name}",
            user_message=user_message,
            suggested_action=suggested_action,
            error_code="TO001"
        )
        return self.handle_error(error)

    def handle_tool_dependency_error(self, tool_name: str, missing_dependencies: list) -> Dict[str, Any]:
        """Handle tool dependency error.

        Args:
            tool_name: Name of the tool
            missing_dependencies: List of missing dependencies

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.TOOL_ORCHESTRATOR,
            severity=ErrorSeverity.ERROR,
            message=f"Tool '{tool_name}' has missing dependencies: {', '.join(missing_dependencies)}",
            user_message=f"Cannot run '{tool_name}' because required tools are missing: {', '.join(missing_dependencies)}",
            suggested_action=f"Ensure these tools are available: {', '.join(missing_dependencies)}",
            error_code="TO002"
        )
        return self.handle_error(error)

    def handle_tool_chain_error(self, exception: Exception, tool_chain: list) -> Dict[str, Any]:
        """Handle tool chain execution error.

        Args:
            exception: The exception that occurred
            tool_chain: The tool chain that failed

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.TOOL_ORCHESTRATOR,
            severity=ErrorSeverity.ERROR,
            message=f"Tool chain execution failed: {str(exception)}",
            user_message="The tool execution plan failed. We'll try an alternative approach.",
            technical_details=traceback.format_exc(),
            suggested_action="Review the tool chain and ensure all tools are compatible.",
            error_code="TO003"
        )
        return self.handle_error(error)

    # Execution Engine Errors
    def handle_execution_timeout(self, tool_name: str, timeout_seconds: int) -> Dict[str, Any]:
        """Handle execution timeout.

        Args:
            tool_name: Name of the tool that timed out
            timeout_seconds: Timeout duration in seconds

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.WARNING,
            message=f"Tool '{tool_name}' execution timed out after {timeout_seconds} seconds",
            user_message=f"The '{tool_name}' tool is taking longer than expected. Attempting auto-recovery...",
            suggested_action="The system will automatically retry with adjusted parameters.",
            error_code="EE001"
        )
        return self.handle_error(error)

    def handle_execution_failure(self, tool_name: str, exception: Exception, retry_count: int = 0) -> Dict[str, Any]:
        """Handle execution failure.

        Args:
            tool_name: Name of the tool that failed
            exception: The exception that occurred
            retry_count: Number of retries attempted

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.EXECUTION_ENGINE,
            severity=ErrorSeverity.ERROR,
            message=f"Tool '{tool_name}' execution failed: {str(exception)} (retry: {retry_count})",
            user_message=f"The '{tool_name}' tool encountered an error during execution.",
            technical_details=traceback.format_exc(),
            suggested_action="The system will attempt to recover automatically." if retry_count < 3 else "Manual intervention may be required.",
            error_code="EE002"
        )
        return self.handle_error(error)

    # Learning Module Errors
    def handle_mistral_inference_error(self, exception: Exception, fallback_available: bool = True) -> Dict[str, Any]:
        """Handle Mistral AI inference error.

        Args:
            exception: The exception that occurred
            fallback_available: Whether fallback to rule-based is available

        Returns:
            Error response
        """
        user_message = "AI recommendation engine is temporarily unavailable."
        suggested_action = "Using rule-based recommendations instead." if fallback_available else "Manual tool selection required."

        error = GhostAIError(
            category=ErrorCategory.LEARNING_MODULE,
            severity=ErrorSeverity.WARNING if fallback_available else ErrorSeverity.ERROR,
            message=f"Mistral inference failed: {str(exception)}",
            user_message=user_message,
            technical_details=traceback.format_exc(),
            suggested_action=suggested_action,
            error_code="LM001"
        )
        return self.handle_error(error)

    def handle_pattern_learning_error(self, exception: Exception) -> Dict[str, Any]:
        """Handle pattern learning error.

        Args:
            exception: The exception that occurred

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.LEARNING_MODULE,
            severity=ErrorSeverity.WARNING,
            message=f"Pattern learning failed: {str(exception)}",
            user_message="Unable to save learning data, but execution will continue.",
            technical_details=traceback.format_exc(),
            suggested_action="This won't affect current execution, but future recommendations may be limited.",
            error_code="LM002"
        )
        return self.handle_error(error)

    # Network Errors
    def handle_network_error(self, exception: Exception, operation: str) -> Dict[str, Any]:
        """Handle network errors.

        Args:
            exception: The exception that occurred
            operation: The operation that failed

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.ERROR,
            message=f"Network error during {operation}: {str(exception)}",
            user_message="Network connection issue detected. Retrying...",
            technical_details=traceback.format_exc(),
            suggested_action="Check your network connection and firewall settings.",
            error_code="NET001"
        )
        return self.handle_error(error)

    # Database Errors
    def handle_database_error(self, exception: Exception, operation: str) -> Dict[str, Any]:
        """Handle database errors.

        Args:
            exception: The exception that occurred
            operation: The operation that failed

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR,
            message=f"Database error during {operation}: {str(exception)}",
            user_message="Database operation failed. Your data may not be saved.",
            technical_details=traceback.format_exc(),
            suggested_action="Check database permissions and disk space.",
            error_code="DB001"
        )
        return self.handle_error(error)

    # Security Errors
    def handle_unauthorized_access(self, resource: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle unauthorized access attempts.

        Args:
            resource: The resource being accessed
            user_id: Optional user ID

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            message=f"Unauthorized access attempt to {resource} by user {user_id}",
            user_message="Access denied. You don't have permission to perform this action.",
            suggested_action="Please contact your administrator for access.",
            error_code="SEC001"
        )
        return self.handle_error(error)

    def handle_invalid_credentials(self, protocol: str) -> Dict[str, Any]:
        """Handle invalid credentials.

        Args:
            protocol: The authentication protocol

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.ERROR,
            message=f"Invalid credentials for {protocol}",
            user_message="Authentication failed. Please check your credentials.",
            suggested_action="Verify your credentials and try again.",
            error_code="SEC002"
        )
        return self.handle_error(error)

    def handle_encryption_error(self, exception: Exception, data_type: str) -> Dict[str, Any]:
        """Handle encryption errors.

        Args:
            exception: The exception that occurred
            data_type: Type of data being encrypted

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            message=f"Encryption failed for {data_type}: {str(exception)}",
            user_message="Failed to secure sensitive data. Operation aborted.",
            technical_details=traceback.format_exc(),
            suggested_action="Check encryption keys and permissions.",
            error_code="SEC003"
        )
        return self.handle_error(error)

    # Validation Errors
    def handle_validation_error(self, field: str, value: Any, expected: str) -> Dict[str, Any]:
        """Handle validation errors.

        Args:
            field: Field name
            value: Invalid value
            expected: Expected format/type

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            message=f"Validation failed for {field}: got {value}, expected {expected}",
            user_message=f"Invalid value for {field}. Expected {expected}.",
            suggested_action=f"Please provide a valid {expected} for {field}.",
            error_code="VAL001"
        )
        return self.handle_error(error)

    # Generic Error Handler
    def handle_generic_error(self, exception: Exception, context: str) -> Dict[str, Any]:
        """Handle generic errors.

        Args:
            exception: The exception that occurred
            context: Context where the error occurred

        Returns:
            Error response
        """
        error = GhostAIError(
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.ERROR,
            message=f"Error in {context}: {str(exception)}",
            user_message="An unexpected error occurred. Please try again.",
            technical_details=traceback.format_exc(),
            suggested_action="If the problem persists, contact support.",
            error_code="SYS001"
        )
        return self.handle_error(error)

    # Error Recovery
    def attempt_recovery(self, error: GhostAIError, recovery_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Attempt to recover from an error.

        Args:
            error: The error to recover from
            recovery_func: Function to call for recovery
            *args: Arguments for recovery function
            **kwargs: Keyword arguments for recovery function

        Returns:
            Recovery result or error response
        """
        try:
            self.logger.info(f"Attempting recovery from {error.category.value} error")
            result = recovery_func(*args, **kwargs)
            self.logger.info("Recovery successful")
            return {'success': True, 'result': result}
        except Exception as e:
            self.logger.error(f"Recovery failed: {str(e)}")
            return self.handle_generic_error(e, "error recovery")

    # Error Statistics
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics.

        Returns:
            Dictionary with error statistics
        """
        if not self.error_history:
            return {
                'total_errors': 0,
                'by_category': {},
                'by_severity': {},
                'recent_errors': []
            }

        by_category = {}
        by_severity = {}

        for error in self.error_history:
            # Count by category
            cat = error.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            # Count by severity
            sev = error.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            'total_errors': len(self.error_history),
            'by_category': by_category,
            'by_severity': by_severity,
            'recent_errors': [e.to_dict() for e in self.error_history[-10:]]
        }

    def clear_error_history(self):
        """Clear error history."""
        self.error_history = []


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance.

    Returns:
        ErrorHandler instance
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler
