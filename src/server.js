const time = require('./utils/timeUtils');

const authRoutes = require('./routers/authRoutes');
const paymentRoutes = require('./routers/paymentRoutes');
const generalRoutes = require('./routers/generalRoutes');

const express = require('express');
const bodyParser = require('body-parser');

require('dotenv').config();

const app = express();
const port = process.env.PORT || 1000;

app.use(bodyParser.json());

app.use('/api', generalRoutes);
app.use('/api', authRoutes);
app.use('/api/payment', paymentRoutes);

app.listen(port, () => 
{
    console.log(`[${time.getCurrentTimestamp()}] ` +
    `Unigram Payment API running at ${process.env.SERVER_DOMAIN}, with port: ${port}`);
});