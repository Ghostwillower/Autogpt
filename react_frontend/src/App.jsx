import React, { useState, useEffect } from 'react';

export default function App() {
  const [goal, setGoal] = useState('');
  const [plan, setPlan] = useState('');
  const [user, setUser] = useState('default');
  const [users, setUsers] = useState([]);
  const [dryRun, setDryRun] = useState(false);
  const [status, setStatus] = useState('');
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetch('/users')
      .then(res => res.json())
      .then(data => setUsers(data.users || ['default']))
      .catch(() => setUsers(['default']));
  }, []);

  useEffect(() => {
    if (users.length) {
      fetchHistory();
    }
  }, [user, users]);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`/history?user=${encodeURIComponent(user)}`);
      const data = await res.json();
      setHistory(data.history || []);
    } catch (e) {
      setHistory([]);
    }
  };

  const sendGoal = async () => {
    setStatus('sending...');
    try {
      const res = await fetch('/goal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, user, dry_run: dryRun })
      });
      const data = await res.json();
      setStatus(data.status || 'started');
      fetchHistory();
    } catch (e) {
      setStatus('failed');
    }
  };

  const sendPlan = async () => {
    setStatus('sending plan...');
    try {
      const res = await fetch('/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal_plan: plan, user, dry_run: dryRun })
      });
      const data = await res.json();
      setStatus(data.status || 'started');
      fetchHistory();
    } catch (e) {
      setStatus('failed');
    }
  };

  const enroll = async () => {
    setStatus('enrolling...');
    try {
      const res = await fetch('/enroll', { method: 'POST' });
      const data = await res.json();
      setStatus(data.status || 'started');
    } catch (e) {
      setStatus('failed');
    }
  };

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', padding: 20, maxWidth: 600 }}>
      <h1>Ghosthand</h1>
      <textarea
        rows={4}
        cols={60}
        value={goal}
        placeholder="Enter goal"
        onChange={e => setGoal(e.target.value)}
      />
      <div style={{ marginTop: 8 }}>
        Plan:
        <textarea
          rows={2}
          cols={60}
          value={plan}
          placeholder="Optional direct plan"
          onChange={e => setPlan(e.target.value)}
        />
      </div>
      <div style={{ marginTop: 8 }}>
        User:
        <select value={user} onChange={e => setUser(e.target.value)}>
          {users.map(u => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>
      </div>
      <label style={{ display: 'block', marginTop: 8 }}>
        <input
          type="checkbox"
          checked={dryRun}
          onChange={e => setDryRun(e.target.checked)}
        />{' '}Dry run
      </label>
      <div style={{ marginTop: 10 }}>
        <button onClick={sendGoal}>Run Goal</button>{' '}
        <button onClick={sendPlan}>Run Plan</button>{' '}
        <button onClick={enroll}>Enroll New User</button>
      </div>
      <p>{status}</p>
      <div style={{ marginTop: 20 }}>
        <button onClick={fetchHistory}>Refresh History</button>
        <ul>
          {history.map((h, idx) => (
            <li key={idx}>
              {h.timestamp}: {h.goal} -&gt; {h.result}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
