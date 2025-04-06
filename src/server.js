const time = require('./utils/timeUtils');
const authRoutes = require('./routers/authRoutes');
const paymentRoutes = require('./routers/paymentRoutes');
const generalRoutes = require('./routers/generalRoutes');
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors'); // Add this line

require('dotenv').config();

const app = express();
const port = process.env.PORT || 1000;

// Configure CORS
app.use(cors({
  origin: ['https://vghosts.github.io', 'http://localhost:3000'], // Add your frontend URLs
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(bodyParser.json());

app.use('/api', generalRoutes);
app.use('/api', authRoutes);
app.use('/api/payment', paymentRoutes);

app.listen(port, () => 
{
    console.log(`[${time.getCurrentTimestamp()}] ` +
    `Unigram Payment API running at ${process.env.SERVER_DOMAIN}, with port: ${port}`);
});