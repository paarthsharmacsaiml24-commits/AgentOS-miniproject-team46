import { useState } from "react";

function App() {
    const [message, setMessage] = useState("");
    const [response, setResponse] = useState("");

    const sendMessage = async () => {
        if (!message.trim()) {
            return;
        }

        const result = await fetch("http://127.0.0.1:8000/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await result.json();

        setResponse(data.response);
    };

    return (
        <div>
            <h1>AgentOS</h1>

            <p>Autonomous Multi-Agent Operating System</p>

            <input
                type="text"
                placeholder="Tell AgentOS what you want..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
            />

            <button onClick={sendMessage}>
                Send
            </button>

            <p>{response}</p>
        </div>
    );
}

export default App;