const { useState, useEffect } = React;

function App() {
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
    } catch (err) {
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
    } catch (err) {
      setStatus('failed');
    }
  };

  const enroll = async () => {
    setStatus('enrolling...');
    try {
      const res = await fetch('/enroll', { method: 'POST' });
      const data = await res.json();
      setStatus(data.status || 'started');
    } catch {
      setStatus('failed');
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`/history?user=${encodeURIComponent(user)}`);
      const data = await res.json();
      setHistory(data.history || []);
    } catch {
      setHistory([]);
    }
  };

  return (
    React.createElement(
      'div',
      { style: { fontFamily: 'Arial, sans-serif', padding: 20, maxWidth: 600 } },
      React.createElement('h1', null, 'Ghosthand'),
      React.createElement('textarea', {
        rows: 4,
        cols: 60,
        value: goal,
        placeholder: 'Enter goal',
        onChange: e => setGoal(e.target.value)
      }),
      React.createElement('div', { style: { marginTop: 8 } },
        'Plan: ',
        React.createElement('textarea', {
          rows: 2,
          cols: 60,
          value: plan,
          placeholder: 'Optional direct plan',
          onChange: e => setPlan(e.target.value)
        })
      ),
      React.createElement(
        'div',
        { style: { marginTop: 8 } },
        'User: ',
        React.createElement(
          'select',
          { value: user, onChange: e => setUser(e.target.value) },
          users.map(u =>
            React.createElement('option', { key: u, value: u }, u)
          )
        )
      ),
      React.createElement(
        'label',
        { style: { display: 'block', marginTop: 8 } },
        React.createElement('input', {
          type: 'checkbox',
          checked: dryRun,
          onChange: e => setDryRun(e.target.checked)
        }),
        ' Dry run'
      ),
      React.createElement(
        'div',
        { style: { marginTop: 10 } },
        React.createElement('button', { onClick: sendGoal }, 'Run Goal'),
        ' ',
        React.createElement('button', { onClick: sendPlan }, 'Run Plan'),
        ' ',
        React.createElement('button', { onClick: enroll }, 'Enroll New User')
      ),
      React.createElement('p', null, status),
      React.createElement(
        'div',
        { style: { marginTop: 20 } },
        React.createElement('button', { onClick: fetchHistory }, 'Refresh History'),
        React.createElement(
          'ul',
          null,
          history.map((h, idx) =>
            React.createElement(
              'li',
              { key: idx },
              `${h.timestamp}: ${h.goal} -> ${h.result}`
            )
          )
        )
      )
    )
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(App));
