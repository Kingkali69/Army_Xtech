#!/usr/bin/env python3
"""
GhostAI Cross-Agent Synchronization
All agents share learned patterns - when Agent A succeeds, all agents benefit
"""

import json
import os
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path


class SharedKnowledge:
    """
    Centralized knowledge repository shared across all agents
    No agent reinvents the wheel
    """

    def __init__(self, storage_path: str = './data'):
        self.storage_path = storage_path
        self.patterns_db = os.path.join(storage_path, 'shared_patterns.json')
        self.sync_log = os.path.join(storage_path, 'sync_log.json')

        # Thread safety
        self._lock = threading.Lock()

        # In-memory cache
        self.patterns: Dict[str, Any] = {}
        self.last_sync_time = 0
        self.sync_interval = 5  # seconds

        # Ensure storage exists
        os.makedirs(storage_path, exist_ok=True)

        # Load existing knowledge
        self.load_patterns()

    def add_pattern(self, agent_id: str, pattern_type: str,
                   target_signature: str, tool_sequence: List[str],
                   success_rate: float, metadata: Dict[str, Any] = None):
        """
        Add a new pattern learned by an agent
        Immediately available to all other agents
        """
        with self._lock:
            pattern_id = f"{target_signature}::{'-'.join(tool_sequence)}"

            if pattern_id not in self.patterns:
                self.patterns[pattern_id] = {
                    'pattern_type': pattern_type,
                    'target_signature': target_signature,
                    'tool_sequence': tool_sequence,
                    'success_rate': success_rate,
                    'contributed_by': [agent_id],
                    'first_discovered': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'total_executions': 1,
                    'metadata': metadata or {}
                }
            else:
                # Update existing pattern
                pattern = self.patterns[pattern_id]
                if agent_id not in pattern['contributed_by']:
                    pattern['contributed_by'].append(agent_id)
                pattern['success_rate'] = success_rate
                pattern['last_updated'] = datetime.now().isoformat()
                pattern['total_executions'] += 1
                if metadata:
                    pattern['metadata'].update(metadata)

            # Save to disk
            self.save_patterns()

            # Log sync event
            self._log_sync_event(agent_id, 'pattern_added', pattern_id)

    def query_patterns(self, target_signature: str = None,
                      tool_name: str = None,
                      min_success_rate: float = 0.0,
                      max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Query the shared knowledge base
        Example: "How do we crack WPA2?" → returns learned sequences ranked by success
        """
        with self._lock:
            results = []

            for pattern_id, pattern in self.patterns.items():
                # Filter by target signature
                if target_signature and pattern['target_signature'] != target_signature:
                    continue

                # Filter by tool name
                if tool_name and tool_name not in pattern['tool_sequence']:
                    continue

                # Filter by success rate
                if pattern['success_rate'] < min_success_rate:
                    continue

                results.append({
                    'pattern_id': pattern_id,
                    'target': pattern['target_signature'],
                    'tools': pattern['tool_sequence'],
                    'success_rate': pattern['success_rate'],
                    'executions': pattern['total_executions'],
                    'discovered_by': pattern['contributed_by'][0],
                    'contributors': len(pattern['contributed_by']),
                    'last_updated': pattern['last_updated'],
                    'metadata': pattern.get('metadata', {})
                })

            # Sort by success rate, then by execution count
            results.sort(
                key=lambda x: (x['success_rate'], x['executions']),
                reverse=True
            )

            return results[:max_results]

    def semantic_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search through patterns
        Example: "crack WPA2" → finds patterns related to wireless attacks
        """
        query_lower = query.lower()
        keywords = set(query_lower.split())

        results = []

        with self._lock:
            for pattern_id, pattern in self.patterns.items():
                # Calculate relevance score
                score = 0

                # Check target signature
                target_words = set(pattern['target_signature'].lower().replace('+', ' ').split())
                score += len(keywords.intersection(target_words)) * 3

                # Check tool names
                for tool in pattern['tool_sequence']:
                    tool_words = set(tool.lower().split())
                    score += len(keywords.intersection(tool_words)) * 2

                # Check metadata
                metadata_str = json.dumps(pattern.get('metadata', {})).lower()
                for keyword in keywords:
                    if keyword in metadata_str:
                        score += 1

                if score > 0:
                    results.append({
                        'pattern_id': pattern_id,
                        'target': pattern['target_signature'],
                        'tools': pattern['tool_sequence'],
                        'success_rate': pattern['success_rate'],
                        'executions': pattern['total_executions'],
                        'relevance_score': score,
                        'contributors': len(pattern['contributed_by'])
                    })

        # Sort by relevance, then success rate
        results.sort(key=lambda x: (x['relevance_score'], x['success_rate']), reverse=True)

        return results[:max_results]

    def get_agent_contributions(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics about an agent's contributions to shared knowledge"""
        with self._lock:
            patterns_contributed = []
            total_patterns = 0

            for pattern_id, pattern in self.patterns.items():
                if agent_id in pattern['contributed_by']:
                    total_patterns += 1
                    if pattern['contributed_by'][0] == agent_id:  # First discoverer
                        patterns_contributed.append({
                            'pattern_id': pattern_id,
                            'target': pattern['target_signature'],
                            'tools': pattern['tool_sequence'],
                            'success_rate': pattern['success_rate']
                        })

            return {
                'agent_id': agent_id,
                'patterns_discovered': len(patterns_contributed),
                'patterns_contributed_to': total_patterns,
                'discoveries': patterns_contributed
            }

    def get_top_patterns(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get the most successful patterns across all agents"""
        with self._lock:
            all_patterns = [
                {
                    'target': p['target_signature'],
                    'tools': p['tool_sequence'],
                    'success_rate': p['success_rate'],
                    'executions': p['total_executions'],
                    'contributors': len(p['contributed_by'])
                }
                for p in self.patterns.values()
            ]

            all_patterns.sort(
                key=lambda x: (x['success_rate'], x['executions']),
                reverse=True
            )

            return all_patterns[:top_n]

    def sync_from_agent(self, agent_id: str, agent_patterns: List[Dict[str, Any]]):
        """
        Sync patterns from an agent to shared knowledge
        Called when an agent wants to share its learnings
        """
        synced_count = 0

        for pattern in agent_patterns:
            self.add_pattern(
                agent_id=agent_id,
                pattern_type=pattern.get('pattern_type', 'tool_sequence'),
                target_signature=pattern['target_signature'],
                tool_sequence=pattern['tool_sequence'],
                success_rate=pattern['success_rate'],
                metadata=pattern.get('metadata', {})
            )
            synced_count += 1

        self._log_sync_event(agent_id, 'bulk_sync', f"{synced_count} patterns")
        return synced_count

    def get_updates_since(self, timestamp: float) -> List[Dict[str, Any]]:
        """
        Get all patterns updated since a given timestamp
        Used by agents to stay synchronized
        """
        with self._lock:
            updates = []

            for pattern_id, pattern in self.patterns.items():
                # Parse ISO timestamp
                last_updated = datetime.fromisoformat(pattern['last_updated'])
                last_updated_ts = last_updated.timestamp()

                if last_updated_ts > timestamp:
                    updates.append({
                        'pattern_id': pattern_id,
                        'pattern': pattern
                    })

            return updates

    def _log_sync_event(self, agent_id: str, event_type: str, details: str):
        """Log synchronization events for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': agent_id,
            'event_type': event_type,
            'details': details
        }

        # Append to sync log
        try:
            if os.path.exists(self.sync_log):
                with open(self.sync_log, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {'events': []}

            log_data['events'].append(log_entry)

            # Keep only last 1000 events
            log_data['events'] = log_data['events'][-1000:]

            with open(self.sync_log, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"[!] Error logging sync event: {e}")

    def save_patterns(self):
        """Save patterns to disk"""
        data = {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'total_patterns': len(self.patterns),
            'patterns': self.patterns
        }

        with open(self.patterns_db, 'w') as f:
            json.dump(data, f, indent=2)

    def load_patterns(self):
        """Load patterns from disk"""
        if not os.path.exists(self.patterns_db):
            return

        try:
            with open(self.patterns_db, 'r') as f:
                data = json.load(f)

            self.patterns = data.get('patterns', {})
            self.last_sync_time = time.time()
        except Exception as e:
            print(f"[!] Error loading shared patterns: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the shared knowledge base"""
        with self._lock:
            total_patterns = len(self.patterns)
            total_executions = sum(p['total_executions'] for p in self.patterns.values())

            # Count unique agents
            unique_agents = set()
            for pattern in self.patterns.values():
                unique_agents.update(pattern['contributed_by'])

            # Average success rate
            avg_success = sum(p['success_rate'] for p in self.patterns.values()) / total_patterns if total_patterns > 0 else 0

            # Target type distribution
            target_types = {}
            for pattern in self.patterns.values():
                target = pattern['target_signature']
                target_types[target] = target_types.get(target, 0) + 1

            return {
                'total_patterns': total_patterns,
                'total_executions': total_executions,
                'contributing_agents': len(unique_agents),
                'avg_success_rate': round(avg_success, 2),
                'target_types': len(target_types),
                'most_common_targets': sorted(
                    target_types.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            }


class AgentSyncClient:
    """
    Client interface for individual agents to sync with shared knowledge
    """

    def __init__(self, agent_id: str, storage_path: str = './data'):
        self.agent_id = agent_id
        self.shared_knowledge = SharedKnowledge(storage_path)
        self.last_sync = 0

    def share_pattern(self, target_signature: str, tool_sequence: List[str],
                     success_rate: float, metadata: Dict[str, Any] = None):
        """Share a learned pattern with all other agents"""
        self.shared_knowledge.add_pattern(
            self.agent_id,
            'tool_sequence',
            target_signature,
            tool_sequence,
            success_rate,
            metadata
        )

    def get_recommendations(self, target_signature: str,
                           max_results: int = 5) -> List[Dict[str, Any]]:
        """Get recommendations from shared knowledge"""
        return self.shared_knowledge.query_patterns(
            target_signature=target_signature,
            max_results=max_results
        )

    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search shared knowledge base"""
        return self.shared_knowledge.semantic_search(query)

    def sync_updates(self) -> int:
        """
        Sync updates from shared knowledge
        Returns number of new patterns received
        """
        updates = self.shared_knowledge.get_updates_since(self.last_sync)
        self.last_sync = time.time()
        return len(updates)

    def get_my_contributions(self) -> Dict[str, Any]:
        """Get my contribution statistics"""
        return self.shared_knowledge.get_agent_contributions(self.agent_id)


# Global instance
_shared_knowledge = None

def get_shared_knowledge(storage_path: str = './data') -> SharedKnowledge:
    """Get or create global shared knowledge instance"""
    global _shared_knowledge
    if _shared_knowledge is None:
        _shared_knowledge = SharedKnowledge(storage_path)
    return _shared_knowledge


if __name__ == '__main__':
    # Demo usage
    print("GhostAI Cross-Agent Synchronization - Demo")
    print("=" * 60)

    # Create multiple agent clients
    agent1 = AgentSyncClient('agent_kali_001', './data')
    agent2 = AgentSyncClient('agent_windows_002', './data')
    agent3 = AgentSyncClient('agent_android_003', './data')

    print("\n[*] Agent 1 discovers a pattern for Windows+SMB...")
    agent1.share_pattern(
        target_signature='Windows+SMB',
        tool_sequence=['nmap', 'metasploit', 'mimikatz'],
        success_rate=92.5,
        metadata={'vulnerabilities': ['EternalBlue', 'MS17-010']}
    )

    print("[*] Agent 2 discovers a pattern for Web+SQL...")
    agent2.share_pattern(
        target_signature='Web+SQL',
        tool_sequence=['sqlmap', 'burp'],
        success_rate=87.3,
        metadata={'vulnerabilities': ['SQL Injection']}
    )

    print("[*] Agent 3 discovers a pattern for Linux+SSH...")
    agent3.share_pattern(
        target_signature='Linux+SSH',
        tool_sequence=['hydra', 'nmap'],
        success_rate=76.8,
        metadata={'vulnerabilities': ['Weak credentials']}
    )

    print("\n[✓] All patterns shared across agents\n")

    # Now Agent 1 can benefit from Agent 2's discovery
    print("=" * 60)
    print("[*] Agent 1 queries: How to attack Web+SQL?")
    print("=" * 60)
    recommendations = agent1.get_recommendations('Web+SQL')

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. Target: {rec['target']}")
        print(f"   Tools: {' → '.join(rec['tools'])}")
        print(f"   Success Rate: {rec['success_rate']:.1f}%")
        print(f"   Discovered by: {rec['discovered_by']}")
        print(f"   Contributors: {rec['contributors']} agent(s)")

    # Semantic search
    print("\n" + "=" * 60)
    print("[*] Agent 2 searches: 'crack Windows passwords'")
    print("=" * 60)
    results = agent2.search_knowledge('crack Windows passwords')

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Target: {result['target']}")
        print(f"   Tools: {' → '.join(result['tools'])}")
        print(f"   Success Rate: {result['success_rate']:.1f}%")
        print(f"   Relevance: {result['relevance_score']}")

    # Statistics
    print("\n" + "=" * 60)
    print("[*] Shared Knowledge Statistics:")
    print("=" * 60)
    stats = get_shared_knowledge('./data').get_statistics()
    print(f"\nTotal Patterns: {stats['total_patterns']}")
    print(f"Total Executions: {stats['total_executions']}")
    print(f"Contributing Agents: {stats['contributing_agents']}")
    print(f"Avg Success Rate: {stats['avg_success_rate']:.1f}%")
    print(f"\nMost Common Targets:")
    for target, count in stats['most_common_targets']:
        print(f"  • {target}: {count} pattern(s)")

    # Agent contributions
    print("\n" + "=" * 60)
    print("[*] Agent 1 Contributions:")
    print("=" * 60)
    contrib = agent1.get_my_contributions()
    print(f"\nPatterns Discovered: {contrib['patterns_discovered']}")
    print(f"Patterns Contributed To: {contrib['patterns_contributed_to']}")

    print("\n[✓] No agent reinvents the wheel!")
    print("[✓] Shared knowledge saved to: ./data/shared_patterns.json")
