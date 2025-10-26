const express = require('express');
const axios = require('axios');
const app = express();

app.use(express.json());

// Enable CORS for all requests
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

// Proxy endpoint for Nominatim
app.get('/nominatim', async (req, res) => {
    try {
        const query = req.query.q;
        const response = await axios.get(`https://nominatim.openstreetmap.org/search?format=json&q=${query}`, {
            headers: {
                'User-Agent': 'CourseProject/1.0 (your_email@example.com)' // Replace with your email
            }
        });
        res.json(response.data);
    } catch (error) {
        console.error('Proxy error:', error.message);
        res.status(500).json({ error: 'Failed to fetch from Nominatim' });
    }
});

app.listen(3000, () => {
    console.log('Proxy server running on http://localhost:3000');
});