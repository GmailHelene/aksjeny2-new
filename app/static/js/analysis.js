const { BuffettAnalysis } = require('../models'); // Example model import

async function getBuffettAnalysis(query) {
    // Replace with your actual DB query logic
    return await BuffettAnalysis.findOne({ where: { symbol: query } });
}

// Fix search functionality on Warren Buffett analysis page
// filepath: /workspaces/aksjeny2/app/routes/analysis.js
router.post('/warren-buffett/search', async (req, res) => {
    try {
        const { query } = req.body;
        const result = await getBuffettAnalysis(query);
        if (!result) {
            return res.status(404).json({ success: false, error: "Ingen resultater funnet." });
        }
        res.json({ success: true, data: result });
    } catch (err) {
        console.error(err);
        res.status(500).json({ success: false, error: "En feil oppstod under analysen. Prøv igjen senere." });
    }
});

// Fix favorites display on profile page
// filepath: /workspaces/aksjeny2/app/routes/profile.js
app.get('/profile', async (req, res) => {
    const userId = req.user.id;
    const favorites = await getUserFavorites(userId);
    res.render('profile', { favorites }); // Ensure favorites are passed to the template
});

// Fix price alert creation error
// filepath: /workspaces/aksjeny2/app/routes/price-alerts.js
app.post('/price-alerts/create', async (req, res) => {
    try {
        const { symbol, price } = req.body;
        await createPriceAlert(req.user.id, symbol, price);
        res.json({ success: true });
    } catch (error) {
        console.error('Price alert creation error:', error);
        res.status(500).json({ success: false, message: 'Kunne ikke opprette prisvarsel. Teknisk feil - kontakt support hvis problemet vedvarer.' });
    }
});

// Fix watchlist update issue
// filepath: /workspaces/aksjeny2/app/routes/watchlist.js
app.post('/watchlist/:id/add', async (req, res) => {
    const watchlistId = req.params.id;
    const { stockSymbol } = req.body;
    await addStockToWatchlist(watchlistId, stockSymbol);
    const updatedWatchlist = await getWatchlist(watchlistId);
    res.json({ success: true, watchlist: updatedWatchlist });
});

// Fix loading alerts issue
// filepath: /workspaces/aksjeny2/app/routes/watchlist.js
app.get('/watchlist', async (req, res) => {
    const alerts = await getUserAlerts(req.user.id);
    res.render('watchlist', { alerts }); // Ensure alerts are passed to the template
});

// Fix portfolio loading error
// filepath: /workspaces/aksjeny2/app/routes/portfolio.js
app.get('/portfolio/:id', async (req, res) => {
    try {
        const portfolio = await getPortfolio(req.params.id);
        res.render('portfolio', { portfolio });
    } catch (error) {
        console.error('Portfolio loading error:', error);
        res.status(500).send('500 Internal Server Error');
    }
});

// Fix add stock to portfolio error
// filepath: /workspaces/aksjeny2/app/routes/portfolio.js
app.post('/portfolio/:id/add', async (req, res) => {
    try {
        const { stockSymbol } = req.body;
        await addStockToPortfolio(req.params.id, stockSymbol);
        res.json({ success: true });
    } catch (error) {
        console.error('Error adding stock to portfolio:', error);
        res.status(500).json({ success: false, message: 'Feil ved lasting av portefølje.' });
    }
});

// Fix conflicting messages on portfolio creation
// filepath: /workspaces/aksjeny2/app/routes/portfolio.js
app.post('/portfolio/create', async (req, res) => {
    try {
        const newPortfolio = await createPortfolio(req.body);
        res.json({ success: true, portfolio: newPortfolio });
    } catch (error) {
        console.error('Portfolio creation error:', error);
        res.status(500).json({ success: false, message: 'Feil ved oppretting av portefølje.' });
    }
});