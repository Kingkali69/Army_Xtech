# =======================================================
# KK&G CYBERSECURITY ENGINE - MASTER CONFIGURATION
# Enterprise-Grade Configuration Scaffolding
# =======================================================

# Core Engine Configuration
engine:
  # Platform detection and overrides
  platform: auto-detect  # auto-detect, windows, linux, darwin, generic
  
  # Performance and scaling parameters
  max_threads: 10
  event_buffer_size: 10000
  max_memory_mb: 512
  cpu_limit_percent: 20
  
  # Logging and monitoring
  log_level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_rotation_size: 100MB
  log_retention_days: 30
  audit_trail: true
  
  # Health and heartbeat monitoring
  heartbeat_interval: 30
  health_check_timeout: 5
  module_restart_threshold: 3
  
  # Security and integrity
  integrity_check_interval: 300
  license_validation_interval: 3600
  tamper_detection: true

# =======================================================
# SECURITY MODULES CONFIGURATION
# =======================================================

modules:
  # Network Security Module
  network_security:
    enabled: true
    priority: 3
    config:
      # Interface monitoring
      monitor_interfaces: ["all"]  # ["eth0", "wlan0"] or ["all"]
      exclude_interfaces: ["lo", "docker0"]
      
      # Detection parameters
      detection_threshold: 100
      analysis_window_seconds: 300
      packet_capture_enabled: false
      deep_packet_inspection: true
      
      # Threat detection
      anomaly_detection: true
      port_scan_detection: true
      dos_detection: true
      lateral_movement_detection: true
      
      # Response configuration
      auto_block_malicious: true
      auto_block_duration: 3600
      whitelist_ranges: ["10.0.0.0/8", "192.168.0.0/16", "172.16.0.0/12"]
      
      # Advanced features
      geo_ip_blocking: false
      reputation_feeds: ["spamhaus", "emergingthreats"]
      ssl_inspection: false

  # Endpoint Security Module  
  endpoint_security:
    enabled: true
    priority: 1
    config:
      # Monitoring scope
      file_monitoring: true
      process_monitoring: true
      registry_monitoring: true
      memory_scanning: false
      
      # File system monitoring
      monitored_directories: 
        - "/etc"
        - "/bin"
        - "/usr/bin"
        - "/tmp"
        - "C:\\Windows\\System32"
        - "C:\\Program Files"
      
      excluded_extensions: [".log", ".tmp", ".cache"]
      real_time_scanning: true
      hash_verification: true
      
      # Process monitoring
      suspicious_process_patterns:
        - "*.exe"
        - "*miner*"
        - "*crypto*"
        - "powershell.exe -enc"
      
      process_injection_detection: true
      privilege_escalation_detection: true
      
      # Behavioral analysis
      behavioral_heuristics: true
      ml_anomaly_detection: false
      baseline_learning_period: 168  # hours
      
      # Response actions
      quarantine_suspicious_files: true
      auto_kill_malicious_processes: false
      create_forensic_snapshots: true

  # Behavioral Analysis Module
  behavioral_analysis:
    enabled: false
    priority: 2
    config:
      # Machine Learning Configuration
      ml_model_path: "./models/behavioral.pkl"
      model_update_interval: 24  # hours
      training_data_retention: 90  # days
      
      # Anomaly Detection
      anomaly_threshold: 0.8
      baseline_establishment_days: 7
      user_behavior_profiling: true
      entity_behavior_analytics: true
      
      # Analysis Windows
      short_term_window: 300    # 5 minutes
      medium_term_window: 3600  # 1 hour  
      long_term_window: 86400   # 24 hours
      
      # Features to analyze
      network_patterns: true
      file_access_patterns: true
      process_execution_patterns: true
      login_patterns: true
      resource_usage_patterns: true

  # Threat Intelligence Module
  threat_intelligence:
    enabled: false
    priority: 4
    config:
      # Intelligence Feeds
      feeds:
        - name: "emerging_threats"
          url: "https://rules.emergingthreats.net/open/suricata/emerging.rules"
          update_interval: 3600
          enabled: true
        - name: "malware_domains"
          url: "https://mirror1.malwaredomains.com/files/justdomains"
          update_interval: 7200
          enabled: true
      
      # IoC Management
      ioc_retention_days: 90
      auto_expire_iocs: true
      custom_ioc_feeds: []
      
      # Threat Scoring
      threat_scoring_enabled: true
      confidence_threshold: 0.7
      severity_weights:
        critical: 1.0
        high: 0.8
        medium: 0.5
        low: 0.2

  # Compliance & Reporting Module
  compliance_reporting:
    enabled: true
    priority: 5
    config:
      # Compliance Frameworks
      frameworks: ["SOC2", "ISO27001", "NIST"]
      
      # Report Generation
      daily_reports: true
      weekly_summaries: true
      monthly_compliance_reports: true
      custom_report_templates: []
      
      # Data Retention
      log_retention_days: 365
      evidence_retention_days: 2555  # 7 years
      audit_trail_encryption: true
      
      # Export Formats
      supported_formats: ["PDF", "JSON", "XML", "CSV"]
      default_format: "PDF"

