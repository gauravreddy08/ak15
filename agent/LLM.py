from openai import OpenAI
from dotenv import load_dotenv
import json
import logging
from src.utils import setup_logger
from agent import prompt as system_prompt
from typing import Dict, Any
import os

setup_logger()
logger = logging.getLogger(__name__)

from src import (
    Configuration,
    Deployment,
    Node,
    Pod,
    Service,
    Namespace,
    Workload
)

load_dotenv(override=True)

class LLM():
    """A class to handle interactions with the OpenAI LLM API for Kubernetes operations.

    This class manages conversations with the LLM, handles tool calls, and executes
    Kubernetes-related functions based on the LLM's responses.

    Attributes:
        model: OpenAI client instance
        model_name (str): Name of the LLM model to use
        messages (list): Conversation history
        tools (dict): Available tools/functions that can be called by the LLM
    """

    def __init__(self, model_name='gpt-4o', temperature=0.2):
        """Initialize the LLM instance.

        Args:
            model_name (str, optional): The name of the LLM model to use. Defaults to 'gpt-4o-mini'.
        """
        self.model = OpenAI()
        self.model_name = model_name
        self.temperature = temperature
        self.messages = []

        tools_path = os.path.join(os.path.dirname(__file__), 'tools.json')
        
        with open(tools_path, 'r') as f:
            self.tools = json.load(f)

    def call(self, prompt=None, tool_choice='auto'):
        """Make a call to the LLM with the given prompt.

        Args:
            prompt (str, optional): User input prompt. If provided, starts a new conversation.
                If None, continues existing conversation. Defaults to None.
            tool_choice (str, optional): Strategy for tool selection. Defaults to 'auto'.

        Returns:
            str: The LLM's response or the result of any tool calls
        """
        if prompt:  
            # Starting "new instance" if User Prompt is provided
            self.messages = [{'role': 'system', 'content': system_prompt.SYSTEM_PROMPT}]
            logger.critical("-"*100)
            logger.critical(f"[USER] Query: {prompt}")
            tool_choice = 'required'
            self.messages.append({'role': 'user', 'content': prompt})

        completion = self.model.chat.completions.create(
                        model=self.model_name,
                        messages=self.messages,
                        tools = self.tools,
                        tool_choice=tool_choice,
                        temperature=self.temperature
                    )
        
        response = completion.choices[0].message.content

        self.messages.append({'role': 'assistant', 'content': str(response)})

        tool_calls = completion.choices[0].message.tool_calls
        
        if tool_calls:
            self.messages.append(completion.choices[0].message)
            return self.function_call(tool_calls)
        else:
            logger.critical(f"[LLM] Response: {response}")
            return response
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute a Kubernetes-related tool with the provided arguments.

        Args:
            tool_name (str): Name of the tool to execute
            args (Dict[str, Any]): Arguments required by the tool

        Returns:
            str: Result of the tool execution, either as a JSON string for dict results
                or a plain string for other results

        Raises:
            Exception: If tool execution fails
        """
        try:
            tool_handlers = {
                'list_configmap_names': lambda: Configuration.list_configmap_names(
                    namespace=args.get('namespace')
                ),

                'get_configmap_details': lambda: Configuration.get_configmap_details(
                    configmap_name=args['configmap_name'],
                    namespace=args.get('namespace', 'default'),
                    deep=args.get('deep', False)
                ),

                'list_secret_names': lambda: Configuration.list_secret_names(
                    namespace=args.get('namespace', 'default')
                ),

                'get_secret_details': lambda: Configuration.get_secret_details(
                    secret_name=args['secret_name'],
                    namespace=args.get('namespace', 'default'),
                    deep=args.get('deep', False)
                ),    





                'list_deployments': lambda: Deployment.list_deployments(
                    namespace=args.get('namespace', 'default')
                ),

                'get_deployment_details': lambda: Deployment.get_deployment_details(
                    deployment_name=args['deployment_name'],
                    namespace=args.get('namespace', 'default'),
                    deep=args.get('deep', False)
                ),





                'list_all_namespaces': lambda: Namespace.list_all_namespaces(),

                'get_namespace_details': lambda: Namespace.get_namespace_details(
                    namespace=args['namespace'],
                    deep=args.get('deep', False)
                ),





                'get_cluster_version_info': lambda: Node.get_cluster_version_info(),

                'list_all_nodes': lambda: Node.list_all_nodes(),

                'get_node_details': lambda: Node.get_node_details(
                    node_name=args['node_name'],
                    deep=args.get('deep', False)
                ),



                'list_pods_in_namespace': lambda: Pod.list_pods_in_namespace(
                    namespace=args.get('namespace', 'default')
                ),

                'get_pod_details': lambda: Pod.get_pod_details(
                    pod_name=args['pod_name'],
                    namespace=args.get('namespace', 'default'),
                    deep=args.get('deep', False)
                ),


                'list_daemonset_names': lambda: Workload.list_daemonset_names(
                    namespace=args.get('namespace', 'default')
                ),

                'get_daemonset_details': lambda: Workload.get_daemonset_details(
                    daemonset_name=args['daemonset_name'],
                    namespace=args.get('namespace', 'default'),
                    deep=args.get('deep', False)
                ),

                'list_statefulset_names': lambda: Workload.list_statefulset_names(
                    namespace=args.get('namespace', 'default')
                ),

                'get_statefulset_details': lambda: Workload.get_statefulset_details(
                    statefulset_name=args['statefulset_name'],
                    namespace=args.get('namespace', 'default'),
                    deep=args.get('deep', False)
                ),    

                'list_replicaset_names': lambda: Workload.list_replicaset_names(
                    namespace=args.get('namespace', 'default')
                ),

                'get_replicaset_details': lambda: Workload.get_replicaset_details(
                    replicaset_name=args['replicaset_name'],
                    namespace=args.get('namespace', 'default'),
                    deep=args.get('deep', False)
                ),

                'list_service_names': lambda: Service.list_service_names(
                    namespace=args.get('namespace', 'default')
                ), 

                'get_service_details': lambda: Service.get_service_details(
                    service_name=args['service_name'],
                    namespace=args.get('namespace', 'default'),
                    deep=args.get('deep', False)
                )
            }

            if tool_name not in tool_handlers:
                return f"Tool '{tool_name}' not implemented"

            result = tool_handlers[tool_name]()
            return json.dumps(result) if isinstance(result, dict) else result

        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    

    def function_call(self, tool_calls):
        """Process and execute tool calls requested by the LLM.

        Handles multiple tool calls in sequence, adding their results to the conversation
        history and returning the LLM's final response.

        Args:
            tool_calls: Collection of tool calls from the LLM response

        Returns:
            str: The LLM's response after processing all tool calls

        Note:
            This method automatically adds tool responses to the conversation history
            and handles error cases by including error messages in the conversation.
        """
        for tool_call in tool_calls:
            if tool_call.function.name:
                try:
                    logger.critical(f"[FUNCTION CALL] Executing tool: {tool_call.function.name} ({tool_call.function.arguments})")
                    # logger.critical(f"[FUNCTION CALL] Arguments: {tool_call.function.arguments}")
                
                    # Parse the function arguments
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool and get the response
                    function_response = self.execute_tool(
                        tool_call.function.name,
                        function_args
                    )
                    
                    # Append the response to messages
                    self.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": function_response,
                    })
                    logger.critical(f"[RESPONSE] {function_response}")

                except Exception as e:
                    # Handle any errors during function execution
                    logger.critical(f"[FUNCTION CALL] [ERROR] Error executing {tool_call.function.name}: {str(e)}")
                    error_response = f"Error executing {tool_call.function.name}: {str(e)}"
                    self.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": error_response,
                    })
                
        return self.call(tool_choice='auto')
    
    