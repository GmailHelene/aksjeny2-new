import React, { useState, useEffect } from 'react';
import ChartComponent from './ChartComponent';
import NokkeltallComponent from './NokkeltallComponent';
import RSIComponent from './RSIComponent';
import MACDComponent from './MACDComponent';

const StockDetailsPage = ({ ticker }) => {
  const [activeTab, setActiveTab] = useState('oversikt');
  const [chartData, setChartData] = useState(null);
  const [nokkeltallData, setNokkeltallData] = useState(null);
  const [rsiData, setRsiData] = useState(null);
  const [macdData, setMacdData] = useState(null);

  useEffect(() => {
    // Fetch data logic here
  }, [ticker]);

  return (
    <div>
      {/* Tab navigation logic here */}
      {activeTab === 'oversikt' && (
        <>
          {/* Fix chart loading: ensure data is fetched before rendering charts */}
          {chartData ? (
            <ChartComponent data={chartData} />
          ) : (
            <div>Loading chart...</div>
          )}
          {/* Only show Nøkkeltall on the "Oversikt" tab */}
          <NokkeltallComponent data={nokkeltallData} />
        </>
      )}
      {activeTab === 'teknisk' && (
        <>
          {/* Remove empty RSI and MACD sections */}
          {rsiData && <RSIComponent data={rsiData} />}
          {macdData && <MACDComponent data={macdData} />}
          {/* Remove whitespace: only render if data exists */}
        </>
      )}
    </div>
  );
};

export default StockDetailsPage;