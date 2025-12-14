from flask import Flask, jsonify, request
# CORS is not strictly required since we use Ingress (Same Origin)
import requests
import os
import random

app = Flask(__name__)

# --- Kubernetes Service Discovery ---
# These hostnames match the 'metadata: name' in your K8s Service YAML files.
# Kubernetes internal DNS resolves these to the correct Pod IPs.
STACK_SERVICE_URL = "http://stack-service:5001"
LINKEDLIST_SERVICE_URL = "http://linkedlist-service:5002"
GRAPH_SERVICE_URL = "http://graph-service:5003"


@app.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """
    Aggregator Endpoint:
    Calls all internal microservices and combines their data into one JSON response.
    """
    response_data = {}

    # --- 1. Interact with Stack Service (Pure C) ---
    try:
        # Generate a random number to push
        val_to_push = random.randint(1, 100)

        # Step A: Push to Stack
        # The C server expects a POST request with a query parameter 'val'
        push_url = f"{STACK_SERVICE_URL}/push?val={val_to_push}"
        requests.post(push_url, timeout=2)

        # Step B: Pop from Stack
        # The C server returns JSON on GET /pop
        pop_url = f"{STACK_SERVICE_URL}/pop"
        stack_response = requests.get(pop_url, timeout=2)

        if stack_response.status_code == 200:
            response_data['stack_pop'] = stack_response.json()
        else:
            response_data['stack_error'] = f"Status Code: {stack_response.status_code}"

    except requests.exceptions.RequestException as e:
        print(f"❌ Stack Service Error: {e}")
        response_data['stack_error'] = "Service Unreachable"

    # --- 2. Interact with Linked List Service (Java) ---
    try:
        # Generate a random node name
        node_val = f"Node-{random.randint(100, 999)}"

        # Step A: Add to List
        # Java server expects GET /add?val=...
        add_url = f"{LINKEDLIST_SERVICE_URL}/add?val={node_val}"
        requests.get(add_url, timeout=2)

        # Step B: Display List
        display_url = f"{LINKEDLIST_SERVICE_URL}/display"
        list_response = requests.get(display_url, timeout=2)

        if list_response.status_code == 200:
            # Java sends plain text, not JSON
            response_data['linked_list'] = list_response.text
        else:
            response_data['linked_list_error'] = f"Status: {list_response.status_code}"

    except requests.exceptions.RequestException as e:
        print(f"❌ LinkedList Service Error: {e}")
        response_data['linked_list_error'] = "Service Unreachable"

    # --- 3. Interact with Graph Service (Python) ---
    try:
        # Step A: Get Graph Data
        graph_url = f"{GRAPH_SERVICE_URL}/graph"
        graph_response = requests.get(graph_url, timeout=2)

        if graph_response.status_code == 200:
            response_data['graph'] = graph_response.json()
        else:
            response_data['graph_error'] = f"Status: {graph_response.status_code}"

    except requests.exceptions.RequestException as e:
        print(f"❌ Graph Service Error: {e}")
        response_data['graph_error'] = "Service Unreachable"

    return jsonify(response_data)


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check for Kubernetes liveness probes"""
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    # Run on port 5000 inside the container
    app.run(host='0.0.0.0', port=5000, debug=True)