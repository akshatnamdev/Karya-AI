import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import Layout from '../components/Layout';
import aiService from '../services/aiService';
import { useAuth } from '../context/AuthContext'; // Import useAuth to get user role
import { Send, Loader2 } from 'lucide-react';
import '../styles/Assistant.css';

function formatAssistantContent(text) {
  if (!text) return '';
  return text
    .replace(/🔴/g, '[[DOT_RED]]')
    .replace(/🟡/g, '[[DOT_AMBER]]')
    .replace(/🟢/g, '[[DOT_GREEN]]');
}

function processDotTokens(nodes) {
  if (nodes == null) return null;
  if (Array.isArray(nodes)) {
    return nodes.map((node, idx) => <span key={idx}>{processDotTokens(node)}</span>);
  }
  if (typeof nodes === 'string') {
    const parts = nodes.split(/(\[\[DOT_(?:RED|AMBER|GREEN)\]\])/g);
    return parts.map((chunk, i) => {
      if (chunk === '[[DOT_RED]]') {
        return <span key={i} className="status-dot red" />;
      }
      if (chunk === '[[DOT_AMBER]]') {
        return <span key={i} className="status-dot amber" />;
      }
      if (chunk === '[[DOT_GREEN]]') {
        return <span key={i} className="status-dot green" />;
      }
      return chunk;
    });
  }
  return nodes;
}

function AssistantMarkdown({ content }) {
  const prepared = formatAssistantContent(content);

  return (
    <div className="message-content markdown">
      <ReactMarkdown
        components={{
          p: ({ children }) => <p>{processDotTokens(children)}</p>,
          li: ({ children }) => <li>{processDotTokens(children)}</li>,
          strong: ({ children }) => <strong>{processDotTokens(children)}</strong>,
        }}
      >
        {prepared}
      </ReactMarkdown>
    </div>
  );
}

function AssistantPage() {
  const { isCustomer } = useAuth(); // Check if user is a customer
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Dynamic suggestions based on role
  const suggestedQuestions = isCustomer ? [
    'What is my pending balance?',
    'What products are available?',
    'Show me my recent orders',
    'Which invoices are overdue?'
  ] : [
    'What invoices are overdue?',
    'Which products need reordering?',
    'How much did we sell this month?',
    'Show me top customers',
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = async (e, questionOverride) => {
    if (e) e.preventDefault();
    const question = questionOverride || input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    setInput('');
    setLoading(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const response = await aiService.askQuestion(question);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.answer },
      ]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please check backend logs.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleTextareaChange = (e) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <Layout>
      <div className="assistant-page">
        <header className="assistant-header">
          <h1 className="assistant-title">Assistant</h1>
          <p className="assistant-subtitle">
            {isCustomer ? 'Ask Karya about your account and orders.' : 'Ask Karya about your business.'}
          </p>
        </header>

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <h3>Start a conversation</h3>
              <p>
                {isCustomer 
                  ? 'Ask about your orders, invoices, or the product catalog.' 
                  : 'Ask about revenue, inventory, customers, or payments.'}
              </p>
              <div className="suggested-questions">
                {suggestedQuestions.map((q, i) => (
                  <button
                    key={i}
                    className="suggested-question"
                    onClick={() => handleSubmit(null, q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`message-row ${msg.role}`}>
              <div>
                <div className="message-role">
                  {msg.role === 'user' ? 'You' : 'Karya'}
                </div>
                {msg.role === 'assistant' ? (
                  <AssistantMarkdown content={msg.content} />
                ) : (
                  <div className="message-content">{msg.content}</div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row assistant">
              <div>
                <div className="message-role">Karya</div>
                <div className="thinking">
                  <Loader2 size={14} className="spin" /> Thinking...
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <form onSubmit={handleSubmit} className="chat-input-form">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder={isCustomer ? "Ask about your orders..." : "Ask anything about your business..."}
              className="chat-input"
              rows="1"
              disabled={loading}
            />
            <button
              type="submit"
              className="chat-send-btn"
              disabled={!input.trim() || loading}
            >
              <Send size={14} /> Send
            </button>
          </form>
        </div>
      </div>
    </Layout>
  );
}

export default AssistantPage;