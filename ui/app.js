// Because we use Ingress, we don't need a port number.
const API_URL = "/api/dashboard";

const stackDisplay = document.getElementById('stack-data');
const listDisplay = document.getElementById('list-data');
const graphDisplay = document.getElementById('graph-data');
const errorMsg = document.getElementById('error-msg');

async function fetchData() {
    try {
        const response = await fetch(API_URL);

        // If the server returns an error (like 404 or 500), throw an error
        if (!response.ok) {
            throw new Error(`Server Error: ${response.status}`);
        }

        const data = await response.json();

        // 1. Update C Stack (Stack Pop)
        if (stackDisplay) {
            if (data.stack_pop) {
                // We use innerHTML to allow the <br> tag for line breaks
                stackDisplay.innerHTML = `
                    <strong>Value:</strong> ${data.stack_pop.value} <br>
                    <strong>Status:</strong> ${data.stack_pop.status}
                `;
            } else {
                stackDisplay.innerText = data.stack_error || "No data";
            }
        }

        // 2. Update Java Linked List
        if (listDisplay) {
            listDisplay.innerText = data.linked_list || "No data";
        }

        // 3. Update Python Graph
        if (graphDisplay) {
            // JSON.stringify makes the object readable with indentation
            graphDisplay.innerText = JSON.stringify(data.graph, null, 2);
        }

        // Clear any previous error messages
        if (errorMsg) errorMsg.innerText = "";

    } catch (error) {
        console.error("Fetch Error:", error);
        if (errorMsg) {
            // This helps you debug if something goes wrong again
            errorMsg.innerText = "Error loading data. Check console for details.";
        }
    }
}

// Run immediately when the page loads
document.addEventListener('DOMContentLoaded', fetchData);
