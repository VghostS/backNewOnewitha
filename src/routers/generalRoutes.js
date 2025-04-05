const time = require('../utils/timeUtils');

const express = require('express');

const router = express.Router();

router.get('/time', async (request, result) =>
{
    result.status(200).json({ tick: time.getUnixTime() });
});

module.exports = router;