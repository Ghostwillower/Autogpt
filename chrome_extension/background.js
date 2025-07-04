// Background script for Ghosthand Chrome extension
// Listens for prompts from the content script, forwards them to ChatGPT
// using the existing session and sends the result to the Ghosthand server.

async function fetchAuthToken() {
  try {
    const resp = await fetch('https://chat.openai.com/api/auth/session', {
      credentials: 'include'
    });
    const data = await resp.json();
    return data.accessToken;
  } catch (err) {
    console.error('Failed to get auth token:', err);
    return null;
  }
}

async function sendPromptToChatGPT(prompt) {
  const token = await fetchAuthToken();
  if (!token) return null;
  try {
    const body = {
      action: 'next',
      messages: [{
        id: crypto.randomUUID(),
        author: { role: 'user' },
        content: { content_type: 'text', parts: [prompt] }
      }],
      model: 'gpt-4'
    };
    const resp = await fetch('https://chat.openai.com/backend-api/conversation', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(body)
    });
    const reader = resp.body.getReader();
    let result = '';
    const decoder = new TextDecoder('utf-8');
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      result += chunk;
    }
    return result;
  } catch (err) {
    console.error('Failed to fetch from ChatGPT:', err);
    return null;
  }
}

function sendToGhosthand(resultText) {
  fetch('http://localhost:5169/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal_plan: resultText })
  }).catch(err => console.error('Failed to send to Ghosthand:', err));
}

chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
  if (request.type === 'gh_prompt') {
    const result = await sendPromptToChatGPT(request.text);
    if (result) {
      sendToGhosthand(result);
    }
    sendResponse({ success: !!result });
  }
});
