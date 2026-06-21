// test.js
console.log('Hello from Node.js!');
console.log('Current directory:', __dirname);

const express = require('express');
console.log('Express loaded successfully');

const app = express();
const PORT = 5000;

app.get('/', (req, res) => {
    res.send('Server is working!');
});

app.listen(PORT, () => {
    console.log(`✅ Server running on http://localhost:${5000}`);
});

console.log('Server setup complete, waiting for connections...');
