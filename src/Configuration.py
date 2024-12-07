"""
Kubernetes Configuration Module
Handles operations for ConfigMaps and Secrets, providing formatted information retrieval.
"""

import json
import logging
from kubernetes import client, config
from src.utils import setup_logger

setup_logger()  
logger = logging.getLogger(__name__)

config.load_kube_config()
v1 = client.CoreV1Api()

def list_configmap_names(namespace: str = 'default') -> str:
    """Lists all ConfigMaps in the specified namespace."""
    logger.critical(f"[FUNCTION] Attempting to list configmaps in namespace: {namespace}")
    cms = v1.list_namespaced_config_map(namespace=namespace).items
    
    if len(cms) == 0:
        return f"No ConfigMaps found in namespace {namespace}"
    
    lines = [
        f"# ConfigMaps in namespace: {namespace}",
        ""  # Empty line for better readability
    ]
    
    if not cms:
        lines.append("No ConfigMaps found in this namespace.")
    else:
        for cm in cms:
            lines.append(f"- {cm.metadata.name}")

    return "\n".join(lines)

def get_configmap_details(configmap_name: str, namespace: str = 'default', deep: bool = False) -> str:
    """
    Gets detailed information about a specific ConfigMap.
    
    Args:
        configmap_name: Name of the ConfigMap
        namespace: Kubernetes namespace
        deep: If True, returns raw JSON data instead of formatted markdown
    """
    logger.critical(f"[FUNCTION] Attempting to get configmap details for {configmap_name} in namespace: {namespace} (deep={deep})")
    try:
        cm = v1.read_namespaced_config_map(name=configmap_name, namespace=namespace)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to get configmap details for {configmap_name} in namespace: {namespace}: {e.reason}")
        return f"[ERROR] Attempting to get configmap details for {configmap_name} in namespace: {namespace}: {e.reason}"

    if deep:
        return f"```json\n{json.dumps(cm.to_dict(), indent=2, default=str)}\n```"

    sections = [
        f"# ConfigMap: {configmap_name}",
        f"**Namespace**: {namespace}\n",
        "## Labels",
        "\n".join(f"- {k}: {v}" for k, v in (cm.metadata.labels or {}).items()) or "None",
        "\n## Data Entries"
    ]

    if cm.data:
        sections.extend(f"### {key}\n```\n{value}\n```" for key, value in cm.data.items())
    else:
        sections.append("No data entries found.")

    if cm.binary_data:
        sections.extend([
            "\n## Binary Data Entries",
            "\n".join(f"- {key} (binary)" for key in cm.binary_data.keys())
        ])

    return "\n".join(sections)

def list_secret_names(namespace: str = 'default') -> str:
    """Lists all Secrets in the specified namespace."""
    logger.critical(f"[FUNCTION] Attempting to list secrets in namespace: {namespace}")
    secrets = v1.list_namespaced_secret(namespace=namespace).items

    if not secrets:
        return "No Secrets found in this namespace."
    
    lines = [f"# Secrets in namespace: {namespace}", ""]
    for secret in secrets:
        lines.append(f"- {secret.metadata.name}")
        
    return "\n".join(lines)

def get_secret_details(secret_name: str, namespace: str = 'default', deep: bool = False) -> str:
    """
    Gets detailed information about a specific Secret.
    
    Args:
        secret_name: Name of the Secret
        namespace: Kubernetes namespace
        deep: If True, returns raw JSON data instead of formatted markdown
    """
    logger.critical(f"[FUNCTION] Attempting to get secret details for {secret_name} in namespace: {namespace} (deep={deep})")
    try:
        secret = v1.read_namespaced_secret(name=secret_name, namespace=namespace)
    except Exception as e:
        logger.error(f"[ERROR] Attempting to get secret details for {secret_name} in namespace: {namespace}: {e.reason}")
        return f"[ERROR] Attempting to get secret details for {secret_name} in namespace: {namespace}: {e.reason}"

    if deep:
        return f"```json\n{json.dumps(secret.to_dict(), indent=2, default=str)}\n```"

    return "\n".join([
        f"# Secret: {secret_name}",
        f"**Namespace**: {namespace}",
        f"**Type**: {secret.type}",
        "",
        "## Labels",
        "\n".join(f"- {k}: {v}" for k, v in (secret.metadata.labels or {}).items()) or "None",
        "",
        "## Data Keys",
        "\n".join(f"- {k}" for k in (secret.data or {}).keys()) or "No data keys found."
    ])

if __name__ == "__main__":
    print(list_configmap_names(namespace='default'))
    print('-'*100)
    print(list_configmap_names(namespace='hello'))
    print('-'*100)
    print(get_configmap_details(configmap_name='db-schema', namespace='default', deep=True))    
    print('-'*100)
    print(get_configmap_details(configmap_name='db-schema', namespace='default', deep=False))    
    print('-'*100)
    print(get_configmap_details(configmap_name='db-schema', namespace='hello', deep=True))    
    print('-'*100)
    print(get_configmap_details(configmap_name='db-schema', namespace='hello', deep=False))   
    print('-'*100)
    print(get_configmap_details(configmap_name='db', deep=True))    
    print('-'*100)
    print(get_configmap_details(configmap_name='db', deep=False))  
    print('-'*100)
    print(list_secret_names(namespace='default'))
    print('-'*100)
    print(list_secret_names(namespace='hello')) 
    print('-'*100)
    print(get_secret_details(secret_name='db-secret', namespace='default', deep=True))
    print('-'*100)
    print(get_secret_details(secret_name='db-secret', namespace='default', deep=False))
    print('-'*100)
    print(get_secret_details(secret_name='db-secret', namespace='hello', deep=True))
    print('-'*100)