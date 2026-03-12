#!/usr/bin/env python3
"""
GhostAI - Recommendation Engine
Recommends penetration testing tools based on contract intelligence.
"""

import json
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ToolRecommendation:
    """Single tool recommendation with reasoning."""
    name: str
    category: str
    priority: int  # 1 (critical) to 5 (optional)
    reason: str
    allowed_by_contract: bool


class RecommendationEngine:
    """Recommend penetration testing tools based on contract data."""

    # Comprehensive tool database
    TOOL_DATABASE = {
        # Network Scanning & Discovery
        "nmap": {
            "category": "Network Scanning",
            "description": "Network mapper for discovery and security auditing",
            "use_cases": ["network", "infrastructure", "port scanning", "service detection"]
        },
        "masscan": {
            "category": "Network Scanning",
            "description": "Fast TCP port scanner",
            "use_cases": ["network", "large-scale scanning"]
        },
        "netdiscover": {
            "category": "Network Scanning",
            "description": "Active/passive ARP reconnaissance tool",
            "use_cases": ["network", "discovery"]
        },

        # Web Application Testing
        "burp-suite": {
            "category": "Web Application",
            "description": "Integrated platform for web security testing",
            "use_cases": ["web application", "web app", "api", "http", "https"]
        },
        "sqlmap": {
            "category": "Web Application",
            "description": "Automatic SQL injection tool",
            "use_cases": ["web application", "database", "sql injection", "api"]
        },
        "nikto": {
            "category": "Web Application",
            "description": "Web server vulnerability scanner",
            "use_cases": ["web application", "web server", "vulnerability scanning"]
        },
        "owasp-zap": {
            "category": "Web Application",
            "description": "Web application security scanner",
            "use_cases": ["web application", "web app", "api"]
        },
        "wfuzz": {
            "category": "Web Application",
            "description": "Web application fuzzer",
            "use_cases": ["web application", "fuzzing", "api"]
        },
        "ffuf": {
            "category": "Web Application",
            "description": "Fast web fuzzer",
            "use_cases": ["web application", "directory brute force", "api"]
        },

        # Exploitation
        "metasploit": {
            "category": "Exploitation",
            "description": "Penetration testing framework",
            "use_cases": ["exploitation", "vulnerability assessment", "post-exploitation"]
        },
        "exploit-db": {
            "category": "Exploitation",
            "description": "Exploit database and search",
            "use_cases": ["exploitation", "vulnerability research"]
        },

        # Password Cracking
        "hashcat": {
            "category": "Password Cracking",
            "description": "Advanced password recovery",
            "use_cases": ["password cracking", "hash cracking", "authentication testing"]
        },
        "john-the-ripper": {
            "category": "Password Cracking",
            "description": "Password cracker",
            "use_cases": ["password cracking", "hash cracking", "authentication testing"]
        },
        "hydra": {
            "category": "Password Cracking",
            "description": "Network logon cracker",
            "use_cases": ["password cracking", "brute force", "authentication testing"]
        },

        # Wireless Testing
        "aircrack-ng": {
            "category": "Wireless",
            "description": "WiFi security auditing suite",
            "use_cases": ["wireless", "wifi", "802.11"]
        },
        "wifite": {
            "category": "Wireless",
            "description": "Automated wireless attack tool",
            "use_cases": ["wireless", "wifi"]
        },

        # Social Engineering
        "set": {
            "category": "Social Engineering",
            "description": "Social-Engineer Toolkit",
            "use_cases": ["social engineering", "phishing"]
        },
        "gophish": {
            "category": "Social Engineering",
            "description": "Phishing framework",
            "use_cases": ["social engineering", "phishing"]
        },

        # Vulnerability Scanning
        "nessus": {
            "category": "Vulnerability Scanning",
            "description": "Vulnerability scanner",
            "use_cases": ["vulnerability scanning", "compliance", "network"]
        },
        "openvas": {
            "category": "Vulnerability Scanning",
            "description": "Open source vulnerability scanner",
            "use_cases": ["vulnerability scanning", "network"]
        },

        # Sniffing & Interception
        "wireshark": {
            "category": "Network Analysis",
            "description": "Network protocol analyzer",
            "use_cases": ["network", "traffic analysis", "protocol analysis"]
        },
        "tcpdump": {
            "category": "Network Analysis",
            "description": "Packet analyzer",
            "use_cases": ["network", "traffic analysis"]
        },

        # Mobile Testing
        "mobsf": {
            "category": "Mobile Security",
            "description": "Mobile Security Framework",
            "use_cases": ["mobile app", "android", "ios"]
        },
        "apktool": {
            "category": "Mobile Security",
            "description": "Android APK reverse engineering",
            "use_cases": ["mobile app", "android"]
        },

        # Cloud Security
        "scoutsuite": {
            "category": "Cloud Security",
            "description": "Multi-cloud security auditing",
            "use_cases": ["cloud", "aws", "azure", "gcp"]
        },
        "prowler": {
            "category": "Cloud Security",
            "description": "AWS security assessment",
            "use_cases": ["cloud", "aws"]
        }
    }

    # Restriction mapping
    RESTRICTED_TOOLS = {
        "no dos": ["hping3", "loic", "slowloris"],
        "no denial of service": ["hping3", "loic", "slowloris"],
        "no social engineering": ["set", "gophish"],
        "no exfiltration": [],
        "no data destruction": []
    }

    def __init__(self):
        """Initialize recommendation engine."""
        pass

    def recommend(self, contract_data: Dict) -> List[ToolRecommendation]:
        """
        Recommend tools based on contract data.

        Args:
            contract_data: Parsed contract intelligence

        Returns:
            List of tool recommendations with reasoning
        """
        recommendations = []

        # Extract contract details
        scope = self._normalize_list(contract_data.get("SCOPE", []))
        allowed_tools = self._normalize_list(contract_data.get("TOOLS_ALLOWED", []))
        restrictions = self._normalize_list(contract_data.get("RESTRICTIONS", []))
        targets = self._normalize_list(contract_data.get("TARGET_SYSTEMS", []))
        objectives = self._normalize_list(contract_data.get("OBJECTIVES", []))

        # Determine restricted tools
        restricted = self._get_restricted_tools(restrictions)

        # Combine scope indicators
        scope_text = " ".join(scope + objectives + targets).lower()

        # Evaluate each tool
        for tool_name, tool_info in self.TOOL_DATABASE.items():
            # Skip if explicitly restricted
            if tool_name in restricted:
                continue

            # Check if tool matches scope
            matches_scope = any(
                use_case in scope_text
                for use_case in tool_info["use_cases"]
            )

            if matches_scope:
                # Determine if explicitly allowed
                allowed_by_contract = self._is_tool_allowed(
                    tool_name,
                    allowed_tools
                )

                # Calculate priority
                priority = self._calculate_priority(
                    tool_name,
                    tool_info,
                    scope_text,
                    allowed_by_contract
                )

                # Generate reasoning
                reason = self._generate_reason(
                    tool_name,
                    tool_info,
                    scope_text,
                    allowed_by_contract
                )

                recommendations.append(ToolRecommendation(
                    name=tool_name,
                    category=tool_info["category"],
                    priority=priority,
                    reason=reason,
                    allowed_by_contract=allowed_by_contract
                ))

        # Sort by priority (lower number = higher priority)
        recommendations.sort(key=lambda x: (x.priority, x.name))

        return recommendations

    def _normalize_list(self, data: any) -> List[str]:
        """Normalize data to list of strings."""
        if isinstance(data, list):
            return [str(item).lower() for item in data]
        elif isinstance(data, str):
            return [data.lower()]
        return []

    def _get_restricted_tools(self, restrictions: List[str]) -> List[str]:
        """Get list of restricted tools based on contract restrictions."""
        restricted = []

        for restriction in restrictions:
            restriction_lower = restriction.lower()
            for keyword, tools in self.RESTRICTED_TOOLS.items():
                if keyword in restriction_lower:
                    restricted.extend(tools)

        return list(set(restricted))

    def _is_tool_allowed(self, tool_name: str, allowed_tools: List[str]) -> bool:
        """Check if tool is explicitly allowed in contract."""
        if not allowed_tools or "not specified" in allowed_tools:
            return False

        tool_name_clean = tool_name.lower().replace("-", " ")

        for allowed in allowed_tools:
            allowed_clean = allowed.lower().replace("-", " ")
            if tool_name_clean in allowed_clean or allowed_clean in tool_name_clean:
                return True

        return False

    def _calculate_priority(
        self,
        tool_name: str,
        tool_info: Dict,
        scope_text: str,
        allowed_by_contract: bool
    ) -> int:
        """Calculate tool priority (1=critical, 5=optional)."""
        # Explicitly allowed = highest priority
        if allowed_by_contract:
            return 1

        # Critical tools for common scenarios
        critical_tools = ["nmap", "burp-suite", "metasploit"]
        if tool_name in critical_tools:
            return 2

        # Strong scope match
        match_count = sum(
            1 for use_case in tool_info["use_cases"]
            if use_case in scope_text
        )

        if match_count >= 3:
            return 2
        elif match_count >= 2:
            return 3
        elif match_count >= 1:
            return 4
        else:
            return 5

    def _generate_reason(
        self,
        tool_name: str,
        tool_info: Dict,
        scope_text: str,
        allowed_by_contract: bool
    ) -> str:
        """Generate reasoning for tool recommendation."""
        if allowed_by_contract:
            return f"Explicitly authorized in contract. {tool_info['description']}"

        # Find matching use cases
        matches = [
            use_case for use_case in tool_info["use_cases"]
            if use_case in scope_text
        ]

        if matches:
            return f"Recommended for {', '.join(matches[:2])}. {tool_info['description']}"

        return tool_info['description']

    def format_recommendations(
        self,
        recommendations: List[ToolRecommendation],
        max_tools: int = 20
    ) -> str:
        """Format recommendations as readable text."""
        output = []
        output.append("=" * 70)
        output.append("GhostAI - Tool Chain Recommendations")
        output.append("=" * 70)

        # Group by priority
        by_priority = {}
        for rec in recommendations[:max_tools]:
            if rec.priority not in by_priority:
                by_priority[rec.priority] = []
            by_priority[rec.priority].append(rec)

        priority_labels = {
            1: "CRITICAL (Explicitly Authorized)",
            2: "HIGH PRIORITY",
            3: "RECOMMENDED",
            4: "OPTIONAL",
            5: "AVAILABLE"
        }

        for priority in sorted(by_priority.keys()):
            output.append(f"\n{priority_labels.get(priority, 'TOOLS')}:")
            output.append("-" * 70)

            for rec in by_priority[priority]:
                status = "✓ AUTHORIZED" if rec.allowed_by_contract else "  suggested"
                output.append(f"\n[{status}] {rec.name}")
                output.append(f"  Category: {rec.category}")
                output.append(f"  Reason: {rec.reason}")

        output.append("\n" + "=" * 70)
        return "\n".join(output)

    def to_json(self, recommendations: List[ToolRecommendation]) -> str:
        """Convert recommendations to JSON."""
        data = [
            {
                "name": rec.name,
                "category": rec.category,
                "priority": rec.priority,
                "reason": rec.reason,
                "allowed_by_contract": rec.allowed_by_contract
            }
            for rec in recommendations
        ]
        return json.dumps(data, indent=2)


def test_recommendation_engine():
    """Test recommendation engine."""
    print("=" * 70)
    print("GhostAI - Recommendation Engine Test")
    print("=" * 70)

    # Sample contract data
    sample_data = {
        "TARGET_SYSTEMS": ["https://example.com", "192.168.1.0/24", "api.example.com"],
        "SCOPE": ["Web application", "Internal network", "API security"],
        "TOOLS_ALLOWED": ["Nmap", "Burp Suite", "SQLMap", "Metasploit"],
        "RESTRICTIONS": ["No DoS attacks", "No social engineering"],
        "TIMELINE": "2 weeks",
        "LEGAL_BOUNDARIES": ["Written authorization", "NDA"]
    }

    # Initialize engine
    engine = RecommendationEngine()

    # Generate recommendations
    print("\n[TEST] Generating tool recommendations...\n")
    recommendations = engine.recommend(sample_data)

    # Display formatted output
    print(engine.format_recommendations(recommendations, max_tools=15))

    # Display JSON
    print("\n[JSON OUTPUT]")
    print(engine.to_json(recommendations[:10]))

    print("\n✓ Test complete")


if __name__ == "__main__":
    test_recommendation_engine()
