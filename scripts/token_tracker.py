"""Track and analyze LLM token usage.

Monitors token consumption across sessions and identifies optimization opportunities.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt


@dataclass
class TokenEntry:
    """Single token usage entry."""

    timestamp: datetime
    model: str
    tokens_in: int
    tokens_out: int
    total_tokens: int
    agent: str
    task_type: str
    cached: bool = False


class TokenTracker:
    """Track and analyze LLM token usage.

    Features:
    - Session-based tracking
    - Cache hit/miss tracking
    - Per-agent statistics
    - Trend analysis
    - Optimization recommendations

    Usage:
        tracker = TokenTracker()
        tracker.log_usage(
            model='gpt-4',
            tokens_in=100,
            tokens_out=200,
            agent='builder',
            task_type='implement'
        )

        stats = tracker.get_statistics()
        print(stats)
    """

    def __init__(self, data_path: str = ".brain/token_usage.json"):
        """Initialize token tracker.

        Args:
            data_path: Path to usage data file.
        """
        self.data_path = Path(data_path)
        self.entries: list[TokenEntry] = []

        if self.data_path.exists():
            self._load()

    def _load(self) -> None:
        """Load existing token data."""
        try:
            with open(self.data_path, encoding="utf-8") as f:
                data = json.load(f)

            self.entries = [
                TokenEntry(
                    timestamp=datetime.fromisoformat(e["timestamp"]),
                    model=e["model"],
                    tokens_in=e["tokens_in"],
                    tokens_out=e["tokens_out"],
                    total_tokens=e["total_tokens"],
                    agent=e["agent"],
                    task_type=e["task_type"],
                    cached=e.get("cached", False),
                )
                for e in data.get("entries", [])
            ]
        except (json.JSONDecodeError, KeyError, TypeError, FileNotFoundError):
            self.entries = []

    def log_usage(
        self,
        model: str,
        tokens_in: int,
        tokens_out: int,
        agent: str,
        task_type: str,
        cached: bool = False,
    ) -> None:
        """Log token usage entry.

        Args:
            model: Model used.
            tokens_in: Input tokens.
            tokens_out: Output tokens.
            agent: Agent name.
            task_type: Task type (implement, fix, research, etc.).
            cached: Whether response was from cache.
        """
        entry = TokenEntry(
            timestamp=datetime.now(),
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            total_tokens=tokens_in + tokens_out,
            agent=agent,
            task_type=task_type,
            cached=cached,
        )

        self.entries.append(entry)
        self._save()

    def _save(self) -> None:
        """Save token data to file."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "entries": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "model": e.model,
                    "tokens_in": e.tokens_in,
                    "tokens_out": e.tokens_out,
                    "total_tokens": e.total_tokens,
                    "agent": e.agent,
                    "task_type": e.task_type,
                    "cached": e.cached,
                }
                for e in self.entries[-1000:]
            ]
        }

        data_json = json.dumps(data, indent=2)
        with open(self.data_path, "w", encoding="utf-8") as f:
            f.write(data_json)

    def get_statistics(self, days: int = 7) -> dict[str, any]:
        """Calculate usage statistics.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary with statistics.
        """
        if not self.entries:
            return {}

        cutoff = datetime.now() - timedelta(days=days)
        recent_entries = [e for e in self.entries if e.timestamp > cutoff]

        total_tokens = sum(e.total_tokens for e in recent_entries)
        cached_entries = [e for e in recent_entries if e.cached]
        cached_tokens = sum(e.total_tokens for e in cached_entries)

        agent_stats: dict[str, dict[str, int]] = {}
        for entry in recent_entries:
            if entry.agent not in agent_stats:
                agent_stats[entry.agent] = {"count": 0, "tokens": 0}
            agent_stats[entry.agent]["count"] += 1
            agent_stats[entry.agent]["tokens"] += entry.total_tokens

        task_type_stats: dict[str, dict[str, int]] = {}
        for entry in recent_entries:
            if entry.task_type not in task_type_stats:
                task_type_stats[entry.task_type] = {"count": 0, "tokens": 0}
            task_type_stats[entry.task_type]["count"] += 1
            task_type_stats[entry.task_type]["tokens"] += entry.total_tokens

        model_stats: dict[str, int] = {}
        for entry in recent_entries:
            if entry.model not in model_stats:
                model_stats[entry.model] = 0
            model_stats[entry.model] += entry.total_tokens

        return {
            "period_days": days,
            "total_entries": len(recent_entries),
            "total_tokens": total_tokens,
            "average_tokens_per_entry": total_tokens / len(recent_entries) if recent_entries else 0,
            "cache_hit_rate": len(cached_entries) / len(recent_entries) if recent_entries else 0,
            "cached_tokens_saved": cached_tokens,
            "agent_stats": agent_stats,
            "task_type_stats": task_type_stats,
            "model_stats": model_stats,
            "top_agents": sorted(agent_stats.items(), key=lambda x: x[1]["tokens"], reverse=True)[
                :5
            ],
            "top_task_types": sorted(
                task_type_stats.items(), key=lambda x: x[1]["tokens"], reverse=True
            )[:5],
        }

    def generate_report(self, days: int = 7) -> str:
        """Generate usage report.

        Args:
            days: Number of days to analyze.

        Returns:
            Formatted report string.
        """
        stats = self.get_statistics(days)

        lines = [
            "# Token Usage Report",
            "",
            f"**Period**: Last {days} days",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Summary",
            "",
            f"- **Total Tokens**: {stats.get('total_tokens', 0):,}",
            f"- **Total Entries**: {stats.get('total_entries', 0)}",
            f"- **Average/Entry**: {stats.get('average_tokens_per_entry', 0):.0f}",
            f"- **Cache Hit Rate**: {stats.get('cache_hit_rate', 0) * 100:.1f}%",
            f"- **Tokens Saved by Cache**: {stats.get('cached_tokens_saved', 0):,}",
            "",
            "## Top 5 Agents by Token Usage",
            "",
        ]

        for agent, data in stats.get("top_agents", []):
            lines.append(f"| {agent} | {data['tokens']:,} tokens | {data['count']} calls |")

        lines.extend(
            [
                "",
                "## Top 5 Task Types by Token Usage",
                "",
            ]
        )

        for task_type, data in stats.get("top_task_types", []):
            lines.append(f"| {task_type} | {data['tokens']:,} tokens | {data['count']} calls |")

        lines.extend(
            [
                "",
                "## Optimization Recommendations",
                "",
            ]
        )

        recommendations = self._get_recommendations(stats)
        lines.extend(recommendations)

        return "\n".join(lines)

    def _get_recommendations(self, stats: dict) -> list[str]:
        """Generate optimization recommendations.

        Args:
            stats: Usage statistics.

        Returns:
            List of recommendation strings.
        """
        recommendations = []

        cache_hit_rate = stats.get("cache_hit_rate", 0)
        if cache_hit_rate < 0.3:
            recommendations.append(
                "- [LOW CACHE HIT] Cache hit rate is low. Consider enabling response caching."
            )

        avg_tokens = stats.get("average_tokens_per_entry", 0)
        if avg_tokens > 5000:
            recommendations.append(
                "- [HIGH TOKEN USAGE] Average tokens per entry is high. "
                "Consider context window management or prompt compression."
            )

        agent_stats = stats.get("agent_stats", {})
        if len(agent_stats) > 5:
            recommendations.append(
                f"- [MANY AGENTS] {len(agent_stats)} different agents used. "
                "Consider consolidating agent types."
            )

        model_stats = stats.get("model_stats", {})
        if len(model_stats) > 2:
            recommendations.append(
                f"- [MANY MODELS] {len(model_stats)} different models used. "
                "Consider standardizing on one model."
            )

        if not recommendations:
            recommendations.append("- Token usage is optimal. No recommendations.")

        return recommendations

    def plot_trends(self, days: int = 30, output_path: str = ".brain/token_trends.png") -> None:
        """Plot token usage trends.

        Args:
            days: Number of days to plot.
            output_path: Path to save plot.
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_entries = [e for e in self.entries if e.timestamp > cutoff]

        if not recent_entries:
            return

        entries_by_day: dict[str, int] = {}

        for entry in recent_entries:
            day_key = entry.timestamp.strftime("%Y-%m-%d")
            entries_by_day[day_key] = entries_by_day.get(day_key, 0) + entry.total_tokens

        dates = sorted(entries_by_day.keys())
        tokens = [entries_by_day[d] for d in dates]

        plt.figure(figsize=(12, 6))
        plt.plot(range(len(dates)), tokens, marker="o")
        plt.xticks(range(len(dates)), dates, rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Total Tokens")
        plt.title(f"Token Usage Trends (Last {days} Days)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()

        print(f"Plot saved to {output_path}")

    def export_csv(self, output_path: str = ".brain/token_usage.csv") -> None:
        """Export usage data to CSV.

        Args:
            output_path: Path to save CSV.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("timestamp,model,tokens_in,tokens_out,total_tokens,agent,task_type,cached\n")

            for entry in self.entries:
                f.write(
                    f"{entry.timestamp.isoformat()},"
                    f"{entry.model},"
                    f"{entry.tokens_in},"
                    f"{entry.tokens_out},"
                    f"{entry.total_tokens},"
                    f"{entry.agent},"
                    f"{entry.task_type},"
                    f"{entry.cached}\n"
                )

        print(f"CSV exported to {output_path}")

    def clear_old_entries(self, days: int = 90) -> int:
        """Clear entries older than specified days.

        Args:
            days: Keep entries from last N days.

        Returns:
            Number of entries removed.
        """
        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self.entries)
        self.entries = [e for e in self.entries if e.timestamp > cutoff]
        removed = original_count - len(self.entries)

        if removed > 0:
            self._save()
            print(f"Cleared {removed} entries older than {days} days")

        return removed


