"""
Kubernetes Workload Module
Handles operations for DaemonSets, StatefulSets, and ReplicaSets.
"""

import json
import logging
from src.utils import load_kube_config

v1, apps_v1, version_api = load_kube_config()
logger = logging.getLogger(__name__)

def list_daemonset_names(namespace: str = 'default') -> str:
    """Lists all DaemonSets in the specified namespace."""
    logger.critical(f"[FUNCTION] Attempting to list daemonsets in namespace: {namespace}")
    try:
        daemonsets = apps_v1.list_namespaced_daemon_set(namespace=namespace).items
    except Exception as e:
        logger.error(f"[ERROR] Attempting to list daemonsets in namespace: {namespace}: {e.reason}")
        return f"[ERROR] Attempting to list daemonsets in namespace: {namespace}: {e.reason}"
    
    if len(daemonsets) == 0:
        return f"No DaemonSets found in namespace {namespace}"
    
    ds_names = [ds.metadata.name for ds in daemonsets]

    # Create markdown formatted output
    lines = [
        f"# DaemonSets in namespace: {namespace}",
        "",  # Empty line for better readability
    ]

    for name in ds_names:
        lines.append(f"- {name}")

    return "\n".join(lines)


def get_daemonset_details(daemonset_name: str, namespace: str = 'default', deep: bool = False) -> str:
    """
    Gets detailed information about a specific DaemonSet.
    
    Args:
        daemonset_name: Name of the DaemonSet
        namespace: Kubernetes namespace
        deep: If True, returns raw JSON data instead of formatted markdown
    """
    logger.critical(f"[FUNCTION] Attempting to get daemonset details for {daemonset_name} in namespace: {namespace} (deep={deep})")
    try:
        ds = apps_v1.read_namespaced_daemon_set(name=daemonset_name, namespace=namespace)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to get daemonset details for {daemonset_name} in namespace: {namespace}: {e.reason}")
        return f"[ERROR] Attempting to get daemonset details for {daemonset_name} in namespace: {namespace}: {e.reason}"

    if deep:
        return f"```json\n{json.dumps(ds.to_dict(), indent=2, default=str)}\n```"

    status = ds.status
    container_images = [c.image for c in ds.spec.template.spec.containers]
    node_selector = ds.spec.template.spec.node_selector or {}

    lines = [
        f"# DaemonSet: {daemonset_name}",
        f"**Namespace**: {namespace}",
        "",
        "## Pod Status",
        f"- Desired Pods: {status.desired_number_scheduled or 0}",
        f"- Current Pods: {status.current_number_scheduled or 0}",
        f"- Ready Pods: {status.number_ready or 0}",
        f"- Updated Pods: {status.updated_number_scheduled or 0}",
        "",
        "## Container Images"
    ]

    # Add container images
    for image in container_images:
        lines.append(f"- `{image}`")

    # Add node selector if present
    if node_selector:
        lines.extend([
            "",
            "## Node Selector"
        ])
        for key, value in node_selector.items():
            lines.append(f"- {key}: {value}")

    # Add conditions if present
    if ds.status.conditions:
        lines.extend([
            "",
            "## Conditions",
            "| Type | Status | Reason | Message |",
            "|------|--------|---------|---------|"
        ])
        for condition in ds.status.conditions:
            lines.append(
                f"| {condition.type} | {condition.status} | "
                f"{condition.reason or 'N/A'} | {condition.message or 'N/A'} |"
            )

    return "\n".join(lines)


def list_statefulset_names(namespace: str = 'default') -> str:
    """Lists all StatefulSets in the specified namespace."""
    logger.critical(f"[FUNCTION] Attempting to list statefulsets in namespace: {namespace}")
    
    statefulsets = apps_v1.list_namespaced_stateful_set(namespace=namespace).items
    
    sts_names = [sts.metadata.name for sts in statefulsets]

    lines = [
        f"# StatefulSets in namespace: {namespace}",
        ""  # Empty line for better readability
    ]
    
    if not sts_names:
        lines.append("No StatefulSets found in this namespace.")
    else:
        for name in sts_names:
            lines.append(f"- {name}")

    return "\n".join(lines)

