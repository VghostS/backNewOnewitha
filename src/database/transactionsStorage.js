class transactionData
{
    constructor(id, buyerId, itemId, itemPrice)
    {
        this.id = id;
        this.buyerId = buyerId;
        this.itemId = itemId;
        this.price = itemPrice;
    }
}

class transactionStorage
{
    constructor()
    {
        this.items = [];
    }

    add(item)
    {
        this.items.push(item);
    }

    deleteByItemId(itemId) 
    {
        const itemIndex = this.items.findIndex(
            item => item.itemId === itemId);
    
        if (itemIndex !== -1) 
        {
            this.items.splice(itemIndex, 1);
        }
    }

    getByUserIdAndItemId(buyerId, itemId) 
    {
        return this.items.find(item => item.buyerId === buyerId 
            && item.itemId === itemId);
    }
}

module.exports = 
{
    transactionStorage,
    transactionData
}