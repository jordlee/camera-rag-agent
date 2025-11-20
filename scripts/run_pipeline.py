#!/usr/bin/env python3
"""
SDK RAG Pipeline Orchestrator

Unified pipeline runner for all SDK variants (Camera Remote, PTP, C#).
Executes parse → chunk → embed workflow based on config/pipeline_config.yaml.

Usage:
    # Run full pipeline
    python scripts/run_pipeline.py --sdk-type camera-remote --version V2.00.00

    # Run specific steps only
    python scripts/run_pipeline.py --sdk-type ptp --version V2.00.00 --steps chunk,embed

    # Dry-run mode (show what would be executed)
    python scripts/run_pipeline.py --sdk-type csharp --version V2.00.00 --dry-run

    # Test mode (process limited data)
    python scripts/run_pipeline.py --sdk-type camera-remote --version V2.00.00 --test
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
import yaml

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "config/pipeline_config.yaml"


class PipelineOrchestrator:
    """Orchestrates SDK RAG pipeline execution."""

    def __init__(self, sdk_type: str, version: str, steps: list, dry_run: bool = False, test_mode: bool = False, environment: str = 'production'):
        """
        Initialize pipeline orchestrator.

        Args:
            sdk_type: SDK type (camera-remote, ptp, csharp, camera-remote-legacy)
            version: SDK version (V1.14.00, V2.00.00)
            steps: List of steps to execute (parse, chunk, embed)
            dry_run: If True, show commands without executing
            test_mode: If True, enable test mode in scripts (limited data)
            environment: Target environment (staging or production)
        """
        self.sdk_type = sdk_type
        self.version = version
        self.steps = steps
        self.dry_run = dry_run
        self.test_mode = test_mode
        self.environment = environment

        # Load config
        self.config = self._load_config()
        self.variant_config = self._get_variant_config()

        # Execution state
        self.start_time = None
        self.step_times = {}

    def _load_config(self) -> dict:
        """Load pipeline configuration."""
        print(f"Loading configuration from: {CONFIG_FILE}")

        if not CONFIG_FILE.exists():
            raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)

        print(f"✅ Configuration loaded")
        return config

    def _get_variant_config(self) -> dict:
        """Get configuration for specific SDK variant."""
        if self.sdk_type not in self.config:
            raise ValueError(
                f"SDK type '{self.sdk_type}' not found in config. "
                f"Available: {list(self.config.keys())}"
            )

        variant = self.config[self.sdk_type]

        if self.version not in variant:
            raise ValueError(
                f"Version '{self.version}' not found for SDK type '{self.sdk_type}'. "
                f"Available: {list(variant.keys())}"
            )

        return variant[self.version]

    def _run_command(self, command: list, description: str, step_name: str) -> bool:
        """
        Execute a subprocess command.

        Args:
            command: Command as list of strings
            description: Human-readable description
            step_name: Step name for timing

        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"{description}")
        print(f"{'='*70}")
        print(f"Command: {' '.join(command)}\n")

        if self.dry_run:
            print("🔍 DRY RUN - Command not executed")
            return True

        step_start = time.time()

        try:
            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=False,  # Show output in real-time
                text=True
            )

            elapsed = time.time() - step_start
            self.step_times[step_name] = elapsed

            print(f"\n✅ {description} completed in {self._format_time(elapsed)}")
            return True

        except subprocess.CalledProcessError as e:
            elapsed = time.time() - step_start
            print(f"\n❌ {description} failed after {self._format_time(elapsed)}")
            print(f"Error: {e}")
            return False

    def _format_time(self, seconds: float) -> str:
        """Format seconds as human-readable time."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes, secs = divmod(seconds, 60)
        return f"{int(minutes)}m {int(secs)}s"

    def run_parsers(self) -> bool:
        """Execute all parsers for the SDK variant."""
        if 'parse' not in self.steps:
            print("ℹ️  Skipping parse step")
            return True

        parsers = self.variant_config.get('parsers', [])

        if not parsers:
            print("⚠️  No parsers defined for this variant")
            return True

        print(f"\n{'#'*70}")
        print(f"# STEP 1: PARSING ({len(parsers)} parsers)")
        print(f"{'#'*70}")

        for i, parser in enumerate(parsers, 1):
            parser_name = parser['name']
            parser_script = PROJECT_ROOT / parser['script']
            parser_args = parser.get('args', [])
            description = parser.get('description', f'Run {parser_name}')

            # Build command
            command = ['python', str(parser_script)] + parser_args

            # Add test mode flag if applicable
            if self.test_mode and '--test' not in command:
                command.append('--test')

            # Execute
            step_name = f"parse_{parser_name}"
            success = self._run_command(
                command,
                f"[{i}/{len(parsers)}] {description}",
                step_name
            )

            if not success:
                print(f"\n❌ Parser '{parser_name}' failed - stopping pipeline")
                return False

        print(f"\n✅ All parsers completed successfully")
        return True

    def run_chunker(self) -> bool:
        """Execute chunker for the SDK variant."""
        if 'chunk' not in self.steps:
            print("\nℹ️  Skipping chunk step")
            return True

        chunker = self.variant_config.get('chunker')

        if not chunker:
            print("\n⚠️  No chunker defined for this variant")
            return True

        print(f"\n{'#'*70}")
        print(f"# STEP 2: CHUNKING")
        print(f"{'#'*70}")

        chunker_script = PROJECT_ROOT / chunker['script']
        description = chunker.get('description', 'Run chunker')

        # Build command
        command = ['python', str(chunker_script)]

        # Add test mode flag if applicable
        if self.test_mode and '--test' not in command:
            command.append('--test')

        # Execute
        success = self._run_command(command, description, 'chunk')

        if success:
            output_file = chunker.get('output', 'N/A')
            print(f"📄 Chunks saved to: {output_file}")

        return success

    def run_embedder(self) -> bool:
        """Execute embedder for the SDK variant."""
        if 'embed' not in self.steps:
            print("\nℹ️  Skipping embed step")
            return True

        embedder = self.variant_config.get('embedder')

        if not embedder:
            print("\n⚠️  No embedder defined for this variant")
            return True

        print(f"\n{'#'*70}")
        print(f"# STEP 3: EMBEDDING")
        print(f"{'#'*70}")

        embedder_script = PROJECT_ROOT / embedder['script']
        description = embedder.get('description', 'Run embedder')

        # Build command
        command = ['python', str(embedder_script)]

        # Add test mode flag if applicable
        if self.test_mode and '--test' not in command:
            command.append('--test')

        # Add environment flag (staging or production)
        if self.environment == 'staging':
            command.extend(['--env', 'staging'])

        # Execute
        success = self._run_command(command, description, 'embed')

        if success:
            index_name = embedder.get('index', 'N/A')
            if self.environment == 'staging':
                print(f"📊 Vectors uploaded to STAGING Pinecone index: sdk-rag-system-v2-staging")
            else:
                print(f"📊 Vectors uploaded to Pinecone index: {index_name}")

        return success

    def run(self) -> bool:
        """Execute complete pipeline."""
        print("\n" + "=" * 70)
        print("SDK RAG PIPELINE ORCHESTRATOR")
        print("=" * 70)
        print(f"SDK Type: {self.sdk_type}")
        print(f"Version: {self.version}")
        print(f"Steps: {', '.join(self.steps)}")
        print(f"Environment: {self.environment.upper()}")
        print(f"Mode: {'DRY RUN' if self.dry_run else ('TEST' if self.test_mode else 'PRODUCTION')}")
        print("=" * 70)

        self.start_time = time.time()

        # Execute pipeline steps
        steps_to_run = [
            ('parse', self.run_parsers),
            ('chunk', self.run_chunker),
            ('embed', self.run_embedder)
        ]

        for step_name, step_func in steps_to_run:
            if step_name in self.steps:
                success = step_func()
                if not success:
                    self._print_summary(failed_step=step_name)
                    return False

        # Success!
        self._print_summary()
        return True

    def _print_summary(self, failed_step: str = None):
        """Print pipeline execution summary."""
        total_time = time.time() - self.start_time

        print("\n" + "=" * 70)
        if failed_step:
            print(f"❌ PIPELINE FAILED AT: {failed_step.upper()}")
        else:
            print("✅ PIPELINE COMPLETE")
        print("=" * 70)

        print(f"SDK Type: {self.sdk_type}")
        print(f"Version: {self.version}")
        print(f"Total time: {self._format_time(total_time)}")

        if self.step_times:
            print("\nStep timings:")
            for step, duration in self.step_times.items():
                print(f"  - {step}: {self._format_time(duration)}")

        print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SDK RAG Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline for Camera Remote SDK V2
  python scripts/run_pipeline.py --sdk-type camera-remote --version V2.00.00

  # Run only chunking and embedding (skip parsing)
  python scripts/run_pipeline.py --sdk-type ptp --version V2.00.00 --steps chunk,embed

  # Dry-run to see what would be executed
  python scripts/run_pipeline.py --sdk-type csharp --version V2.00.00 --dry-run

  # Test mode (limited data processing)
  python scripts/run_pipeline.py --sdk-type camera-remote --version V2.00.00 --test
        """
    )

    parser.add_argument(
        '--sdk-type',
        required=True,
        choices=['camera-remote', 'ptp', 'csharp', 'camera-remote-legacy'],
        help='SDK type to process'
    )

    parser.add_argument(
        '--version',
        required=True,
        choices=['V1.14.00', 'V2.00.00'],
        help='SDK version'
    )

    parser.add_argument(
        '--steps',
        default='parse,chunk,embed',
        help='Comma-separated list of steps to run (parse, chunk, embed). Default: all steps'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show commands without executing them'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Enable test mode (process limited data)'
    )

    parser.add_argument(
        '--env',
        '--environment',
        type=str,
        default='production',
        choices=['staging', 'production'],
        help='Target environment for embeddings (staging or production). Default: production'
    )

    args = parser.parse_args()

    # Parse steps
    steps = [step.strip() for step in args.steps.split(',')]
    valid_steps = {'parse', 'chunk', 'embed'}
    invalid_steps = set(steps) - valid_steps

    if invalid_steps:
        print(f"❌ Invalid steps: {invalid_steps}")
        print(f"Valid steps: {valid_steps}")
        sys.exit(1)

    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        sdk_type=args.sdk_type,
        version=args.version,
        steps=steps,
        dry_run=args.dry_run,
        test_mode=args.test,
        environment=args.env
    )

    # Run pipeline
    success = orchestrator.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
