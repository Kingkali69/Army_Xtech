#!/usr/bin/env python3
"""
GhostAI - Integration Layer
Main entry point for contract parsing and tool recommendation.
"""

import sys
import argparse
from pathlib import Path
from contract_parser import ContractParser
from recommendation_engine import RecommendationEngine


class GhostAI:
    """GhostAI - Contract Intelligence and Tool Recommendation System."""

    BANNER = """
    ╔════════════════════════════════════════════════════════════════╗
    ║                         GhostAI v1.0                          ║
    ║              Contract Parser & Tool Recommender               ║
    ║                                                               ║
    ║  Powered by Mistral 7B - Local Inference                     ║
    ╚════════════════════════════════════════════════════════════════╝
    """

    def __init__(self, model_path=None):
        """
        Initialize GhostAI system.

        Args:
            model_path: Optional explicit path to Mistral model
        """
        self.model_path = model_path
        self.parser = None
        self.recommender = None

    def process_contract(
        self,
        contract_text: str = None,
        contract_file: str = None,
        output_json: str = None,
        show_recommendations: bool = True
    ):
        """
        Process contract and generate recommendations.

        Args:
            contract_text: Raw contract text (if not reading from file)
            contract_file: Path to contract file
            output_json: Optional path to save JSON output
            show_recommendations: Whether to show tool recommendations
        """
        print(self.BANNER)

        # Initialize components
        print("\n[1/4] Initializing GhostAI...")
        self.parser = ContractParser(self.model_path)
        self.recommender = RecommendationEngine()

        # Parse contract
        print("\n[2/4] Parsing contract...")
        if contract_file:
            contract_data = self.parser.parse_file(contract_file)
        elif contract_text:
            contract_data = self.parser.parse(contract_text)
        else:
            raise ValueError("Must provide either contract_text or contract_file")

        # Display contract intelligence
        print("\n[3/4] Contract Intelligence Extracted")
        print("=" * 70)
        self._display_contract_data(contract_data)

        # Save JSON if requested
        if output_json:
            self.parser.save_json(contract_data, output_json)

        # Generate recommendations
        if show_recommendations:
            print("\n[4/4] Generating Tool Recommendations...")
            recommendations = self.recommender.recommend(contract_data)
            print("\n" + self.recommender.format_recommendations(recommendations))

            # Save recommendations JSON
            if output_json:
                rec_path = output_json.replace('.json', '_recommendations.json')
                with open(rec_path, 'w') as f:
                    f.write(self.recommender.to_json(recommendations))
                print(f"\n[INFO] Recommendations saved to: {rec_path}")

        print("\n✓ GhostAI processing complete\n")

        return contract_data

    def _display_contract_data(self, data: dict):
        """Display contract data in readable format."""
        sections = [
            ("TARGET SYSTEMS", "TARGET_SYSTEMS"),
            ("SCOPE", "SCOPE"),
            ("AUTHORIZED TOOLS", "TOOLS_ALLOWED"),
            ("RESTRICTIONS", "RESTRICTIONS"),
            ("TIMELINE", "TIMELINE"),
            ("LEGAL BOUNDARIES", "LEGAL_BOUNDARIES")
        ]

        for label, key in sections:
            value = data.get(key, "Not specified")

            print(f"\n{label}:")
            print("-" * 70)

            if isinstance(value, list):
                if value and value[0] != "Not specified":
                    for item in value:
                        print(f"  • {item}")
                else:
                    print("  Not specified")
            else:
                print(f"  {value}")

    def interactive_mode(self):
        """Run GhostAI in interactive mode."""
        print(self.BANNER)
        print("\n[INTERACTIVE MODE]")
        print("Paste your penetration test contract below.")
        print("Press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows) when done.\n")

        # Read multi-line input
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass

        contract_text = "\n".join(lines)

        if not contract_text.strip():
            print("\n✗ No contract text provided")
            return

        # Process contract
        self.process_contract(contract_text=contract_text)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GhostAI - Penetration Test Contract Parser & Tool Recommender",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (paste contract)
  python integration.py

  # Process contract file
  python integration.py -f contract.txt

  # Process and save JSON output
  python integration.py -f contract.txt -o output.json

  # Specify Mistral model path
  python integration.py -f contract.txt -m ~/models/mistral-7b
        """
    )

    parser.add_argument(
        '-f', '--file',
        help='Contract file to process',
        type=str
    )

    parser.add_argument(
        '-o', '--output',
        help='Output JSON file path',
        type=str
    )

    parser.add_argument(
        '-m', '--model',
        help='Path to Mistral 7B model',
        type=str
    )

    parser.add_argument(
        '--no-recommendations',
        help='Skip tool recommendations',
        action='store_true'
    )

    parser.add_argument(
        '--test',
        help='Run with test contract',
        action='store_true'
    )

    args = parser.parse_args()

    # Initialize GhostAI
    ghostai = GhostAI(model_path=args.model)

    # Test mode
    if args.test:
        test_contract = """
        PENETRATION TESTING AGREEMENT

        TARGET SYSTEMS:
        - Web Application: https://example.com
        - Internal Network: 192.168.1.0/24
        - API: api.example.com

        SCOPE: Web application security testing, internal network assessment, API testing

        AUTHORIZED TOOLS: Nmap, Burp Suite Professional, SQLMap, Metasploit Framework

        RESTRICTIONS:
        - NO denial of service attacks
        - NO social engineering
        - Testing only during business hours

        TIMELINE: January 15-30, 2024 (2 weeks)

        LEGAL: Written authorization provided, NDA signed, responsible disclosure required
        """

        ghostai.process_contract(
            contract_text=test_contract,
            output_json=args.output,
            show_recommendations=not args.no_recommendations
        )

    # File mode
    elif args.file:
        if not Path(args.file).exists():
            print(f"✗ Error: File not found: {args.file}")
            sys.exit(1)

        ghostai.process_contract(
            contract_file=args.file,
            output_json=args.output,
            show_recommendations=not args.no_recommendations
        )

    # Interactive mode
    else:
        ghostai.interactive_mode()


if __name__ == "__main__":
    main()
