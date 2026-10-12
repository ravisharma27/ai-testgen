"""Command line entry point.

    python -m testgen generate examples/stories/password_reset.md
    python -m testgen generate examples/stories/password_reset.md -o output/password_reset.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .client import ConfigError, build_client, deployment_name
from .generator import GenerationError, generate_test_suite


def _print_summary(result) -> None:
    suite = result.suite
    print(f"\n{suite.story_summary}\n")
    print(f"{'ID':<8}{'Technique':<26}{'Priority':<10}Title")
    print("-" * 90)
    for tc in suite.test_cases:
        print(f"{tc.id:<8}{tc.technique.value:<26}{tc.priority.value:<10}{tc.title}")
    techniques = ", ".join(sorted(t.value for t in suite.techniques_used()))
    print(
        f"\n{len(suite.test_cases)} test cases | techniques: {techniques} | "
        f"attempts: {result.attempt_count} | tokens: {result.total_tokens}"
    )


def cmd_generate(args: argparse.Namespace) -> int:
    story = Path(args.story).read_text(encoding="utf-8")
    try:
        client = build_client()
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    model = args.deployment or deployment_name()
    try:
        result = generate_test_suite(story, client, model, max_attempts=args.max_attempts)
    except GenerationError as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    _print_summary(result)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": str(args.story),
            "deployment": model,
            "attempts": [
                {"number": a.number, "error": a.error, "latency_s": a.latency_s,
                 "total_tokens": a.total_tokens}
                for a in result.attempts
            ],
            "suite": result.suite.model_dump(mode="json"),
        }
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved to {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="testgen", description="AI test case generator")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate test cases from a user story file")
    gen.add_argument("story", help="Path to a .md or .txt user story")
    gen.add_argument("-o", "--output", help="Write the validated JSON here")
    gen.add_argument("-d", "--deployment", help="Deployment name (default: env or gpt-5-mini)")
    gen.add_argument("--max-attempts", type=int, default=3)
    gen.set_defaults(func=cmd_generate)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    return args.func(args)
