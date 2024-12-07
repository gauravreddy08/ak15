<div style="position: relative; padding-bottom: 56.25%; height: 0;"><iframe src="https://www.loom.com/embed/b26b3b4641a44c8dbc01cc3f243c4dee?sid=3fc726ec-c997-43c9-b11d-4c1101d1c3eb" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

# AK15 (Agentic Kubernetes 15)

AK15 is a Kubernetes agent that uses a human-like approach to query the Kubernetes API. **15** is the number of functions it has access to.

> **Note:** I forgot to mention this in the video, the function choosing, arguments, and setting deep=true are all done by the LLM itself.

## Motivation & Approach

When building an AI system, my first instinct is to solve the problem as a human would. 

> It took me 2-3 days to first understand the problem from a human perspective.

The easy route would have been to retrieve all Kubernetes cluster data and feed it to the LLM, hoping it would find the answer while costing ~$1 per prompt due to the massive context length. 

Instead, I asked myself: "How would a human handle these queries?"

A human wouldn't look at the entire cluster state to answer **"How many pods are running?**" They'd specifically check pod information. 

## How It Works

The agent has access to 15 specialized functions, each retrieving specific Kubernetes component information. It intelligently decides which function to call based on the query, similar to how a human would navigate the Kubernetes cluster.

### Function Types

1. **List Functions** (`list_*`): Return names of specific components
2. **Get Functions** (`get_*`): Retrieve detailed information about a specific component
   - Has a `deep` parameter that provides even more detailed information when needed
   - LLM will retry with `deep=true` if initial attempt doesn't yield enough information

The agent optimizes costs by making targeted function calls. Here's a token usage comparison for Pod-related functions:

| Function Call | Tokens | Use Case |
|--------------|---------|----------|
| `list_pods_in_namespace()` | 222 | Quick pod enumeration |
| `get_pod_details(deep=false)` | 224 | Basic pod information |
| `get_pod_details(deep=true)` | 3,369 | Detailed pod analysis |

This design allows the agent to:
- Start with lightweight calls (list/basic get)
- Only use expensive deep retrievals when necessary
- Save ~93% tokens when basic info suffices

## How good is my agent?

When asked "**How many services are of type ClusterIP?**", the agent:

1. First lists all services using `list_service_names(namespace="default")`
   - Found: api, db, kubernetes, web

2. Then checks each service's type using `get_service_details()`:
   - api: ClusterIP
   - db: ClusterIP  
   - kubernetes: ClusterIP
   - web: LoadBalancer

3. Counts services with type=ClusterIP
   - Total count: 3 (api, db, kubernetes)

4. Returns the final count: 3

This methodical approach ensures accuracy and demonstrates the agent's human-like reasoning process.

## Technical Details

### Output Format
- Functions output in Markdown format
  - LLMs understand Markdown well
  - 15-20% more cost-effective than JSON responses
  - Better readability for debugging

### Code Structure
- `src/`: Contains component-specific modules
  - Separate files for different Kubernetes components (pods, services, etc.)
- `agent/`: LLM interaction and tool definitions
  - `LLM.py`: Handles OpenAI API interactions
  - `tools.json`: Function definitions and parameters
  - `prompt.py`: System prompt defining agent behavior

The codebase follows a modular approach, making it easy to add new Kubernetes component handlers or modify existing ones without affecting the core LLM interaction logic.

## Results

The agent successfully handles a wide range of Kubernetes queries with high accuracy and cost efficiency. In testing across 30 different queries, it consistently provided accurate responses while minimizing API costs by making targeted function calls instead of processing the entire cluster state.

### Example Queries and Responses
```
Q: How many containers are running in the 'web' pod?
A: None

Q: What is the node port of the 'web' service?
A: 31465

Q: Is the 'api' deployment fully available?
A: Yes

Q: How many pods are labeled with 'app=api'?
A: 5

Q: What is the port exposed by the 'db' service?
A: 5432

Q: Is the 'kubernetes' service in the default namespace?
A: Yes

Q: How many pods are running the 'db' deployment?
A: 1

Q: What is the ClusterIP of the 'kubernetes' service?
A: 10.96.0.1

Q: Are all pods in 'Running' state?
A: Yes

Q: How many services are of type ClusterIP?
A: 3
```
