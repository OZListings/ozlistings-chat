import React, { useState } from 'react';

function App() {
  const [email, setEmail] = useState('');
  const [hasEmail, setHasEmail] = useState(false);
  const [message, setMessage] = useState('');
  const [conversation, setConversation] = useState([]);

  // Function to send a chat message
  const sendMessage = async () => {
    if (!message.trim()) return;

    // Append the user's message to the conversation
    const userMsg = { sender: 'user', text: message };
    setConversation(prev => [...prev, userMsg]);

    // Call the backend /chat endpoint
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: email,
          message: message
        })
      });
      const data = await response.json();
      
      // Append the agent's response to the conversation
      const agentMsg = { sender: 'agent', text: data.response };
      setConversation(prev => [...prev, agentMsg]);
    } catch (err) {
      console.error('Error sending message:', err);
    }
    setMessage('');
  };

  // If the email isn't set, show the email capture screen
  if (!hasEmail) {
    return (
      <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
        <h1>Welcome to Ozlistings AI Agent</h1>
        <p style={{ color: 'gray', fontSize: '0.9em' }}>
          Disclaimer: This is not financial or legal advice.
        </p>
        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ padding: '10px', width: '300px', marginRight: '10px' }}
        />
        <button onClick={() => { if(email.trim()) setHasEmail(true); }}>
          Start Chat
        </button>
      </div>
    );
  }

  // Main chat interface
  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>Ozlistings AI Chat</h1>
      <div
        style={{
          border: '1px solid #ccc',
          padding: '10px',
          height: '400px',
          overflowY: 'scroll',
          marginBottom: '10px'
        }}
      >
        {conversation.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
            <p>
              <strong>{msg.sender === 'user' ? 'You' : 'Agent'}:</strong> {msg.text}
            </p>
          </div>
        ))}
      </div>
      <div>
        <input
          type="text"
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => { if(e.key === 'Enter') sendMessage(); }}
          style={{ width: '80%', padding: '10px' }}
        />
        <button onClick={sendMessage} style={{ padding: '10px' }}>
          Send
        </button>
      </div>
    </div>
  );
}

export default App;