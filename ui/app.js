// Because we use Ingress, we don't need a port number.
// The browser sends this request to the same domain it is currently on.
const API_URL = "/api/dashboard";

const refreshBtn = document.getElementById('refresh-btn');
const stackDisplay = document.getElementById('stack-data');
const listDisplay = document.getElementById('list-data');
const graphDisplay = document.getElementById('graph-data');
const errorMsg = document.getElementById('error-msg');

async function fetchData() {
    refreshBtn.disabled = true;
    refreshBtn.innerText = "Loading...";
    errorMsg.innerText = "";

    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error("Network response was not ok");

        const data = await response.json();

        // 1. C Stack
        if(data.stack_pop) {
            stackDisplay.innerHTML = `Value: ${data.stack_pop.value} <br> Status: ${data.stack_pop.status}`;
        } else {
            stackDisplay.innerText = data.stack_error || "Error";
        }

        // 2. Java List
        listDisplay.innerText = data.linked_list || data.linked_list_error || "Error";

        // 3. Python Graph
        if(data.graph) {
            graphDisplay.innerText = JSON.stringify(data.graph, null, 2);
        } else {
            graphDisplay.innerText = data.graph_error || "Error";
        }

    } catch (error) {
        console.error(error);
        errorMsg.innerText = "Could not reach Backend. Is Minikube Tunnel running?";
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.innerText = "Fetch Data";
    }
}

refreshBtn.addEventListener('click', fetchData);