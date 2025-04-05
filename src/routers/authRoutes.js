const sessionValidation = require('../handlers/sessionValidation');

const bodyParser = require('body-parser');

const express = require('express');
const router = express.Router();

router.post('/authenticate', 
    bodyParser.text(), (request, result) => 
{
    sessionValidation.startClientCheckIn(request, result);
});

module.exports = router;