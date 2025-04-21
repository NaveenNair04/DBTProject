import React, { useEffect, useState } from "react";
import "./index.css";

const API_BASE_URL = "http://localhost:8000";

function App() {
  const [symbols, setSymbols] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [minMaxData, setMinMaxData] = useState(null);
  const [rollingMetricsData, setRollingMetricsData] = useState(null);

  // Fetch available symbols
  const fetchSymbols = () => {
    fetch(`${API_BASE_URL}/api/v1/spark-analytics/symbols`)
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched symbols:", data.symbols);
        setSymbols(data.symbols);
      })
      .catch((err) => {
        console.error("Error fetching symbols:", err);
      });
  };

  // Fetch Min/Max Analytics
  const fetchMinMaxData = (symbol) => {
    fetch(`${API_BASE_URL}/api/v1/spark-analytics/min-max/${symbol}`)
      .then((res) => res.json())
      .then((data) => {
        console.log("Min/Max Data:", data);
        setMinMaxData(data);
      })
      .catch((err) => console.error("Error fetching min/max data:", err));
  };

  // Fetch Rolling Metrics
  const fetchRollingMetricsData = (symbol, windowDuration = "5 minutes") => {
    fetch(
      `${API_BASE_URL}/api/v1/spark-analytics/rolling-metrics/${symbol}?window_duration=${windowDuration}`,
    )
      .then((res) => res.json())
      .then((data) => {
        console.log("Rolling Metrics Data:", data);
        setRollingMetricsData(data);
      })
      .catch((err) => console.error("Error fetching rolling metrics:", err));
  };

  useEffect(() => {
    fetchSymbols();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      fetchMinMaxData(selectedSymbol);
      fetchRollingMetricsData(selectedSymbol);
    }
  }, [selectedSymbol]);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800">
          📊 Market Analytics Dashboard
        </h1>
        <p className="text-gray-600 mt-2">
          Track and visualize financial metrics in real time.
        </p>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow">
          <h2 className="text-xl font-semibold mb-2">Symbol Selector</h2>
          <select
            className="w-full p-2 rounded border"
            onChange={(e) => setSelectedSymbol(e.target.value)}
            value={selectedSymbol}
          >
            <option value="">Choose a symbol</option>
            {symbols.map((symbol) => (
              <option key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
        </div>

        {minMaxData && (
          <div className="bg-white p-6 rounded-2xl shadow">
            <h2 className="text-xl font-semibold mb-2">Min/Max Analytics</h2>
            <p>Symbol: {minMaxData.symbol}</p>
            <p>Min Price: {minMaxData.min_price}</p>
            <p>Max Price: {minMaxData.max_price}</p>
            <p>Avg Price: {minMaxData.avg_price}</p>
            <p>Count: {minMaxData.count}</p>
          </div>
        )}

        {rollingMetricsData && (
          <div className="bg-white p-6 rounded-2xl shadow">
            <h2 className="text-xl font-semibold mb-2">Rolling Metrics</h2>
            <p>Symbol: {rollingMetricsData.symbol}</p>
            <p>Min Price: {rollingMetricsData.min_price}</p>
            <p>Max Price: {rollingMetricsData.max_price}</p>
            <p>Avg Price: {rollingMetricsData.avg_price}</p>
            <p>Avg Volume: {rollingMetricsData.avg_volume}</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
