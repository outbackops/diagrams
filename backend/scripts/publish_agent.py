"""Foundry agent publishing script — register agent application,
configure Entra identity, publish endpoint (T079).

Usage:
    python scripts/publish_agent.py --project-connection <connection_string>

Prerequisites:
    - az login
    - pip install azure-ai-projects azure-identity
"""

from __future__ import annotations

import argparse
import sys


def publish_agent(connection_string: str) -> None:
    """Publish the diagram agent to Azure AI Foundry."""
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
    except ImportError:
        print("ERROR: Install azure-ai-projects and azure-identity first.")
        print("  pip install 'azure-ai-projects>=2.0.0b3' azure-identity")
        sys.exit(1)

    credential = DefaultAzureCredential()
    client = AIProjectClient(
        credential=credential,
        connection_string=connection_string,
    )

    print("Publishing diagram agent to Azure AI Foundry...")
    print(f"  Project: {connection_string}")

    # Agent registration would use the client.agents API
    # This is a scaffold — actual registration depends on Foundry SDK version
    print("\nAgent publishing steps:")
    print("  1. Build Docker image: docker build -t diagram-agent:latest -f backend/Dockerfile .")
    print("  2. Tag for ACR: docker tag diagram-agent:latest <acr>.azurecr.io/diagram-agent:latest")
    print("  3. Push to ACR: docker push <acr>.azurecr.io/diagram-agent:latest")
    print("  4. Deploy with azd: azd up")
    print("  5. Register agent application in Foundry portal")
    print("\nOr use `azd up` from the repository root with azure.yaml configured.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish Diagram Agent to Azure AI Foundry")
    parser.add_argument(
        "--project-connection",
        required=True,
        help="Azure AI Foundry project connection string",
    )
    args = parser.parse_args()
    publish_agent(args.project_connection)


if __name__ == "__main__":
    main()
