#!/usr/bin/env python3
"""
GhostAI - Contract Parser
Extracts penetration test intelligence from contracts using Mistral 7B.
"""

import json
import re
from typing import Dict, List, Optional
from mistral_local import MistralLocal


class ContractParser:
    """Parse penetration test contracts and extract structured intelligence."""

    EXTRACTION_TEMPLATE = """
    Analyze the following penetration test contract and extract key information.

    CONTRACT TEXT:
    {contract_text}

    Extract the following information in JSON format:
    {{
        "TARGET_SYSTEMS": ["list of systems, IPs, domains to test"],
        "SCOPE": ["what areas/systems are in scope"],
        "TOOLS_ALLOWED": ["which security tools are permitted"],
        "RESTRICTIONS": ["what is forbidden or restricted"],
        "TIMELINE": "testing period/duration",
        "LEGAL_BOUNDARIES": ["legal and ethical constraints"],
        "OBJECTIVES": ["testing goals and objectives"],
        "DELIVERABLES": ["expected outputs/reports"]
    }}

    Respond ONLY with valid JSON. Be precise and extract actual details from the contract.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize contract parser.

        Args:
            model_path: Optional explicit path to Mistral model
        """
        print("[ContractParser] Initializing...")
        self.mistral = MistralLocal(model_path)
        print("[ContractParser] Ready")

    def parse(self, contract_text: str) -> Dict:
        """
        Parse contract and extract intelligence.

        Args:
            contract_text: Raw contract text

        Returns:
            Structured contract intelligence as dict
        """
        # Clean contract text
        contract_text = self._clean_text(contract_text)

        # Build prompt
        prompt = self.EXTRACTION_TEMPLATE.format(contract_text=contract_text)

        # Generate extraction
        print("[ContractParser] Analyzing contract...")
        response = self.mistral.generate(
            prompt,
            temperature=0.3,  # Low temperature for consistency
            max_tokens=2048
        )

        # Extract JSON
        data = self.mistral.extract_json(response)

        if not data:
            print("[ContractParser] WARNING: Could not extract JSON, using raw response")
            # Attempt to build structured data from text
            data = self._fallback_parse(response)

        # Validate and clean data
        data = self._validate_data(data)

        return data

    def parse_file(self, file_path: str) -> Dict:
        """
        Parse contract from file.

        Args:
            file_path: Path to contract file

        Returns:
            Structured contract intelligence
        """
        print(f"[ContractParser] Reading contract from: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            contract_text = f.read()

        return self.parse(contract_text)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize contract text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might confuse the model
        text = text.strip()
        return text

    def _validate_data(self, data: Dict) -> Dict:
        """Validate and ensure all required fields exist."""
        required_fields = [
            "TARGET_SYSTEMS",
            "SCOPE",
            "TOOLS_ALLOWED",
            "RESTRICTIONS",
            "TIMELINE",
            "LEGAL_BOUNDARIES"
        ]

        optional_fields = [
            "OBJECTIVES",
            "DELIVERABLES",
            "CONTACT_INFO",
            "METHODOLOGY"
        ]

        validated = {}

        # Ensure required fields
        for field in required_fields:
            if field in data:
                validated[field] = data[field]
            else:
                validated[field] = [] if field != "TIMELINE" else "Not specified"

        # Add optional fields if present
        for field in optional_fields:
            if field in data:
                validated[field] = data[field]

        return validated

    def _fallback_parse(self, text: str) -> Dict:
        """Fallback parser if JSON extraction fails."""
        print("[ContractParser] Using fallback text parser...")

        data = {
            "TARGET_SYSTEMS": self._extract_targets(text),
            "SCOPE": self._extract_scope(text),
            "TOOLS_ALLOWED": self._extract_tools(text),
            "RESTRICTIONS": self._extract_restrictions(text),
            "TIMELINE": self._extract_timeline(text),
            "LEGAL_BOUNDARIES": self._extract_legal(text)
        }

        return data

    def _extract_targets(self, text: str) -> List[str]:
        """Extract target systems from text."""
        targets = []

        # Look for IPs
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b'
        targets.extend(re.findall(ip_pattern, text))

        # Look for domains
        domain_pattern = r'\b(?:https?://)?(?:www\.)?([a-z0-9-]+\.[a-z]{2,})\b'
        targets.extend(re.findall(domain_pattern, text, re.IGNORECASE))

        return list(set(targets)) if targets else ["Not specified"]

    def _extract_scope(self, text: str) -> List[str]:
        """Extract scope from text."""
        scope_keywords = ["web application", "network", "mobile app", "api", "infrastructure"]
        scope = []

        for keyword in scope_keywords:
            if keyword.lower() in text.lower():
                scope.append(keyword)

        return scope if scope else ["Not specified"]

    def _extract_tools(self, text: str) -> List[str]:
        """Extract allowed tools from text."""
        tool_names = [
            "nmap", "burp suite", "metasploit", "sqlmap", "nikto",
            "wireshark", "john", "hashcat", "hydra", "aircrack"
        ]

        tools = []
        text_lower = text.lower()

        for tool in tool_names:
            if tool in text_lower:
                tools.append(tool.title())

        return tools if tools else ["Not specified"]

    def _extract_restrictions(self, text: str) -> List[str]:
        """Extract restrictions from text."""
        restriction_keywords = [
            "no dos", "no denial of service", "no exfiltration",
            "no data destruction", "no social engineering"
        ]

        restrictions = []
        text_lower = text.lower()

        for keyword in restriction_keywords:
            if keyword in text_lower:
                restrictions.append(keyword)

        return restrictions if restrictions else ["Not specified"]

    def _extract_timeline(self, text: str) -> str:
        """Extract timeline from text."""
        # Look for date ranges
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:-\d{1,2})?,?\s+\d{4}\b'
        dates = re.findall(date_pattern, text, re.IGNORECASE)

        if dates:
            return ", ".join(dates)

        # Look for duration
        duration_pattern = r'\b(\d+)\s+(day|week|month)s?\b'
        durations = re.findall(duration_pattern, text, re.IGNORECASE)

        if durations:
            return f"{durations[0][0]} {durations[0][1]}s"

        return "Not specified"

    def _extract_legal(self, text: str) -> List[str]:
        """Extract legal boundaries from text."""
        legal_keywords = [
            "written authorization", "legal authorization", "nda", "confidentiality",
            "report findings", "responsible disclosure"
        ]

        legal = []
        text_lower = text.lower()

        for keyword in legal_keywords:
            if keyword in text_lower:
                legal.append(keyword)

        return legal if legal else ["Not specified"]

    def to_json(self, data: Dict, pretty: bool = True) -> str:
        """Convert parsed data to JSON string."""
        if pretty:
            return json.dumps(data, indent=2, sort_keys=True)
        return json.dumps(data)

    def save_json(self, data: Dict, output_path: str):
        """Save parsed data to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, sort_keys=True)

        print(f"[ContractParser] Saved to: {output_path}")


def test_contract_parser():
    """Test contract parser with sample contract."""
    print("=" * 60)
    print("GhostAI - Contract Parser Test")
    print("=" * 60)

    # Sample contract
    sample_contract = """
    PENETRATION TESTING AGREEMENT

    This agreement authorizes security testing of the following systems:

    TARGET SYSTEMS:
    - Web Application: https://example.com
    - Internal Network: 192.168.1.0/24
    - API Endpoints: api.example.com

    SCOPE:
    The penetration test will cover:
    1. Web application security assessment
    2. Network infrastructure testing
    3. API security evaluation

    AUTHORIZED TOOLS:
    - Nmap for network scanning
    - Burp Suite Professional for web testing
    - SQLMap for SQL injection testing
    - Metasploit Framework for exploitation

    RESTRICTIONS:
    - NO denial of service (DoS) attacks
    - NO data exfiltration or destruction
    - NO social engineering of employees
    - Testing only during business hours (9 AM - 5 PM EST)

    TIMELINE:
    Testing Period: January 15 - January 30, 2024
    Duration: 2 weeks

    LEGAL REQUIREMENTS:
    - Written authorization provided by client
    - All findings covered under NDA
    - Report findings only to designated client contact
    - Follow responsible disclosure practices

    DELIVERABLES:
    - Executive summary report
    - Technical findings report
    - Remediation recommendations
    """

    try:
        # Initialize parser
        parser = ContractParser()

        # Parse contract
        print("\n[TEST] Parsing sample contract...\n")
        result = parser.parse(sample_contract)

        # Display results
        print("\n[PARSED CONTRACT INTELLIGENCE]")
        print("=" * 60)
        print(parser.to_json(result))
        print("=" * 60)

        # Test JSON save
        parser.save_json(result, "/tmp/ghostai_test_contract.json")

        print("\n✓ Test complete")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_contract_parser()
