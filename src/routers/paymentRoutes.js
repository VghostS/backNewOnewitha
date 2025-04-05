const { transactionData, transactionStorage } = require('../database/transactionsStorage');

const time = require('../utils/timeUtils');

const sessionValidation = require('../handlers/sessionValidation');
const payment = require('../handlers/paymentApiHelper');

const storage = new transactionStorage();

const express = require('express');
const router = express.Router();

router.post('/create-invoice', 
    sessionValidation.authenticateClient, async (request, result) =>
{
    await payment.createInvoice(request, result);
});

router.post('/refund',
    sessionValidation.authenticateClient, async (request, result) =>
{
    await payment.refund(request, result);
});

router.post('/order-receipt',
    sessionValidation.authenticateClient,(request, result) => 
{
    const { userId, itemId } = request.body;

    if (!userId)
    {
        return result.status(404).json(
        {
            error: `Param 'userId' is required`
        });
    }

    const loadedTransaction = storage.getByUserIdAndItemId(userId, itemId);

    console.log(`Loaded available transaction by filter: ${JSON.stringify(loadedTransaction)}`);

    if (!loadedTransaction || loadedTransaction.length === 0)
    {
        return result.status(404).json(
        {
            error: `Target transaction not found`
        });
    }

    result.status(200).json(loadedTransaction);

    storage.deleteByItemId(itemId);

    console.log(`Item ${itemId} successful deleted from temporary storage`);
});

router.post('/update-order-receipt',
    sessionValidation.authenticateBot, (request, result) => 
{
    latestReceipt = request.body;

    if (!latestReceipt)
    {
        return result.status(404).json(
        {
            error: `Failed to load order receipt from bot`
        });
    }
        
    console.log(`[${time.getCurrentTimestamp()}] Received payment data:`, latestReceipt);

    const buyerTelegramId = latestReceipt.provider_payment_charge_id.split('_')[0];

    storage.add(new transactionData(
        `${latestReceipt.telegram_payment_charge_id}`,
        `${buyerTelegramId}`,
        `${latestReceipt.invoice_payload}`,
        `${latestReceipt.total_amount}`));

    console.log(`[${time.getCurrentTimestamp()}] ` +
        `Receipt ${latestReceipt.telegram_payment_charge_id} ` +
        `successfully added to temporary storage: for user: ${buyerTelegramId}`);
        
    result.sendStatus(200);
});

router.get('/purchase-history', 
    sessionValidation.authenticateClient, async (request, result) =>
{
    await payment.getPurchaseHistory(request, result);
});

router.get('/refund-history', 
    sessionValidation.authenticateClient, async (request, result) =>
{
    await payment.getRefundHistory(request, result);
});

module.exports = router;