"""
Kubernetes Deployment Module
Handles operations for Deployments, providing formatted information retrieval.
"""

import json
import logging
from src.utils import load_kube_config

v1, apps_v1, version_api = load_kube_config()
logger = logging.getLogger(__name__)

def list_deployments(namespace: str = 'default') -> str:
    """Lists all deployments in the specified namespace."""
    logger.critical(f"[FUNCTION] Attempting to list deployments in namespace: {namespace}")
    try:
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace).items
    except Exception as e:
        logger.error(f"[ERROR] Attempting to list deployments in namespace: {namespace}: {e.reason}")
        return f"[ERROR] Attempting to list deployments in namespace: {namespace}: {e.reason}"
    
    deployment_names = [d.metadata.name for d in deployments]
    lines = [f"# Deployments in namespace: {namespace}", ""]
    for name in deployment_names:
        lines.append(f"- {name}")

    return "\n".join(lines)

def get_deployment_details(deployment_name: str, namespace: str = 'default', deep: bool = False) -> str:
    """
    Gets detailed information about a specific Deployment.
    
    Args:
        deployment_name: Name of the Deployment
        namespace: Kubernetes namespace
        deep: If True, returns raw JSON data instead of formatted markdown
    """
    logger.critical(f"[FUNCTION] Attempting to get deployment details for {deployment_name} in namespace: {namespace} (deep={deep})")
    try:
        d = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to get deployment details for {deployment_name} in namespace: {namespace}: {e.reason}")
        return f"[ERROR] Attempting to get deployment details for {deployment_name} in namespace: {namespace}: {e.reason}"

    if deep:
        return f"```json\n{json.dumps(d.to_dict(), indent=2, default=str)}\n```"

    selector = d.spec.selector.match_labels
    selector_str = ','.join([f'{k}={v}' for k, v in selector.items()])
    pods = v1.list_namespaced_pod(
        namespace=namespace,
        label_selector=selector_str
    ).items

    lines = [
        f"# Deployment: {deployment_name}",
        f"**Namespace**: {namespace}",
        "",
        "## Replica Status",
        f"- Desired: {d.spec.replicas or 0}",
        f"- Current: {d.status.replicas or 0}",
        f"- Available: {d.status.available_replicas or 0}",
        f"- Updated: {d.status.updated_replicas or 0}",
        f"- Ready: {d.status.ready_replicas or 0}",
        f"- Unavailable: {d.status.unavailable_replicas or 0}",
        "",
        "## Container Images"
    ]

    for container in d.spec.template.spec.containers:
        lines.append(f"- `{container.image}`")

    lines.extend(["", "## Conditions", "| Type | Status | Reason | Message |", "|------|--------|---------|---------|"])
    for c in (d.status.conditions or []):
        lines.append(f"| {c.type} | {c.status} | {c.reason} | {c.message} |")

    lines.extend(["", "## Managed Pods", "| Pod Name | Status | Node | Pod IP |", "|-----------|--------|------|---------|"])
    for pod in pods:
        lines.append(
            f"| {pod.metadata.name} | {pod.status.phase} | {pod.spec.node_name} | {pod.status.pod_ip} |"
        )

    return "\n".join(lines)

if __name__ == "__main__":
    print(list_deployments(namespace='default'))
    print('-'*100)
    print(list_deployments(namespace='hello'))
    print('-'*100)
    print(get_deployment_details(deployment_name='api', namespace='default', deep=True))
    print('-'*100)
    print(get_deployment_details(deployment_name='api', namespace='default', deep=False))
    print('-'*100)
    print(get_deployment_details(deployment_name='api', namespace='hello', deep=True))
    print('-'*100)
    print(get_deployment_details(deployment_name='api', namespace='hello', deep=False))
    print('-'*100)
    print(get_deployment_details(deployment_name='hello', deep=True))
    print('-'*100)
    print(get_deployment_details(deployment_name='hello', deep=False))