def get_statefulset_details(statefulset_name: str, namespace: str = 'default', deep: bool = False) -> str:
    """
    Gets detailed information about a specific StatefulSet.
    
    Args:
        statefulset_name: Name of the StatefulSet
        namespace: Kubernetes namespace
        deep: If True, returns raw JSON data instead of formatted markdown
    """
    logger.critical(f"[FUNCTION] Attempting to get statefulset details for {statefulset_name} in namespace: {namespace} (deep={deep})")
    try:
        sts = apps_v1.read_namespaced_stateful_set(name=statefulset_name, namespace=namespace)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to get statefulset details for {statefulset_name} in namespace: {namespace}: {e.reason}")
        return f"[ERROR] Attempting to get statefulset details for {statefulset_name} in namespace: {namespace}: {e.reason}"

    if deep:
        return f"```json\n{json.dumps(sts.to_dict(), indent=2, default=str)}\n```"

    lines = [
        f"# StatefulSet: {statefulset_name}",
        f"**Namespace**: {namespace}",
        "",
        "## Replica Status",
        f"- Desired: {sts.spec.replicas or 0}",
        f"- Current: {sts.status.current_replicas or 0}",
        f"- Ready: {sts.status.ready_replicas or 0}",
        f"- Updated: {sts.status.updated_replicas or 0}",
        "",
        f"## Pod Management Policy: {sts.spec.pod_management_policy or 'OrderedReady'}",
        "",
        "## Container Images"
    ]

    # Add container images
    for container in sts.spec.template.spec.containers:
        lines.append(f"- `{container.image}`")

    # Add volume claim templates if present
    if sts.spec.volume_claim_templates:
        lines.extend([
            "",
            "## Volume Claim Templates"
        ])
        for vct in sts.spec.volume_claim_templates:
            storage = vct.spec.resources.requests.get('storage', 'N/A')
            lines.extend([
                f"### {vct.metadata.name}:",
                f"- Storage Class: {vct.spec.storage_class_name or 'default'}",
                f"- Access Modes: {', '.join(vct.spec.access_modes)}",
                f"- Storage Request: {storage}"
            ])

    # Add conditions if present
    if sts.status.conditions:
        lines.extend([
            "",
            "## Conditions",
            "| Type | Status | Reason | Message |",
            "|------|--------|---------|---------|"
        ])
        for condition in sts.status.conditions:
            lines.append(
                f"| {condition.type} | {condition.status} | "
                f"{condition.reason or 'N/A'} | {condition.message or 'N/A'} |"
            )

    return "\n".join(lines)

def list_replicaset_names(namespace: str = 'default') -> str:
    """Lists all ReplicaSets in the specified namespace."""
    logger.critical(f"[FUNCTION] Attempting to list replicasets in namespace: {namespace}")
    replicasets = apps_v1.list_namespaced_replica_set(namespace=namespace).items
    lines = [
        f"# ReplicaSets in namespace: {namespace}",
        ""  # Empty line for better readability
    ]
    
    if not replicasets:
        lines.append("No ReplicaSets found in this namespace.")
    else:
        for rs in replicasets:
            lines.append(f"- {rs.metadata.name}")

    return "\n".join(lines)

def get_replicaset_details(replicaset_name: str, namespace: str = 'default', deep: bool = False) -> str:
    """
    Gets detailed information about a specific ReplicaSet.
    
    Args:
        replicaset_name: Name of the ReplicaSet
        namespace: Kubernetes namespace
        deep: If True, returns raw JSON data instead of formatted markdown
    """
    logger.critical(f"[FUNCTION] Attempting to get replicaset details for {replicaset_name} in namespace: {namespace} (deep={deep})")
    try:
        rs = apps_v1.read_namespaced_replica_set(name=replicaset_name, namespace=namespace)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to get replicaset details for {replicaset_name} in namespace: {namespace}: {e.reason}")
        return f"[ERROR] Attempting to get replicaset details for {replicaset_name} in namespace: {namespace}: {e.reason}"

    if deep:
        return f"```json\n{json.dumps(rs.to_dict(), indent=2, default=str)}\n```"

    lines = [
        f"# ReplicaSet: {replicaset_name}",
        f"**Namespace**: {namespace}",
        "",
        "## Replica Status",
        f"- Desired: {rs.spec.replicas or 0}",
        f"- Current: {rs.status.replicas or 0}",
        f"- Ready: {rs.status.ready_replicas or 0}",
        f"- Available: {rs.status.available_replicas or 0}",
        "",
        "## Labels"
    ]


    # Add container images
    lines.append("")
    lines.append("## Container Images")
    container_images = [c.image for c in rs.spec.template.spec.containers]
    for image in container_images:
        lines.append(f"- `{image}`")

    return "\n".join(lines)




if __name__ == "__main__":
    print('-'*100)
    print(list_daemonset_names(namespace='default'))
    print('-'*100)
    print(list_daemonset_names(namespace='hello'))
    print('-'*100)  
    print(get_daemonset_details(daemonset_name='hello', namespace='default', deep=True))
    print('-'*100)
    print(get_daemonset_details(daemonset_name='hello', namespace='default', deep=False))
    print('-'*100)  
    print(get_daemonset_details(daemonset_name='hello', namespace='hello', deep=True))
    print('-'*100)
    print(get_daemonset_details(daemonset_name='hello', namespace='hello', deep=False))
    print('-'*100)
    print(list_statefulset_names(namespace='default'))
    print('-'*100)
    print(list_statefulset_names(namespace='hello'))
    print('-'*100)
    print(get_statefulset_details(statefulset_name='hello', namespace='default', deep=True))
    print('-'*100)
    print(get_statefulset_details(statefulset_name='hello', namespace='default', deep=False))
    print('-'*100)
    print(get_statefulset_details(statefulset_name='hello', namespace='hello', deep=True))
    print('-'*100)
    print(get_statefulset_details(statefulset_name='hello', namespace='hello', deep=False))
    print('-'*100)
    print(list_replicaset_names(namespace='default'))
    print('-'*100)
    print(list_replicaset_names(namespace='hello'))
    print('-'*100)  
    print(get_replicaset_details(replicaset_name='hello', namespace='default', deep=True))
    print('-'*100)
    print(get_replicaset_details(replicaset_name='hello', namespace='default', deep=False))
    print('-'*100)
    print(get_replicaset_details(replicaset_name='hello', namespace='hello', deep=True))
    print('-'*100)
    print(get_replicaset_details(replicaset_name='hello', namespace='hello', deep=False))