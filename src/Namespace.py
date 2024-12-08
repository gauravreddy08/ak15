"""
Kubernetes Namespace Module
Handles operations for Namespaces, providing formatted information retrieval.
"""

import json
import logging
from src.utils import load_kube_config

v1, apps_v1, version_api = load_kube_config()
logger = logging.getLogger(__name__)

def list_all_namespaces() -> str:
    """Lists all namespaces in the cluster."""
    try:
        logger.info("[INFO] Attempting to list all namespaces")
        namespaces = v1.list_namespace().items
        namespace_names = [ns.metadata.name for ns in namespaces]

        lines = ["# Namespace Names", ""]
        for name in namespace_names:
            lines.append(f"- {name}")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to list all namespaces: {e.reason}")
        return f"[ERROR] Attempting to list all namespaces: {e.reason}"

def get_namespace_details(namespace: str = 'default', deep: bool = False) -> str:
    """
    Gets detailed information about a specific Namespace.
    
    Args:
        namespace: Name of the namespace
        deep: If True, returns raw JSON data with namespace, quotas, pods, and services
    """
    logger.critical(f"[FUNCTION] Attempting to get namespace details for {namespace} (deep={deep})")

    try:
        ns = v1.read_namespace(name=namespace)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to get namespace details for {namespace}: {e.reason}")
        return f"[ERROR] Attempting to get namespace details for {namespace}: {e.reason}"

    quotas = v1.list_namespaced_resource_quota(namespace=namespace).items
    pods = v1.list_namespaced_pod(namespace=namespace).items
    services = v1.list_namespaced_service(namespace=namespace).items

    if deep:
        data = {
            "namespace": ns.to_dict(),
            "resourceQuotas": [q.to_dict() for q in quotas],
            "pods": [p.metadata.name for p in pods],
            "services": [s.metadata.name for s in services]
        }
        return f"```json\n{json.dumps(data, indent=2, default=str)}\n```"

    ns_phase = ns.status.phase
    labels = ns.metadata.labels or {}

    quota_list = []
    for q in quotas:
        q_hard = q.status.hard if q.status else {}
        q_used = q.status.used if q.status else {}
        quota_info = {
            "name": q.metadata.name,
            "hard": {k: v for k, v in q_hard.items()},
            "used": {k: v for k, v in q_used.items()}
        }
        quota_list.append(quota_info)

    pod_count = len(pods)
    service_count = len(services)

    lines = [
        f"# Namespace Details for: {namespace}",
        f"## Phase: {ns_phase}",
        "## Labels:"
    ]
    lines += [f"- {k}: {v}" for k, v in labels.items()] if labels else ["None"]
    lines += ["", "## Resource Quotas:"]
    for quota in quota_list:
        lines.append(f"- Name: {quota['name']}")
        lines.append("  - Hard:")
        lines += [f"    - {k}: {v}" for k, v in quota['hard'].items()]
        lines.append("  - Used:")
        lines += [f"    - {k}: {v}" for k, v in quota['used'].items()]
    lines += ["", f"## Pod Count: {pod_count}", f"## Service Count: {service_count}"]

    return "\n".join(lines)

if __name__ == "__main__":
    print(list_all_namespaces())
    print('-'*100)
    print(get_namespace_details(namespace='default', deep=False)) 
    print('-'*100)
    print(get_namespace_details(namespace='default', deep=True))   
    print('-'*100)
    print(get_namespace_details(namespace='hello', deep=True))     
    print('-'*100)
    print(get_namespace_details(namespace='hello', deep=False))     