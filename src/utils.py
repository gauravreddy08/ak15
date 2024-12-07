import logging
from kubernetes import client, config

def setup_logger():
    logging.basicConfig(
        filename='agent.log',
        filemode='a',
        level=logging.CRITICAL,
        format='%(name)s - %(levelname)s - %(message)s'
    )

def load_kube_config():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    version_api = client.VersionApi()
    return v1, apps_v1, version_api