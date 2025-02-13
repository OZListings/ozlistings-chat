import React, { useState, useEffect, useRef } from 'react';

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
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        padding: '1rem'
      }}>
        <div style={{
          background: 'white',
          borderRadius: '0.5rem',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          padding: '2rem',
          maxWidth: '24rem',
          width: '100%'
        }}>
          <h1 style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            marginBottom: '1.5rem',
            textAlign: 'center'
          }}>
            Welcome to Ozlistings AI Assistant
          </h1>
          
          <div style={{
            background: '#f8f9fa',
            border: '1px solid #e9ecef',
            borderRadius: '0.375rem',
            padding: '1rem',
            marginBottom: '1.5rem'
          }}>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#495057' }}>
              This AI assistant provides general information about real estate investments. 
              Not financial or legal advice.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <input
              type="email"
              placeholder="Enter your email to get started"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #dee2e6',
                borderRadius: '0.375rem',
                outline: 'none'
              }}
            />
            
            {error && (
              <div style={{
                background: '#fff5f5',
                color: '#c53030',
                padding: '0.75rem',
                borderRadius: '0.375rem',
                fontSize: '0.875rem'
              }}>
                {error}
              </div>
            )}

            <button
              onClick={handleEmailSubmit}
              style={{
                width: '100%',
                padding: '0.75rem',
                background: '#4299e1',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                fontWeight: '500'
              }}
            >
              Start Chat
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      background: '#f8f9fa'
    }}>
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{
          background: 'white',
          padding: '1rem',
          borderBottom: '1px solid #e9ecef',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{
            margin: 0,
            fontSize: '1.25rem',
            fontWeight: '600'
          }}>
            Ozlistings Assistant
          </h2>
          <button
            onClick={fetchProfile}
            style={{
              padding: '0.5rem 1rem',
              background: 'transparent',
              color: '#4299e1',
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            Refresh Profile
          </button>
        </div>

        <div style={{
          flex: 1,
          display: 'flex'
        }}>
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{
              flex: 1,
              overflowY: 'auto',
              padding: '1rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem'
            }}>
              {conversation.map((msg, index) => (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start'
                  }}
                >
                  <div style={{
                    maxWidth: '70%',
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    background: msg.sender === 'user' ? '#4299e1' : 'white',
                    color: msg.sender === 'user' ? 'white' : 'black',
                    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
                  }}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{
                  display: 'flex',
                  justifyContent: 'flex-start'
                }}>
                  <div style={{
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    background: 'white',
                    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
                  }}>
                    Typing...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div style={{
              padding: '1rem',
              background: 'white',
              borderTop: '1px solid #e9ecef'
            }}>
              <div style={{
                display: 'flex',
                gap: '0.5rem'
              }}>
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
                  style={{
                    flex: 1,
                    padding: '0.75rem',
                    border: '1px solid #e9ecef',
                    borderRadius: '0.375rem',
                    outline: 'none'
                  }}
                />
                <button
                  onClick={sendMessage}
                  disabled={loading}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: '#4299e1',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    opacity: loading ? 0.7 : 1
                  }}
                >
                  Send
                </button>
              </div>
            </div>
          </div>

          <div style={{
            width: '20rem',
            background: 'white',
            borderLeft: '1px solid #e9ecef',
            padding: '1rem'
          }}>
            <h3 style={{
              margin: '0 0 1rem 0',
              fontSize: '1rem',
              fontWeight: '600'
            }}>
              Profile Information
            </h3>
            {profile ? (
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem'
              }}>
                {Object.entries(profile).map(([key, value]) => (
                  <div key={key}>
                    <div style={{
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: '#4a5568',
                      marginBottom: '0.25rem'
                    }}>
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                    <div style={{
                      fontSize: '0.875rem'
                    }}>
                      {Array.isArray(value)
                        ? value.join(', ') || 'Not specified'
                        : value?.toString() || 'Not specified'}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                color: '#718096',
                fontSize: '0.875rem'
              }}>
                No profile data yet. Continue chatting to build your profile.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedChat;