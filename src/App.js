import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchData = useCallback(async (pageNumber) => {
    try {
      const response = await axios.get('http://127.0.0.1:5000/api/data', {
        params: { page: pageNumber, limit: 10 }  // Fetch data with pagination
      });
      console.log("Response data:", response.data); // Log response data
      if (response.data.length > 0) {
        setData(prevData => [...prevData, ...response.data]);
        setHasMore(response.data.length === 10);  // Check if there might be more data
      } else {
        setHasMore(false);  // No more data to fetch
      }
      setLoading(false); // Data loaded successfully
    } catch (error) {
      console.error("Error fetching data:", error);
      setError(error);
      setLoading(false); // Data failed to load
    }
  }, []);

  useEffect(() => {
    fetchData(page);  // Fetch initial page
  }, [fetchData, page]);

  const handleScroll = (event) => {
    const { scrollTop, clientHeight, scrollHeight } = event.currentTarget;
    if (scrollTop + clientHeight >= scrollHeight && !loading && hasMore) {
      setPage(prevPage => prevPage + 1); // Load next page
    }
  };

  if (loading && page === 1) return <p>Loading...</p>;
  if (error) {
    return (
      <div className="App">
        <h1>Article List</h1>
        <p>Error loading data.</p>
        <table>
          <thead>
            <tr>
              <th>Number</th>
              <th>Update Log</th>
              <th>Summary</th>
              <th>Link</th>
              <th>Keywords</th>
            </tr>
          </thead>
          <tbody>
            {/* Display no data available row */}
            <tr>
              <td colSpan="5">No data available.</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="App" onScroll={handleScroll} style={{ height: '80vh', overflowY: 'scroll' }}>
      <h1>Article List</h1>
      <table>
        <thead>
          <tr>
            <th>Number</th>
            <th>Update Log</th>
            <th>Summary</th>
            <th>Link</th>
            <th>Keywords</th>
          </tr>
        </thead>
        <tbody>
          {data.length > 0 ? (
            data.map((item, index) => (
              <tr key={index}>
                <td>{item.number}</td>
                <td>{item.update_log}</td>
                <td>{item.summary}</td>
                <td><a href={item.link} target="_blank" rel="noopener noreferrer">Read more</a></td>
                <td>
                  {Array.isArray(item.keywords)
                    ? item.keywords.join(', ')  // 如果是数组，则使用 join 将其转换为字符串
                    : 'Invalid Keywords'}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="5">No data available.</td>
            </tr>
          )}
        </tbody>
      </table>
      {loading && <p>Loading more...</p>}
    </div>
  );
}

export default App;
