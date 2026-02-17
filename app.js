const express = require('express');
const app = express();
const port = 3000;

// Import routers
const advancedAnalyticsRouter = require('./app/routes/advanced_analytics');

// Use routers
app.use('/advanced-analytics', advancedAnalyticsRouter);

// Other app configurations...

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});