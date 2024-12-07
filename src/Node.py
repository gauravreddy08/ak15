"""
Kubernetes Node Operations Module
Provides functions to retrieve and format information about Kubernetes nodes and cluster version.
"""

from kubernetes import client, config
import json
import logging
from src.utils import setup_logger, load_kube_config

setup_logger()
logger = logging.getLogger(__name__)

v1, apps_v1, version_api = load_kube_config()

def get_cluster_version_info() -> str:
    """Gets and formats Kubernetes cluster version details."""
    logger.critical("[RUNNING] Attempting to get cluster version info")
    version_info = version_api.get_code()
    lines = [
        "# Kubernetes Cluster Version",
        f"- **Major Version**: {version_info.major}",
        f"- **Minor Version**: {version_info.minor}", 
        f"- **Git Version**: {version_info.git_version}"
    ]
    return "\n".join(lines)


def list_all_nodes() -> str:
    """Lists all Kubernetes nodes in the cluster."""
    logger.critical("[RUNNING] Attempting to list all nodes") 

    try:
        nodes = v1.list_node()
        node_names = [node.metadata.name for node in nodes.items]

        # Create markdown formatted output
        lines = ["# Present Nodes", ""]
        for node in node_names:
            lines.append(f"- {node}")
        
        return "\n".join(lines)

    except Exception as e:
        logger.error(f"[ERROR] Attempting to list all nodes: {e}")
        return f"Error: {e.reason}"

def get_node_details(node_name: str, deep: bool = False) -> str:
    """
    Gets detailed information about a specific Kubernetes node.
    
    Args:
        node_name: Name of the node to query
        deep: If True, returns raw JSON data instead of formatted markdown
    """
    logger.critical(f"[RUNNING] Attempting to get node info for {node_name} (deep={deep})")

    try:
        node = v1.read_node(node_name)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to get node info for {node_name}: {e}")
        return f"[ERROR] Attempting to get node info for {node_name}: {e.reason}"

    # If deep is True, return all node info directly in JSON.
    if deep:
        return f"```json\n{json.dumps(node.to_dict(), indent=2, default=str)}\n```"

    labels = node.metadata.labels or {}
    conditions = node.status.conditions or []
    addresses = {addr.type: addr.address for addr in node.status.addresses}
    capacity = node.status.capacity or {}
    allocatable = node.status.allocatable or {}
    node_info = node.status.node_info
    taints = node.spec.taints or []

    node_role = "Unknown"
    for k in labels:
        if k.startswith("node-role.kubernetes.io/"):
            node_role = k.split("/")[-1]
            break

    lines = [
        f"# Node Information for: {node_name}",
        f"## Role: {node_role}",
        "## Conditions:"
    ]
    for c in conditions:
        lines += [
            f"- Type: {c.type}",
            f"  Status: {c.status}",
            f"  Reason: {c.reason}",
            f"  Message: {c.message}"
        ]
    lines += ["", "## Labels:"]
    lines += [f"- {k}: {v}" for k, v in labels.items()] if labels else ["None"]
    lines += ["", "## Addresses:"]
    lines += [f"- {t}: {a}" for t, a in addresses.items()] if addresses else ["None"]
    lines += ["", "## Capacity:"]
    lines += [f"- {k}: {v}" for k, v in capacity.items()] if capacity else ["None"]
    lines += ["", "## Allocatable:"]
    lines += [f"- {k}: {v}" for k, v in allocatable.items()] if allocatable else ["None"]
    lines += [
        "",
        "## Node System Info:",
        f"- OS Image: {node_info.os_image}",
        f"- Container Runtime: {node_info.container_runtime_version}",
        f"- Kubelet Version: {node_info.kubelet_version}",
        "",
        "## Taints:"
    ]
    lines += [f"- {t.key}={t.value}, Effect={t.effect}" for t in taints] if taints else ["None"]

    return "\n".join(lines)

if __name__ == "__main__":
    print(list_all_nodes())
    print('-'*100)
    print(get_node_details("hello", deep=False))
    print('-'*100)
    print(get_node_details("hahaaaa", deep=True))