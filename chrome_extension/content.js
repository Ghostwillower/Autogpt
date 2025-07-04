// Content script for Ghosthand Chrome extension
// Sends selected text to the background script when the user
// presses Ctrl+Shift+G.

function getActiveText() {
  const selection = window.getSelection();
  if (selection && selection.toString().trim()) {
    return selection.toString().trim();
  }
  return null;
}

function handleKey(e) {
  if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'g') {
    const text = getActiveText();
    if (text) {
      chrome.runtime.sendMessage({ type: 'gh_prompt', text });
    }
  }
}

document.addEventListener('keydown', handleKey);