# =======================================================
# PLATFORM-SPECIFIC OVERRIDES
# =======================================================

platform_overrides:
  # Windows-specific configuration
  windows:
    event_sources:
      - "Security"
      - "Application" 
      - "System"
      - "Microsoft-Windows-Sysmon/Operational"
      - "Microsoft-Windows-PowerShell/Operational"
    
    # Windows Event Log configuration
    event_log_max_size: 512MB
    event_log_retention: "overwrite"
    
    # WMI and Performance Counters
    performance_counters: true
    wmi_monitoring: true
    wmi_queries:
      - "SELECT * FROM Win32_Process WHERE CreationDate > '${timestamp}'"
      - "SELECT * FROM Win32_LogicalDisk WHERE FreeSpace < 1000000000"
    
    # Windows-specific features
    registry_monitoring_keys:
      - "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
      - "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
      - "HKLM\\SYSTEM\\CurrentControlSet\\Services"
    
    # Advanced Windows features
    etw_providers: ["Microsoft-Windows-Kernel-Process", "Microsoft-Windows-Security-Auditing"]
    use_sysmon: true
    powershell_logging: true
    
    # Response capabilities
    windows_firewall_integration: true
    service_control_enabled: true
    scheduled_task_monitoring: true

  # Linux-specific configuration  
  linux:
    event_sources:
      - "/var/log/syslog"
      - "/var/log/auth.log"
      - "/var/log/kern.log"
      - "journald"
    
    # System monitoring
    use_auditd: true
    auditd_rules_path: "/etc/audit/rules.d/"
    
    # Filesystem monitoring
    inotify_monitoring: true
    proc_monitoring: true
    sys_monitoring: true
    
    # Network monitoring
    netlink_sockets: true
    iptables_integration: true
    tc_integration: false  # Traffic Control
    
    # Linux-specific paths
    critical_directories:
      - "/etc"
      - "/bin" 
      - "/sbin"
      - "/usr/bin"
      - "/usr/sbin"
      - "/boot"
    
    # Container monitoring
    docker_monitoring: true
    kubernetes_integration: false
    cgroup_monitoring: true
    
    # Response capabilities
    iptables_auto_blocking: true
    systemctl_integration: true
    process_cgroup_isolation: true

  # macOS-specific configuration
  darwin:
    event_sources:
      - "system.log"
      - "unified_logging"
      - "/var/log/install.log"
      - "/var/log/system.log"
    
    # macOS monitoring
    use_dtrace: false
    endpoint_security_framework: true
    fsevents_monitoring: true
    
    # Security features
    system_integrity_protection: true
    gatekeeper_monitoring: true
    xprotect_integration: true
    
    # Application monitoring
    bundle_monitoring: true
    launch_daemon_monitoring: true
    launch_agent_monitoring: true
    
    # Response capabilities
    application_firewall_integration: true
    quarantine_integration: true

  # Mobile platform configuration
  mobile:
    android:
      event_sources: ["logcat", "kernel_logs"]
      permissions_monitoring: true
      app_behavior_analysis: true
      network_monitoring: true
      
    ios:
      event_sources: ["unified_logging"]
      app_sandbox_monitoring: true
      certificate_pinning_detection: true
      jailbreak_detection: true

# =======================================================
# API & INTEGRATION CONFIGURATION
# =======================================================

api:
  # REST API Configuration
  rest:
    enabled: true
    port: 8080
    bind_address: "0.0.0.0"
    max_connections: 1000
    request_timeout: 30
    
    # Security
    enable_ssl: true
    ssl_cert_path: "./certs/server.crt"
    ssl_key_path: "./certs/server.key"
    
    # Authentication
    authentication_required: true
    api_keys: []  # Populated at runtime
    jwt_secret: "${JWT_SECRET}"
    token_expiry: 3600
    
    # Rate limiting
    rate_limit_enabled: true
    requests_per_minute: 100
    burst_limit: 20

  # WebSocket Configuration
  websocket:
    enabled: true
    port: 8081
    max_connections: 500
    heartbeat_interval: 30
    message_buffer_size: 1000
    
    # Real-time streams
    event_streaming: true
    health_streaming: true
    response_streaming: true

  # SDK Configuration
  sdk:
    enabled: true
    language_bindings: ["python", "javascript", "java", "csharp"]
    documentation_path: "./docs/api"
    
    # Client libraries
    auto_generate_clients: true
    client_timeout: 60
    retry_attempts: 3

