"""
Local runner for the multi-agent news aggregation pipeline.

Usage:
    python run_local.py                      # real mode (requires .env with Azure credentials)
    python run_local.py --demo               # demo mode (mock LLMs, live RSS feeds)
    python run_local.py --demo --topic trade # choose topic in demo mode
    python run_local.py --topic economy      # real mode with custom topic
"""
import argparse
import json
import sys
import os
import logging
from pathlib import Path

# ── Setup ─────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.WARNING)
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


# ── Demo mode mock LLMs ───────────────────────────────────────────────────────

SUMMARIZER_TEMPLATE = (
    "This article reports on {topic}. "
    "Key facts are presented from a {lean} perspective. "
    "Multiple stakeholders weigh in on the implications."
)

BIAS_RESPONSE = json.dumps({
    "lean_score": 0.0,
    "key_claims": ["Key claim 1", "Key claim 2"],
    "framing_notes": "Neutral demo framing",
    "named_entities": ["Demo Entity"],
})

AGREEMENT_RESPONSE = json.dumps({
    "agreements": ["Both sides agree on the basic facts"],
    "disagreements": ["Perspectives differ on policy implications"],
})


def make_demo_llm():
    """Return a callable that mimics the LangChain LLM interface without API calls."""
    from unittest.mock import MagicMock

    call_count = [0]

    def demo_llm(messages):
        idx = call_count[0]
        call_count[0] += 1
        resp = MagicMock()
        # Alternate between summarizer / bias / moderator style responses
        system_text = messages[0].content.lower() if messages else ""
        if "summarize" in system_text or "summary" in system_text:
            human_text = messages[1].content if len(messages) > 1 else ""
            topic = human_text[:40].replace("\n", " ") if human_text else "this topic"
            lean = "left" if idx % 2 == 0 else "right"
            resp.content = SUMMARIZER_TEMPLATE.format(topic=topic, lean=lean)
        elif "bias" in system_text or "lean" in system_text:
            score = round((-0.6 + (idx * 0.3)) % 1.4 - 0.7, 2)  # vary scores
            resp.content = json.dumps({
                "lean_score": score,
                "key_claims": [f"Demo claim {idx+1}a", f"Demo claim {idx+1}b"],
                "framing_notes": f"Demo framing note {idx+1}",
                "named_entities": ["Demo Entity", f"Entity {idx+1}"],
            })
        else:
            resp.content = AGREEMENT_RESPONSE
        return resp

    return demo_llm


# ── Main ──────────────────────────────────────────────────────────────────────

def run(topic: str, demo: bool):
    from src.graph.news_graph import build_graph

    if demo:
        from unittest.mock import patch
        demo_llm = make_demo_llm()
        patches = [
            patch("src.agents.summarizer.llm", side_effect=demo_llm),
            patch("src.agents.bias_analyzer.llm", side_effect=demo_llm),
            patch("src.agents.moderator.llm", side_effect=demo_llm),
        ]
        ctx_managers = [p.__enter__() for p in patches]
        try:
            pipeline = build_graph()
            result = pipeline.invoke({"topic": topic})
        finally:
            for p in reversed(patches):
                p.__exit__(None, None, None)
    else:
        pipeline = build_graph()
        result = pipeline.invoke({"topic": topic})

    return result


def pretty_print(digest: dict):
    """Print the balanced digest in a readable format."""
    topic = digest.get("topic") or "(all)"
    generated_at = digest.get("generated_at", "")
    paired = digest.get("paired_stories", [])
    left_only = digest.get("left_only_stories", [])
    right_only = digest.get("right_only_stories", [])

    print("\n" + "=" * 70)
    print(f"  BALANCED NEWS DIGEST — topic: {topic}")
    print(f"  Generated: {generated_at}")
    print("=" * 70)

    if paired:
        print(f"\n📰  PAIRED STORIES ({len(paired)} matched across perspectives)\n")
        for i, pair in enumerate(paired, 1):
            confidence = pair.get("match_confidence", 0)
            label = pair.get("topic_label", "")
            print(f"  [{i}] {label}  (confidence: {confidence:.2f})")
            left = pair.get("left", {})
            right = pair.get("right", {})
            print(f"      LEFT  [{left.get('lean_label', '')}]  {left.get('title', '')[:70]}")
            print(f"            {left.get('summary_text', '')[:120]}...")
            print(f"      RIGHT [{right.get('lean_label', '')}]  {right.get('title', '')[:70]}")
            print(f"            {right.get('summary_text', '')[:120]}...")
            agreements = pair.get("agreements", [])
            disagreements = pair.get("disagreements", [])
            if agreements:
                print(f"      ✅ Agree:    {'; '.join(agreements[:2])}")
            if disagreements:
                print(f"      ⚡ Disagree: {'; '.join(disagreements[:2])}")
            print()
    else:
        print("\n  (no matched story pairs)\n")

    if left_only:
        print(f"◀  LEFT-ONLY STORIES ({len(left_only)})")
        for s in left_only[:5]:
            print(f"     • [{s.get('lean_label', '')}] {s.get('title', '')[:70]}")
        print()

    if right_only:
        print(f"▶  RIGHT-ONLY STORIES ({len(right_only)})")
        for s in right_only[:5]:
            print(f"     • [{s.get('lean_label', '')}] {s.get('title', '')[:70]}")
        print()

    print("=" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the news aggregation pipeline locally.")
    parser.add_argument("--topic", default="economy", help="News topic to filter (default: economy)")
    parser.add_argument("--demo", action="store_true", help="Demo mode: use mock LLMs, live RSS feeds")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted digest")
    args = parser.parse_args()

    mode_label = "DEMO (mock LLMs)" if args.demo else "LIVE (Azure OpenAI)"
    print(f"\n🚀  Starting pipeline  |  mode: {mode_label}  |  topic: \"{args.topic}\"")
    print("    Fetching RSS feeds and processing articles...\n")

    try:
        result = run(topic=args.topic, demo=args.demo)
    except Exception as e:
        print(f"\n❌  Pipeline failed: {e}")
        if not args.demo:
            print("\n💡  Tip: Run with --demo to test without Azure credentials:")
            print("        python run_local.py --demo\n")
        sys.exit(1)

    digest = result.get("balanced_digest", {})

    if args.json:
        print(json.dumps(digest, indent=2))
    else:
        pretty_print(digest)

    # Summary stats
    left_count = len(result.get("left_articles", []))
    right_count = len(result.get("right_articles", []))
    summary_count = len(result.get("summaries", []))
    paired_count = len(digest.get("paired_stories", []))
    print(f"  Stats: {left_count} left + {right_count} right articles fetched, "
          f"{summary_count} summarized, {paired_count} pairs matched.\n")
