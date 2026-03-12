#!/usr/bin/env python3
"""
GhostAI - Ghost Discovery System
Find ghosts. Search. Browse. Discover rivals. Build your network.
"""

import sqlite3
from typing import List, Dict, Optional, Tuple
from ghost_profile import GhostProfile, GhostTier, Specialty, GhostProfileManager


class GhostDiscovery:
    """System for discovering and browsing ghosts."""

    def __init__(self, db_path: str = "ghost_social.db"):
        """
        Initialize discovery system.

        Args:
            db_path: Path to database
        """
        self.db_path = db_path
        self.profile_manager = GhostProfileManager(db_path)

    def search_by_tag(self, query: str) -> List[GhostProfile]:
        """
        Search ghosts by tag.

        Args:
            query: Search query (partial match)

        Returns:
            List of matching profiles
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM profiles
            WHERE ghost_tag LIKE ?
            ORDER BY tier_points DESC
            LIMIT 50
        """, (f"%{query}%",))

        rows = cursor.fetchall()
        conn.close()

        return [self.profile_manager._row_to_profile(row) for row in rows]

    def browse_by_tier(self, tier: GhostTier) -> List[GhostProfile]:
        """
        Browse ghosts by tier.

        Args:
            tier: Tier to browse

        Returns:
            List of ghosts in that tier
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM profiles
            WHERE tier_points >= ? AND tier_points < ?
            ORDER BY tier_points DESC
            LIMIT 100
        """, (tier.min_points, tier.max_points))

        rows = cursor.fetchall()
        conn.close()

        return [self.profile_manager._row_to_profile(row) for row in rows]

    def find_by_school(self, school: str) -> List[GhostProfile]:
        """
        Find ghosts from a specific school.

        Args:
            school: School name

        Returns:
            List of ghosts from that school
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM profiles
            WHERE school = ?
            ORDER BY tier_points DESC
        """, (school,))

        rows = cursor.fetchall()
        conn.close()

        return [self.profile_manager._row_to_profile(row) for row in rows]

    def find_by_specialty(self, specialty: Specialty) -> List[GhostProfile]:
        """
        Find ghosts with a specific specialty.

        Args:
            specialty: Specialty to search for

        Returns:
            List of ghosts with that specialty
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM profiles
            WHERE specialty = ? OR secondary_specialty = ?
            ORDER BY tier_points DESC
            LIMIT 100
        """, (specialty.name, specialty.name))

        rows = cursor.fetchall()
        conn.close()

        return [self.profile_manager._row_to_profile(row) for row in rows]

    def find_rivals(self, ghost_id: int, min_rivalry_level: int = 3) -> List[Tuple[GhostProfile, Dict]]:
        """
        Find rivals for a ghost.

        Args:
            ghost_id: Ghost to find rivals for
            min_rivalry_level: Minimum rivalry level

        Returns:
            List of (profile, rivalry_stats) tuples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Find rivalries
        cursor.execute("""
            SELECT * FROM rivalries
            WHERE (ghost1_id = ? OR ghost2_id = ?)
              AND rivalry_level >= ?
            ORDER BY rivalry_level DESC, total_matches DESC
        """, (ghost_id, ghost_id, min_rivalry_level))

        rows = cursor.fetchall()
        conn.close()

        rivals = []
        for row in rows:
            # Determine which ghost is the rival
            if row[0] == ghost_id:
                rival_id = row[1]
                your_wins = row[2]
                their_wins = row[3]
            else:
                rival_id = row[0]
                your_wins = row[3]
                their_wins = row[2]

            profile = self.profile_manager.get_profile_by_id(rival_id)
            if profile:
                rivalry_stats = {
                    "total_matches": row[4],
                    "your_wins": your_wins,
                    "their_wins": their_wins,
                    "rivalry_level": row[5],
                    "last_match": row[7]
                }
                rivals.append((profile, rivalry_stats))

        return rivals

    def get_trending_ghosts(self, limit: int = 10) -> List[GhostProfile]:
        """
        Get trending ghosts (most active recently).

        Args:
            limit: Number of ghosts to return

        Returns:
            List of trending ghosts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM profiles
            ORDER BY last_active DESC, followers DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [self.profile_manager._row_to_profile(row) for row in rows]

    def get_top_ghosts(self, limit: int = 25) -> List[GhostProfile]:
        """
        Get top ghosts by tier points.

        Args:
            limit: Number of ghosts to return

        Returns:
            List of top ghosts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM profiles
            ORDER BY tier_points DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [self.profile_manager._row_to_profile(row) for row in rows]

    def get_recommended_ghosts(self, ghost_id: int, limit: int = 10) -> List[GhostProfile]:
        """
        Get recommended ghosts based on similarity.

        Args:
            ghost_id: Ghost to get recommendations for
            limit: Number of recommendations

        Returns:
            List of recommended ghosts
        """
        profile = self.profile_manager.get_profile_by_id(ghost_id)
        if not profile:
            return []

        # Find ghosts with same school or specialty
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM profiles
            WHERE (school = ? OR specialty = ?)
              AND ghost_id != ?
              AND ABS(tier_points - ?) < 500
            ORDER BY RANDOM()
            LIMIT ?
        """, (profile.school, profile.specialty.name, ghost_id, profile.tier_points, limit))

        rows = cursor.fetchall()
        conn.close()

        return [self.profile_manager._row_to_profile(row) for row in rows]

    def display_search_results(self, results: List[GhostProfile], title: str = "SEARCH RESULTS"):
        """Display search results."""
        print("\n" + "="*70)
        print(title)
        print("="*70 + "\n")

        if not results:
            print("No ghosts found.")
        else:
            print(f"Found {len(results)} ghost(s)\n")

            for i, ghost in enumerate(results, 1):
                tier_emoji = self._get_tier_emoji(ghost.tier)
                school_str = f"🎓 {ghost.school}" if ghost.school else ""

                print(f"{i}. {tier_emoji} {ghost.ghost_tag}")
                print(f"   Tier: {ghost.tier.display_name} ({ghost.tier_points} pts)")
                print(f"   Record: {ghost.wins}W-{ghost.losses}L ({ghost.win_rate:.1f}%)")
                print(f"   {school_str}  🎯 {ghost.specialty.value}")
                print(f"   👥 {ghost.followers} followers")
                print()

        print("="*70)

    def display_rivals(self, rivals: List[Tuple[GhostProfile, Dict]]):
        """Display rivalry information."""
        print("\n" + "="*70)
        print("🔥 YOUR RIVALS")
        print("="*70 + "\n")

        if not rivals:
            print("No established rivalries yet. Go challenge some ghosts!")
        else:
            for profile, stats in rivals:
                rivalry_intensity = "🔥" * min(stats["rivalry_level"], 5)

                print(f"{rivalry_intensity} {profile.ghost_tag}")
                print(f"   Head-to-Head: {stats['your_wins']}-{stats['their_wins']} ({stats['total_matches']} matches)")

                if stats['your_wins'] > stats['their_wins']:
                    print(f"   Status: 🏆 You're winning this rivalry!")
                elif stats['your_wins'] < stats['their_wins']:
                    print(f"   Status: ⚔️ They're ahead. Time for revenge!")
                else:
                    print(f"   Status: ⚖️ Dead even. Next match decides it!")

                print(f"   Rivalry Level: {stats['rivalry_level']}/10")
                print()

        print("="*70)

    def _get_tier_emoji(self, tier: GhostTier) -> str:
        """Get emoji for tier."""
        tier_emojis = {
            GhostTier.CASPER: "👻",
            GhostTier.PHANTOM: "🌫️",
            GhostTier.SPECTER: "💀",
            GhostTier.WRAITH: "😈",
            GhostTier.POLTERGEIST: "👹",
            GhostTier.BANSHEE: "😱",
            GhostTier.JACKAL: "🏆"
        }
        return tier_emojis.get(tier, "👻")

    def display_leaderboard(self, limit: int = 25):
        """Display global leaderboard."""
        top_ghosts = self.get_top_ghosts(limit)

        print("\n" + "╔" + "═"*68 + "╗")
        print("║" + " "*23 + "GLOBAL LEADERBOARD" + " "*26 + "║")
        print("╚" + "═"*68 + "╝\n")

        for i, ghost in enumerate(top_ghosts, 1):
            tier_emoji = self._get_tier_emoji(ghost.tier)

            # Medal for top 3
            if i == 1:
                rank = "🥇"
            elif i == 2:
                rank = "🥈"
            elif i == 3:
                rank = "🥉"
            else:
                rank = f"{i:2d}."

            school_tag = f"[{ghost.school}]" if ghost.school else ""

            print(f"{rank} {tier_emoji} {ghost.ghost_tag:25s} {school_tag:15s}")
            print(f"     {ghost.tier.display_name:15s} {ghost.tier_points:5d} pts | "
                  f"{ghost.wins}W-{ghost.losses}L")
            print()

        print("="*70)