# =======================================================
# INTEGRATION ECOSYSTEM
# =======================================================

integrations:
  # SIEM Integrations
  siem:
    splunk:
      enabled: false
      endpoint: "https://splunk.company.com:8088"
      token: "${SPLUNK_TOKEN}"
      index: "cybersecurity"
      
    elasticsearch:
      enabled: false
      hosts: ["https://elastic.company.com:9200"]
      index: "kkg-security"
      api_key: "${ELASTIC_API_KEY}"
      
    qradar:
      enabled: false
      endpoint: "https://qradar.company.com"
      api_token: "${QRADAR_TOKEN}"
      
  # SOAR Integrations  
  soar:
    phantom:
      enabled: false
      endpoint: "https://phantom.company.com"
      api_token: "${PHANTOM_TOKEN}"
      
    demisto:
      enabled: false
      endpoint: "https://demisto.company.com"
      api_key: "${DEMISTO_API_KEY}"

  # Cloud Security Platforms
  cloud:
    aws_security_hub:
      enabled: false
      region: "us-east-1"
      access_key_id: "${AWS_ACCESS_KEY_ID}"
      secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
      
    azure_sentinel:
      enabled: false
      workspace_id: "${AZURE_WORKSPACE_ID}"
      shared_key: "${AZURE_SHARED_KEY}"
      
    gcp_security_command_center:
      enabled: false
      project_id: "${GCP_PROJECT_ID}"
      credentials_path: "${GCP_CREDENTIALS_PATH}"

# =======================================================
# DEPLOYMENT CONFIGURATION
# =======================================================

deployment:
  # Deployment mode
  mode: standalone  # standalone, centralized, cloud-native
  
  # Scaling parameters
  auto_scaling: false
  min_instances: 1
  max_instances: 5
  scale_threshold_cpu: 80
  scale_threshold_memory: 80
  
  # High availability
  cluster_mode: false
  cluster_nodes: []
  failover_enabled: false
  
  # Container deployment
  container:
    enabled: false
    image: "kkg/cybersecurity-engine:latest"
    resources:
      cpu_limit: "1000m"
      memory_limit: "1Gi"
      cpu_request: "100m" 
      memory_request: "256Mi"

# =======================================================
# LICENSING & IP PROTECTION
# =======================================================

licensing:
  # License validation
  license_key: "${KKG_LICENSE_KEY}"
  license_server: "https://licensing.kkg.com"
  validation_interval: 3600
  offline_grace_period: 72  # hours
  
  # Feature licensing
  licensed_features: []  # Populated by license server
  feature_usage_tracking: true
  
  # Protection mechanisms
  code_obfuscation: true
  integrity_monitoring: true
  anti_tampering: true
  license_binding: "hardware"  # hardware, software, hybrid

# =======================================================
# PERFORMANCE & MONITORING
# =======================================================

performance:
  # Resource limits
  max_cpu_usage: 20  # percentage
  max_memory_usage: 512  # MB
  max_disk_usage: 10  # GB
  
  # Performance monitoring
  metrics_collection: true
  performance_profiling: false
  detailed_timing: false
  
  # Optimization
  event_batching: true
  batch_size: 100
  batch_timeout: 1000  # milliseconds
  
  # Caching
  cache_enabled: true
  cache_size: 100  # MB
  cache_ttl: 3600  # seconds

# =======================================================
# SECURITY HARDENING
# =======================================================

security:
  # Engine security
  encrypted_configuration: false
  secure_memory_allocation: true
  stack_protection: true
  
  # Communication security
  mutual_tls: false
  certificate_validation: true
  secure_random_generation: true
  
  # Data protection
  data_encryption_at_rest: false
  encryption_algorithm: "AES-256-GCM"
  key_rotation_interval: 30  # days
  
  # Access control
  rbac_enabled: false
  admin_users: ["admin"]
  read_only_users: []
  
# =======================================================
# CUSTOM EXTENSIONS
# =======================================================

extensions:
  # Custom module paths
  custom_modules_path: "./custom_modules"
  
  # Plugin system
  plugin_system_enabled: true
  plugin_directory: "./plugins"
  plugin_signature_verification: true
  
  # Scripting engine
  scripting_enabled: false
  allowed_languages: ["python", "lua"]
  script_timeout: 30
  
  # Custom rules engine
  rules_engine_enabled: true
  rules_directory: "./rules"
  rules_language: "yaml"  # yaml, json, xml

# =======================================================
# DEVELOPMENT & DEBUGGING
# =======================================================

development:
  # Debug settings
  debug_mode: false
  verbose_logging: false
  profiling_enabled: false
  
  # Testing
  test_mode: false
  mock_platform_adapter: false
  simulation_mode: false
  
  # Development tools
  api_documentation: true
  swagger_ui: true
  health_dashboard: true
