"""
Kubernetes Pod Module
Handles operations for Pods, providing formatted information retrieval.
"""

import json
import logging
from src.utils import load_kube_config

v1, apps_v1, version_api = load_kube_config()
logger = logging.getLogger(__name__)

def list_pods_in_namespace(namespace: str = 'default') -> str:
    """Lists all pods in the specified namespace."""

    v1, apps_v1, version_api = load_kube_config()
    
    logger.critical(f"[FUNCTION] Attempting to list pods in namespace: {namespace}")
    
    pods = v1.list_namespaced_pod(namespace).items
    if not pods:
        logger.error(f"[ERROR] No pods found in namespace: {namespace}")
        return f"# Pods in namespace: {namespace}\n\nNo pods found."
    
    lines = ["", "## Managed Pods", "| Pod Name | Status | Node | Pod IP |", "|-----------|--------|------|---------|"]

    for pod in pods:
        lines.append(
            f"| {pod.metadata.name} | {pod.status.phase} | {pod.spec.node_name} | {pod.status.pod_ip} |"
        )
    
    return "\n".join(lines)

def get_pod_details(pod_name: str, namespace: str = 'default', deep: bool = False) -> str:
    """
    Gets detailed information about a specific Pod.
    
    Args:
        pod_name: Name of the Pod
        namespace: Kubernetes namespace
        deep: If True, returns raw JSON data with full pod info, events, and logs
    """
    v1, apps_v1, version_api = load_kube_config()

    logger.critical(f"[FUNCTION] Attempting to get pod details for {pod_name} in namespace: {namespace} (deep={deep})")
    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to get pod details for {pod_name} in namespace: {namespace}: {e.reason}")
        return f"Error: {e.reason}"

    if deep:
        field_selector = f"involvedObject.kind=Pod,involvedObject.name={pod_name},involvedObject.namespace={namespace}"
        events = v1.list_event_for_all_namespaces(field_selector=field_selector).items
        events_dict = [e.to_dict() for e in events]

        container_logs = {}
        for c in pod.spec.containers:
            try:
                log = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, container=c.name)
            except Exception as e:
                log = "No logs available or unable to retrieve logs."
            container_logs[c.name] = log

        data = {
            "pod": pod.to_dict(),
            "events": events_dict,
            "logs": container_logs
        }
        return f"```json\n{json.dumps(data, indent=2, default=str)}\n```"

    lines = [
        f"# Pod Details: {pod_name}",
        f"**Namespace**: {namespace}",
        f"**Phase**: {pod.status.phase}",
        f"**Host Node**: {pod.spec.node_name}",
        f"**Pod IP**: {pod.status.pod_ip}",
        "",
        "## Labels",
        "```",
        "\n".join([f"{k}: {v}" for k, v in (pod.metadata.labels or {}).items()]) or "No labels",
        "```",
        "",
        "## Conditions",
        "| Type | Status | Reason | Message |",
        "|------|--------|---------|---------|"
    ]

    for c in pod.status.conditions or []:
        lines.append(f"| {c.type} | {c.status} | {c.reason or 'N/A'} | {c.message or 'N/A'} |")

    lines.extend(["", "## Containers"])

    for c in pod.spec.containers:
        cs = next((cs for cs in (pod.status.container_statuses or []) if cs.name == c.name), None)
        
        lines.extend([
            f"### Container: {c.name}",
            f"- **Image**: `{c.image}`",
            "- **Resources**:"
        ])

        requests = c.resources.requests or {}
        limits = c.resources.limits or {}
        if requests:
            lines.append("  - **Requests**:")
            for k, v in requests.items():
                lines.append(f"    - {k}: {v}")
        if limits:
            lines.append("  - **Limits**:")
            for k, v in limits.items():
                lines.append(f"    - {k}: {v}")

        if cs:
            lines.append("- **Status**:")
            lines.append(f"  - Ready: {cs.ready}")
            lines.append(f"  - Restart Count: {cs.restart_count}")
            
            if cs.state.waiting:
                lines.extend([
                    "  - State: Waiting",
                    f" - Reason: {cs.state.waiting.reason}",
                    f" - Message: {cs.state.waiting.message}"
                ])
            elif cs.state.running:
                lines.extend([
                    " - State: Running",
                    f" - Started At: {cs.state.running.started_at}"
                ])
            elif cs.state.terminated:
                lines.extend([
                    " - State: Terminated",
                    f" - Reason: {cs.state.terminated.reason}",
                    f" - Exit Code: {cs.state.terminated.exit_code}",
                    f" - Started At: {cs.state.terminated.started_at}",
                    f" - Finished At: {cs.state.terminated.finished_at}"
                ])

    return "\n".join(lines)

if __name__ == "__main__":
    print(list_pods_in_namespace(namespace='default'))
    print(get_pod_details(pod_name='api-774f98dbbd-7qk8t', deep=True))    
    print(get_pod_details(pod_name='api-774f98dbbd-7qk8t', deep=False))    
    