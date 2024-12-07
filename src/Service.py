"""
Kubernetes Service Module
Handles operations for Services, providing formatted information retrieval.
"""

import json
import logging
from kubernetes import client, config
from src.utils import setup_logger

setup_logger()  
logger = logging.getLogger(__name__)

config.load_kube_config()
v1 = client.CoreV1Api()

def list_service_names(namespace: str = 'default') -> str:
    """Lists all Services in the specified namespace."""
    logger.critical(f"[FUNCTION] Attempting to list services in namespace: {namespace}")
    services = v1.list_namespaced_service(namespace=namespace).items

    if not services:
        return f"No Services found in namespace {namespace}"
    
    service_names = [s.metadata.name for s in services]
    lines = [
        f"# Services in namespace: {namespace}",
        ""
    ]
    for name in service_names:
        lines.append(f"- {name}")
    return "\n".join(lines)


def get_service_details(service_name: str, namespace: str = 'default', deep: bool = False) -> str:
    """
    Gets detailed information about a specific Service.
    
    Args:
        service_name: Name of the Service
        namespace: Kubernetes namespace
        deep: If True, returns raw JSON data instead of formatted markdown
    """
    logger.critical(f"[FUNCTION] Attempting to get service details for {service_name} in namespace: {namespace} (deep={deep})")

    try:
        svc = v1.read_namespaced_service(name=service_name, namespace=namespace)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to get service details for {service_name} in namespace: {namespace}: {e.reason}")
        return f"[ERROR] Attempting to get service details for {service_name} in namespace: {namespace}: {e.reason}"

    if deep:
        return f"```json\n{json.dumps(svc.to_dict(), indent=2, default=str)}\n```"

    lines = [
        f"# Service: {service_name}",
        f"- **Namespace**: {namespace}",
        f"- **Type**: {svc.spec.type}",
        f"- **Cluster IP**: {svc.spec.cluster_ip}",
        "",
        "## Labels",
        "\n".join(f"- {k}: {v}" for k, v in (svc.metadata.labels or {}).items()) or "None",
        "",
        "## Ports"
    ]

    for p in (svc.spec.ports or []):
        port_info = [f"- Port {p.port} ({p.protocol})"]
        if p.node_port:
            port_info.append(f"  - NodePort: {p.node_port}")
        if p.target_port:
            port_info.append(f"  - TargetPort: {p.target_port}")
        lines.extend(port_info)

    return "\n".join(lines)

if __name__ == "__main__":
    print(list_service_names(namespace='default'))
    print('-'*100)
    print(list_service_names(namespace='hello'))
    print('-'*100)
    print(get_service_details(service_name='db', namespace='default', deep=False))  
    print('-'*100)
    print(get_service_details(service_name='db', namespace='hello', deep=False))
    print('-'*100)
    print(get_service_details(service_name='db', namespace='default', deep=True))
    print('-'*100)
    print(get_service_details(service_name='db', namespace='hello', deep=True))