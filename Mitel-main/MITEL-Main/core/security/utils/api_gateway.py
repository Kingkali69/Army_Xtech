"""
GhostAI API Gateway
REST API endpoints for all GhostAI functionality.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from functools import wraps
import json
import os
from typing import Dict, Any, Optional

from ghostai_core import GhostAI
from security_layer import SecurityLayer


# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize GhostAI and security
ghostai = GhostAI()
security = SecurityLayer()


def require_auth(f):
    """Decorator to require authentication for endpoints.

    Args:
        f: Function to wrap

    Returns:
        Wrapped function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'No authorization token provided'}), 401

        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != 'Bearer':
            return jsonify({'success': False, 'error': 'Invalid authorization header'}), 401

        token = parts[1]

        # Verify token
        user = security.verify_token(token)
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401

        # Store user in request context
        request.user = user
        request.token = token

        return f(*args, **kwargs)

    return decorated_function


# Authentication endpoints

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """Login endpoint.

    Request body:
        {
            "username": "string",
            "password": "string",
            "protocol": "local" | "dead_duck"
        }

    Returns:
        {
            "success": true,
            "token": "string",
            "user": {...}
        }
    """
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    protocol = data.get('protocol', 'local')

    if not username or not password:
        return jsonify({
            'success': False,
            'error': 'Username and password required'
        }), 400

    # Authenticate
    user = security.authenticate_user(username, password, protocol)

    if not user:
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401

    return jsonify({
        'success': True,
        'token': user.token,
        'user': {
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role,
            'permissions': user.permissions
        }
    })