def analyze_session_logs(log_path: str) -> dict[str, int]:
    """Analyze session logs for token usage.

    Args:
        log_path: Path to session log file.

    Returns:
        Dictionary with token counts by session.
    """
    path = Path(log_path)

    if not path.exists():
        return {}

    content = path.read_text(encoding="utf-8")

    import re

    token_pattern = re.compile(r"token.*?(\d+)", re.IGNORECASE)

    session_stats: dict[str, int] = {}

    current_session = None
    session_tokens = 0

    for line in content.split("\n"):
        session_match = re.search(r"session[_\s+id:\s+(\w+)", line)
        if session_match:
            if current_session and session_tokens > 0:
                session_stats[current_session] = session_tokens
            current_session = session_match.group(1)
            session_tokens = 0

        token_match = token_pattern.search(line)
        if token_match:
            session_tokens += int(token_match.group(1))

    if current_session and session_tokens > 0:
        session_stats[current_session] = session_tokens

    return session_stats


if __name__ == "__main__":
    import sys

    tracker = TokenTracker()

    if "--report" in sys.argv:
        days = (
            int(sys.argv[sys.argv.index("--report") + 1])
            if "--report" in sys.argv and len(sys.argv) > sys.argv.index("--report") + 1
            else 7
        )
        print(tracker.generate_report(days=days))
    elif "--plot" in sys.argv:
        days = (
            int(sys.argv[sys.argv.index("--plot") + 1])
            if "--plot" in sys.argv and len(sys.argv) > sys.argv.index("--plot") + 1
            else 30
        )
        tracker.plot_trends(days=days)
    elif "--csv" in sys.argv:
        tracker.export_csv()
    elif "--analyze" in sys.argv:
        log_file = (
            sys.argv[sys.argv.index("--analyze") + 1]
            if "--analyze" in sys.argv and len(sys.argv) > sys.argv.index("--analyze") + 1
            else ".opencode/logs/session.log"
        )
        stats = analyze_session_logs(log_file)
        for session, tokens in stats.items():
            print(f"{session}: {tokens} tokens")
    else:
        print("Usage:")
        print("  python scripts/token_tracker.py --report [days]  # Generate report")
        print("  python scripts/token_tracker.py --plot [days]      # Plot trends")
        print("  python scripts/token_tracker.py --csv               # Export CSV")
        print("  python scripts/token_tracker.py --analyze [log]    # Analyze logs")
