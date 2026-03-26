import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import { sendChatMessage, clearChatHistory } from '../services/api';

const EXAMPLE_QUERIES = [
  "Which products are associated with the highest number of billing documents?",
  "Show me all sales orders that were delivered but not billed",
  "Trace the full flow of a billing document",
  "How many orders are there in total?",
  "Which customers have the most orders?",
  "Show me broken flows where delivery exists but no invoice",
  "What tables are available in the dataset?",
];

function ChatInterface({ onHighlightNodes }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (messageText = null) => {
    const text = messageText || input.trim();
    if (!text || isLoading) return;

    const userMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage(text);
      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        sql_query: response.sql_query,
        results: response.results,
        query_type: response.query_type,
        highlighted_nodes: response.highlighted_nodes,
      };
      setMessages(prev => [...prev, assistantMessage]);

      if (response.highlighted_nodes && response.highlighted_nodes.length > 0) {
        onHighlightNodes(response.highlighted_nodes);
      }
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${error.message}. Please try again.`,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = async () => {
    setMessages([]);
    try {
      await clearChatHistory();
    } catch (e) {
      // ignore
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h2>💬 Query Assistant</h2>
        {messages.length > 0 && (
          <button onClick={handleClear}>Clear</button>
        )}
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <h3>Welcome! 👋</h3>
            <p>
              Ask questions about orders, deliveries, invoices, payments, customers, and products.
              Your queries will be converted to SQL and executed on the dataset.
            </p>
            <div className="example-queries">
              {EXAMPLE_QUERIES.map((q, i) => (
                <button
                  key={i}
                  className="example-query"
                  onClick={() => handleSend(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}

        {isLoading && (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your business data..."
            disabled={isLoading}
          />
          <button onClick={() => handleSend()} disabled={isLoading || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;