import React, { useState } from 'react';

function ChatMessage({ message }) {
  const [showSql, setShowSql] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const isUser = message.role === 'user';

  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-content">
        {message.content.split('\n').map((line, i) => (
          <React.Fragment key={i}>
            {line}
            {i < message.content.split('\n').length - 1 && <br />}
          </React.Fragment>
        ))}
      </div>

      {!isUser && message.sql_query && (
        <div
          className="message-sql"
          onClick={() => setShowSql(!showSql)}
          title="Click to toggle SQL query"
        >
          {showSql ? message.sql_query : '🔍 Show SQL query'}
        </div>
      )}

      {!isUser && message.results && message.results.length > 0 && (
        <>
          <div
            className="message-results-badge"
            onClick={() => setShowResults(!showResults)}
          >
            📊 {message.results.length} result{message.results.length !== 1 ? 's' : ''}
            {showResults ? ' ▲' : ' ▼'}
          </div>

          {showResults && (
            <div className="results-table-container">
              <table className="results-table">
                <thead>
                  <tr>
                    {Object.keys(message.results[0]).map(key => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {message.results.slice(0, 20).map((row, i) => (
                    <tr key={i}>
                      {Object.values(row).map((val, j) => (
                        <td key={j} title={String(val)}>{val !== null ? String(val) : '—'}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {!isUser && message.query_type && (
        <div className="message-meta">
          {message.query_type !== 'rejected' ? `Type: ${message.query_type}` : ''}
        </div>
      )}
    </div>
  );
}

export default ChatMessage;