import logging
from kubernetes import client, config
import os

def setup_logger():
    # Get absolute path for the log file
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agent.log')
    
    try:
        # Create the file if it doesn't exist
        with open(log_file, 'w') as _:
            pass
        
        # Configure file handler explicitly
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.CRITICAL)
        
        # Create formatter and add it to the handler
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Get the root logger and add the handler
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.CRITICAL)
        
        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add our file handler
        root_logger.addHandler(file_handler)
        
    except Exception as e:
        print(f"Error setting up logger: {str(e)}")
        raise

def load_kube_config():
    kubeconfig_path = os.path.expanduser("~/.kube/config")
    config.load_kube_config(config_file=kubeconfig_path)
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    version_api = client.VersionApi()
    return v1, apps_v1, version_api