@app.route('/api/v1/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Logout endpoint.

    Returns:
        {
            "success": true
        }
    """
    security.logout(request.token)
    return jsonify({'success': True})


# Contract endpoints

@app.route('/api/v1/upload_contract', methods=['POST'])
@require_auth
def upload_contract():
    """Upload and parse contract.

    Request body:
        {
            "contract_path": "string" or file upload
        }

    Returns:
        {
            "success": true,
            "contract_id": "string",
            "summary": {...},
            "recommendations": [...]
        }
    """
    # Check if file was uploaded
    if 'file' in request.files:
        file = request.files['file']
        # Save temporarily
        temp_path = f"/tmp/contract_{request.user.user_id}_{file.filename}"
        file.save(temp_path)
        contract_path = temp_path
    else:
        data = request.get_json()
        contract_path = data.get('contract_path')

    if not contract_path:
        return jsonify({
            'success': False,
            'error': 'Contract path or file required'
        }), 400

    # Upload contract
    result = ghostai.upload_contract(contract_path, request.token)

    # Clean up temp file if it exists
    if 'file' in request.files and os.path.exists(temp_path):
        os.remove(temp_path)

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/api/v1/start_engagement', methods=['POST'])
@require_auth
def start_engagement():
    """Start security engagement.

    Request body:
        {
            "engagement_id": "string",
            "selected_tools": ["tool1", "tool2"] (optional)
        }

    Returns:
        {
            "success": true,
            "engagement_id": "string",
            "job_ids": [...]
        }
    """
    data = request.get_json()

    engagement_id = data.get('engagement_id')
    selected_tools = data.get('selected_tools')

    if not engagement_id:
        return jsonify({
            'success': False,
            'error': 'engagement_id required'
        }), 400

    # Start engagement
    result = ghostai.start_engagement(
        engagement_id,
        request.token,
        selected_tools
    )

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/api/v1/status', methods=['GET'])
@require_auth
def get_status():
    """Get engagement status.

    Query parameters:
        engagement_id: string

    Returns:
        {
            "success": true,
            "status": "string",
            "progress": 0-100,
            "jobs": [...]
        }
    """
    engagement_id = request.args.get('engagement_id')

    if not engagement_id:
        return jsonify({
            'success': False,
            'error': 'engagement_id required'
        }), 400

    # Get status
    result = ghostai.get_status(engagement_id, request.token)

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/api/v1/report', methods=['GET'])
@require_auth
def get_report():
    """Get engagement report.

    Query parameters:
        engagement_id: string
        format: 'json' | 'pdf' | 'html' (optional, default: json)

    Returns:
        {
            "success": true,
            "report": {...}
        }
    """
    engagement_id = request.args.get('engagement_id')
    format_type = request.args.get('format', 'json')

    if not engagement_id:
        return jsonify({
            'success': False,
            'error': 'engagement_id required'
        }), 400

    # Get report
    result = ghostai.get_report(engagement_id, request.token)

    if not result.get('success'):
        return jsonify(result), 400

    # Return based on format
    if format_type == 'json':
        return jsonify(result), 200
    elif format_type == 'pdf':
        # TODO: Generate PDF report
        return jsonify({
            'success': False,
            'error': 'PDF format not yet implemented'
        }), 501
    elif format_type == 'html':
        # TODO: Generate HTML report
        return jsonify({
            'success': False,
            'error': 'HTML format not yet implemented'
        }), 501
    else:
        return jsonify({
            'success': False,
            'error': f'Invalid format: {format_type}'
        }), 400


@app.route('/api/v1/learned_patterns', methods=['GET'])
@require_auth
def get_learned_patterns():
    """Get learned patterns.

    Query parameters:
        target_type: string (optional)

    Returns:
        {
            "success": true,
            "patterns": [...],
            "tool_effectiveness": {...},
            "optimizations": [...]
        }
    """
    target_type = request.args.get('target_type')

    # Get learned patterns
    result = ghostai.get_learned_patterns(request.token, target_type)

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400


# System endpoints

@app.route('/api/v1/system/stats', methods=['GET'])
@require_auth
def get_system_stats():
    """Get system statistics.

    Returns:
        {
            "success": true,
            "engagement_stats": {...},
            "tool_performance": {...},
            "system_metrics": {...}
        }
    """
    result = ghostai.get_system_stats(request.token)

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/api/v1/system/health', methods=['GET'])
def health_check():
    """Health check endpoint.

    Returns:
        {
            "status": "healthy",
            "version": "1.0.0"
        }
    """
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'components': {
            'database': 'ok',
            'execution_engine': 'ok',
            'learning_module': 'ok'
        }
    })


# Tool endpoints

@app.route('/api/v1/tools', methods=['GET'])
@require_auth
def list_tools():
    """List available tools.

    Query parameters:
        category: string (optional)
        os_type: string (optional)

    Returns:
        {
            "success": true,
            "tools": [...]
        }
    """
    category = request.args.get('category')
    os_type = request.args.get('os_type')

    tools = ghostai.tool_orchestrator.list_tools(category, os_type)

    return jsonify({
        'success': True,
        'tools': [
            {
                'tool_id': t.tool_id,
                'tool_name': t.tool_name,
                'category': t.category,
                'description': t.description,
                'requires_os': t.requires_os,
                'timeout': t.timeout
            }
            for t in tools
        ]
    })


@app.route('/api/v1/tools/recommend', methods=['POST'])
@require_auth
def recommend_tools():
    """Get tool recommendations.

    Request body:
        {
            "target_type": "string",
            "target_os": "string",
            "objectives": ["string"]
        }

    Returns:
        {
            "success": true,
            "recommendations": [...]
        }
    """
    data = request.get_json()

    target_type = data.get('target_type', 'ip')
    target_os = data.get('target_os', 'unknown')
    objectives = data.get('objectives', [])

    recommendations = ghostai.learning_module.get_recommendations(
        target_type, target_os, objectives
    )

    return jsonify({
        'success': True,
        'recommendations': [
            {
                'tool_ids': rec.tool_ids,
                'confidence': rec.confidence,
                'reasoning': rec.reasoning,
                'estimated_time': rec.estimated_time,
                'estimated_success_rate': rec.estimated_success_rate,
                'source': rec.source
            }
            for rec in recommendations
        ]
    })


# Job management endpoints

@app.route('/api/v1/jobs/<job_id>', methods=['GET'])
@require_auth
def get_job_status(job_id):
    """Get job status.

    Returns:
        {
            "success": true,
            "job": {...}
        }
    """
    job = ghostai.execution_engine.get_job_status(job_id)

    if not job:
        return jsonify({
            'success': False,
            'error': f'Job not found: {job_id}'
        }), 404

    return jsonify({
        'success': True,
        'job': {
            'job_id': job.job_id,
            'engagement_id': job.engagement_id,
            'status': job.status.value,
            'progress': job.progress_percent,
            'current_step': job.current_step,
            'completed_steps': job.completed_steps,
            'total_steps': job.total_steps
        }
    })


@app.route('/api/v1/jobs/<job_id>/cancel', methods=['POST'])
@require_auth
def cancel_job(job_id):
    """Cancel a job.

    Returns:
        {
            "success": true
        }
    """
    success = ghostai.execution_engine.cancel_job(job_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': 'Job not found or cannot be cancelled'
        }), 400


@app.route('/api/v1/jobs/<job_id>/output', methods=['GET'])
@require_auth
def get_job_output(job_id):
    """Get real-time job output.

    Returns:
        {
            "success": true,
            "output": ["line1", "line2", ...]
        }
    """
    output = ghostai.execution_engine.get_real_time_output(job_id)

    return jsonify({
        'success': True,
        'output': output
    })


# Error handler
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


def run_api_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """Run the API server.

    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_api_server(debug=True)
