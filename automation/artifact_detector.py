import os
import json
import fnmatch
from typing import List, Dict, Tuple
from pathlib import Path


class ArtifactDetector:
    """
    Detects and classifies artifacts in the test_case_artifacts directory.
    Maps artifacts to appropriate test generation agents based on patterns.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the artifact detector with configuration

        Args:
            config_path: Path to the configuration file
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.artifacts_config = self.config.get("artifacts", {})
        self.base_dir = self.artifacts_config.get("base_dir", "test_case_artifacts")
        self.mappings = self.artifacts_config.get("mappings", {})

    def detect_artifacts(self) -> List[Dict]:
        """
        Scan the artifacts directory and detect all artifacts

        Returns:
            List of detected artifacts with metadata:
            [
                {
                    "path": "path/to/artifact",
                    "filename": "artifact.json",
                    "type": "openapi",
                    "agent": "openapi_test_generator",
                    "description": "OpenAPI specification"
                },
                ...
            ]
        """
        if not os.path.exists(self.base_dir):
            print(f"❌ Artifacts directory not found: {self.base_dir}")
            return []

        detected_artifacts = []

        # Get all files in the artifacts directory
        artifact_files = []
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if not file.startswith('.'):  # Skip hidden files
                    artifact_files.append(os.path.join(root, file))

        if not artifact_files:
            print(f"⚠️  No artifacts found in {self.base_dir}")
            return []

        # Classify each artifact
        for artifact_path in artifact_files:
            artifact_info = self._classify_artifact(artifact_path)
            if artifact_info:
                detected_artifacts.append(artifact_info)

        return detected_artifacts

    def _classify_artifact(self, artifact_path: str) -> Dict:
        """
        Classify an artifact based on filename patterns

        Args:
            artifact_path: Path to the artifact file

        Returns:
            Dictionary with artifact metadata or None if not matched
        """
        filename = os.path.basename(artifact_path)

        # Try to match against each artifact type
        for artifact_type, config in self.mappings.items():
            patterns = config.get("patterns", [])

            for pattern in patterns:
                if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    return {
                        "path": artifact_path,
                        "filename": filename,
                        "type": artifact_type,
                        "agent": config.get("agent"),
                        "description": config.get("description")
                    }

        # If no pattern matched, classify as unknown
        return {
            "path": artifact_path,
            "filename": filename,
            "type": "unknown",
            "agent": None,
            "description": "Unknown artifact type"
        }

    def get_agent_for_artifact(self, artifact_type: str) -> str:
        """
        Get the agent name for a given artifact type

        Args:
            artifact_type: Type of the artifact

        Returns:
            Agent name or None
        """
        artifact_config = self.mappings.get(artifact_type, {})
        return artifact_config.get("agent")

    def get_agent_config(self, agent_name: str) -> Dict:
        """
        Get the configuration for a specific agent

        Args:
            agent_name: Name of the agent

        Returns:
            Agent configuration dictionary
        """
        agents = self.config.get("agents", {})
        return agents.get(agent_name, {})

    def print_detection_summary(self, artifacts: List[Dict]):
        """
        Print a summary of detected artifacts

        Args:
            artifacts: List of detected artifacts
        """
        print(f"\n{'='*80}")
        print(f"📦 Artifact Detection Summary")
        print(f"{'='*80}")
        print(f"Base Directory: {self.base_dir}")
        print(f"Total Artifacts Found: {len(artifacts)}")
        print()

        # Group by type
        by_type = {}
        for artifact in artifacts:
            artifact_type = artifact.get("type")
            if artifact_type not in by_type:
                by_type[artifact_type] = []
            by_type[artifact_type].append(artifact)

        # Print grouped artifacts
        for artifact_type, items in by_type.items():
            agent_name = items[0].get("agent", "N/A")
            description = items[0].get("description", "")

            print(f"📋 {artifact_type.upper()} ({len(items)} file{'s' if len(items) > 1 else ''})")
            print(f"   Agent: {agent_name}")
            print(f"   Description: {description}")
            print(f"   Files:")
            for item in items:
                print(f"      - {item.get('filename')}")
            print()

        print(f"{'='*80}\n")


def main():
    """
    Test the artifact detector
    """
    detector = ArtifactDetector()
    artifacts = detector.detect_artifacts()
    detector.print_detection_summary(artifacts)

    return artifacts


if __name__ == "__main__":
    main()
