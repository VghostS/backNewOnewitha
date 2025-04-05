const time = require('../utils/timeUtils');

const axios = require('axios');

require('dotenv').config();

const createInvoiceLink = `https://api.telegram.org/bot${process.env.BOT_TOKEN}/createInvoiceLink`;
const refundPaymentLink = `https://api.telegram.org/bot${process.env.BOT_TOKEN}/refundStarPayment`;
const getTransactionsLink = `https://api.telegram.org/bot${process.env.BOT_TOKEN}/getStarTransactions`;

async function createInvoice(request, result)
{
    var productData = createProductData(request);

    try
    {
        const response = await axios.post(createInvoiceLink, productData);

        if (response.data && response.data.result)
        {
            return result.status(200).json(
            {
                invoiceLink: response.data.result
            });
        }

        result.status(500).json(
        {
            error: 'Failed to create invoice link.'
        });
    }
    catch (error)
    {
        console.error(`[${time.getCurrentTimestamp()}] Error creating invoice:`, error);

        if (error.response && error.response.data && error.response.data.description)
        {
            result.status(error.res.status).json(
            {
                error: error.response.data.description
            });

            return;
        }

        result.status(500).json(
        {
            error: 'Internal server error'
        });
    }
}

async function refund(request, result)
{
    var refundData = createRefundData(request);

    try 
    {
        const response = await axios.post(refundPaymentLink, refundData);

        if (response.data && response.data.ok)
        {
            return result.status(200).json(
            {
                message: 'The refund to the buyer was successfully made'
            })
        }

        result.status(500).json(
        {
            error: 'Failed to process refund'
        });
    }
    catch (error)
    {
        console.error(`[${time.getCurrentTimestamp()}] Error processing refund:`, error);

        if (error.response && error.response.data && error.response.data.description) 
        {
            result.status(error.response.status).json(
            {
                error: error.response.data.description
            });

            return;
        }

        result.status(500).json(
        {
            error: 'Internal server error'
        });
    }
}

async function getRefundHistory(request, result)
{
    const transactions = await getTransactionsHistory(request);

    if (!transactions)
    {
        return result.status(401).json(
        {
            error: `Failed to load refund transactions history`
        });
    }

    const refundTransactions = transactions.filter(
        transaction => transaction.receiver);

    return result.status(200).json(
    {
        transactions: refundTransactions
    });
}

async function getPurchaseHistory(request, result)
{
    const transactions = await getTransactionsHistory(request);

    if (!transactions)
    {
        return result.status(401).json(
        {
            error: `Failed to load purchase transactions history`
        });
    }

    const purchaseTransactions = transactions.filter(
        transaction => transaction.source);

    return result.status(200).json(
    {
        transactions: purchaseTransactions
    });
}

async function getTransactionsHistory(request)
{
    const { amount, totalPass = 0 } = request.body;

    if (!amount || amount === 0)
    {
        return { error: `Param 'amount' is required` };
    }

    try
    {
        const response = await axios.get(getTransactionsLink,
        {
            params: 
            {
                offset: totalPass,
                limit: amount
            }
        });

        const successLoad = createSuccessfulTransactionsData(response.data);

        if (!successLoad.isSuccess || !successLoad.data)
        {
            return { error: successLoad.error };
        }

        console.log(`Parsed transactions:` + 
            `${JSON.stringify(successLoad.data)}`);

        return successLoad.data;
    }
    catch (error)
    {
        console.error(`[${time.getCurrentTimestamp()}] ` +
            `Failed to load transactions history`);

        if (error.response && error.response.data && error.response.data.description) 
        {
            return { error: error.response.data.description };
        }

        return { error: 'Internal server error' };
    }
}

function createSuccessfulTransactionsData(request)
{
    const { ok, result } = request;

    if (!ok || !result)
    {
        var messageError = `Failed to parse transactions data`;

        console.error(`[${time.timestamp}] ${messageError}`);

        return {
            isSuccess: false,
            data: null,
            error: messageError
        };
    }

    const transactions = result.transactions;
    
    if (!transactions || transactions.length === 0)
    {
        var messageError = `Not transactions found at response`;

        console.error(`[${time.getCurrentTimestamp()}] ${messageError}`);

        return {
            isSuccess: false,
            data: null,
            error: messageError
        };
    }

    return {
        isSuccess: true,
        data: transactions
    };
}

function createProductData(request)
{
    const { title, description, payload, providerToken, currency, amount } = request.body;

    const data =
    {
        title,
        description,
        payload,
        provider_token: providerToken,
        currency,
        prices:
        [
            { 
                label:title,
                amount 
            }
        ]
    };

    return data;
}

function createRefundData(request)
{
    const { userId, transactionId } = request.body;

    const data = 
    {
        user_id: userId,
        telegram_payment_charge_id: transactionId
    };

    return data;
}

module.exports = 
{
    createInvoice,
    refund,

    getPurchaseHistory,
    getRefundHistory
};