def demo_discovery():
    """Demonstrate discovery system."""
    print("\n" + "="*70)
    print("GHOST DISCOVERY SYSTEM - DEMO")
    print("="*70 + "\n")

    discovery = GhostDiscovery("demo_ghost_social.db")

    # Search by tag
    print("\n[Searching for 'Ghost'...]\n")
    results = discovery.search_by_tag("Ghost")
    discovery.display_search_results(results, "SEARCH: 'Ghost'")

    time.sleep(1)

    # Browse by tier
    print("\n[Browsing Phantom tier...]\n")
    results = discovery.browse_by_tier(GhostTier.PHANTOM)
    discovery.display_search_results(results, "TIER: Phantom")

    time.sleep(1)

    # Find by school
    print("\n[Finding MIT ghosts...]\n")
    results = discovery.find_by_school("MIT")
    discovery.display_search_results(results, "SCHOOL: MIT")

    time.sleep(1)

    # Find by specialty
    print("\n[Finding Web Exploitation experts...]\n")
    results = discovery.find_by_specialty(Specialty.WEB_EXPLOITATION)
    discovery.display_search_results(results, "SPECIALTY: Web Exploitation")

    time.sleep(1)

    # Leaderboard
    print("\n[Global Leaderboard...]\n")
    discovery.display_leaderboard(limit=10)

    time.sleep(1)

    # Find rivals
    print("\n[Finding rivals for Ghost #1...]\n")
    rivals = discovery.find_rivals(1, min_rivalry_level=1)
    discovery.display_rivals(rivals)

    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)


if __name__ == "__main__":
    import time
    demo_discovery()
