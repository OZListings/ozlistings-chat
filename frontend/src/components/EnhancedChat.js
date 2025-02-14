import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

const EnhancedChat = () => {
  const [email, setEmail] = useState('');
  const [hasEmail, setHasEmail] = useState(false);
  const [message, setMessage] = useState('');
  const [conversation, setConversation] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Initial greeting from the agent
  const INITIAL_GREETING = {
    sender: 'agent',
    text: `Welcome to Ozlistings! I'm here to help you explore real estate investment opportunities, particularly in Opportunity Zones. How can I assist you today?

Some topics we can discuss:
- Opportunity Zone investment benefits
- Available properties and locations
- Investment requirements and timelines
- Tax advantages and strategies`
  };

  useEffect(() => {
    if (hasEmail && conversation.length === 0) {
      setConversation([INITIAL_GREETING]);
    }
  }, [hasEmail]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation]);

  const handleEmailSubmit = async () => {
    if (!email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }
    setError(null);
    setHasEmail(true);
    await fetchProfile();
  };

  const fetchProfile = async () => {
    try {
      const response = await fetch(`http://localhost:8000/profile/${email}`);
      const data = await response.json();
      setProfile(data);
    } catch (err) {
      console.error("Error fetching profile:", err);
    }
  };

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMsg = { sender: 'user', text: message };
    setConversation(prev => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      // Send message for chat response
      const chatResponse = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: email, message: message })
      });
      const chatData = await chatResponse.json();

      // Update profile in parallel
      const profileResponse = await fetch('http://localhost:8000/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: email, message: message })
      });
      const profileData = await profileResponse.json();

      setProfile(profileData.profile);
      setConversation(prev => [...prev, { sender: 'agent', text: chatData.response }]);
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
      setMessage('');
    }
  };

  if (!hasEmail) {
    return (
      <div style={styles.centeredContainer}>
        <div style={styles.emailContainer}>
          <h1 style={styles.emailTitle}>Welcome to Ozlistings AI Assistant</h1>
          <div style={styles.disclaimerBox}>
            <p style={styles.disclaimerText}>
              This AI assistant provides general information about real estate investments.
              Not financial or legal advice.
            </p>
          </div>
          <input
            type="email"
            placeholder="Enter your email to get started"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={styles.emailInput}
          />

          {error && (
            <div style={styles.emailError}>
              {error}
            </div>
          )}

          <button
            onClick={handleEmailSubmit}
            style={styles.startButton}
          >
            Start Chat
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.appContainer}>
      <div style={styles.chatPanel}>
        <div style={styles.chatHeader}>
          <h2 style={styles.headerTitle}>Chat with Ozlistings Assistant</h2>
          <button onClick={fetchProfile} style={styles.profileButton}>Refresh Profile</button>
        </div>
        <div style={styles.chatWindow}>
          {conversation.map((msg, index) => (
            <div key={index} style={styles.messageWrapper(msg.sender)}>
              <div style={styles.messageBubble(msg.sender)}>
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
            </div>
          ))}
          {loading && (
            <div style={styles.loadingWrapper}>
              <div style={styles.loadingBubble}>
                Typing...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div style={styles.inputContainer}>
          <input
            type="text"
            placeholder="Type your message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            style={styles.messageInput}
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            style={styles.sendButton}
          >
            Send
          </button>
        </div>
      </div>
      <div style={styles.profilePanel}>
        <h2 style={styles.headerTitle}>Your Profile</h2>
        {profile ? (
          <div style={styles.profileDetails}>
            {Object.entries(profile).map(([key, value]) => (
              <div key={key} style={styles.profileItem}>
                <div style={styles.profileKey}>
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
                <div style={styles.profileValue}>
                  {Array.isArray(value)
                    ? value.join(', ') || 'Not specified'
                    : value?.toString() || 'Not specified'}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={styles.noProfileText}>
            No profile data yet. Chat to build your profile.
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  centeredContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    fontFamily: 'sans-serif', // Default sans-serif for broader compatibility
    background: '#f0f2f5', // Light gray background
  },
  emailContainer: {
    textAlign: 'center',
    background: '#fff',
    padding: '3rem',
    borderRadius: '0.75rem', // More rounded corners
    boxShadow: '0 5px 15px rgba(0,0,0,0.1)' // More pronounced shadow
  },
  emailTitle: {
    fontSize: '2rem',
    fontWeight: 'bold',
    color: '#333', // Darker title text
    marginBottom: '1.5rem'
  },
  disclaimerBox: {
    background: '#e8f0fe', // Light blue disclaimer box
    border: '1px solid #d0d7de',
    borderRadius: '0.5rem',
    padding: '1.25rem',
    marginBottom: '1.75rem'
  },
  disclaimerText: {
    color: '#555', // Muted disclaimer text
    fontSize: '0.9rem',
    margin: 0,
    lineHeight: '1.6'
  },
  emailInput: {
    padding: '1rem',
    width: '100%',
    marginBottom: '1.75rem',
    border: '1px solid #d0d7de',
    borderRadius: '0.5rem',
    fontSize: '1rem',
    color: '#333',
    outline: 'none'
  },
  emailError: {
    background: '#fce8e6',
    color: '#d93025',
    padding: '1rem',
    borderRadius: '0.5rem',
    fontSize: '0.9rem',
    marginBottom: '1.75rem'
  },
  startButton: {
    padding: '1rem 2rem',
    background: '#007bff', // Classic blue button
    color: '#fff',
    border: 'none',
    borderRadius: '0.5rem',
    cursor: 'pointer',
    fontSize: '1.1rem',
    fontWeight: '500',
    boxShadow: '0 2px 5px rgba(0,0,0,0.15)'
  },
  appContainer: {
    display: 'flex',
    height: '100vh',
    fontFamily: 'sans-serif', // Consistent font
    backgroundColor: '#f0f2f5' // Light gray app background
  },
  chatPanel: {
    flex: 3,
    display: 'flex',
    flexDirection: 'column',
    borderRight: '1px solid #e0e0e0'
  },
  chatHeader: {
    padding: '1.5rem',
    borderBottom: '1px solid #e0e0e0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff' // White header background
  },
  headerTitle: {
    margin: 0,
    fontSize: '1.75rem',
    fontWeight: 'bold',
    color: '#333' // Darker header title
  },
  profileButton: {
    padding: '0.75rem 1.5rem',
    background: 'transparent',
    color: '#555', // Muted profile button text
    border: '1px solid #ccc',
    borderRadius: '0.5rem',
    cursor: 'pointer',
    fontSize: '0.9rem'
  },
  chatWindow: {
    flex: 1,
    padding: '1.5rem',
    overflowY: 'auto',
    backgroundColor: '#f0f2f5', // Light gray chat window background
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem' // Spacing between messages
  },
  messageWrapper: (sender) => ({
    display: 'flex',
    justifyContent: sender === 'user' ? 'flex-end' : 'flex-start',
    width: '100%' // Ensure wrapper takes full width to align messages correctly
  }),
  messageBubble: (sender) => ({
    maxWidth: '70%',
    padding: '1rem 1.25rem',
    borderRadius: '1.25rem', // More rounded message bubbles
    backgroundColor: sender === 'user' ? '#007bff' : '#fff', // Blue for user, white for agent
    color: sender === 'user' ? '#fff' : '#333', // White text for user, dark for agent
    boxShadow: '0 2px 4px rgba(0,0,0,0.08)', // Subtle bubble shadow
    wordBreak: 'break-word' // Prevent text overflow
  }),
  loadingWrapper: {
    display: 'flex',
    justifyContent: 'flex-start'
  },
  loadingBubble: {
    padding: '1rem 1.25rem',
    borderRadius: '1.25rem',
    backgroundColor: '#fff',
    boxShadow: '0 2px 4px rgba(0,0,0,0.08)',
    color: '#555' // Muted loading text
  },
  inputContainer: {
    padding: '1.5rem',
    background: '#fff', // White input container background
    borderTop: '1px solid #e0e0e0',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem'
  },
  messageInput: {
    flex: 1,
    padding: '1rem',
    borderRadius: '0.5rem',
    border: '1px solid #d0d7de',
    fontSize: '1rem',
    color: '#333',
    outline: 'none',
    boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.05)' // Subtle input shadow
  },
  sendButton: {
    padding: '1rem 1.75rem',
    background: '#007bff', // Blue send button
    color: '#fff',
    border: 'none',
    borderRadius: '0.5rem',
    cursor: 'pointer',
    fontSize: '1.1rem',
    fontWeight: '500',
    boxShadow: '0 2px 5px rgba(0,0,0,0.15)'
  },
  profilePanel: {
    flex: 1,
    padding: '2rem',
    overflowY: 'auto',
    backgroundColor: '#f8f9fa', // Slightly darker profile panel background
    borderLeft: '1px solid #e0e0e0'
  },
  profileDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem'
  },
  profileItem: {
    marginBottom: '1rem'
  },
  profileKey: {
    fontSize: '1rem',
    fontWeight: '600',
    color: '#4a5568',
    marginBottom: '0.5rem'
  },
  profileValue: {
    fontSize: '1rem',
    color: '#555',
    lineHeight: '1.5'
  },
  noProfileText: {
    color: '#718096',
    fontSize: '1rem',
    textAlign: 'center',
    marginTop: '2rem'
  }
};

export default EnhancedChat;