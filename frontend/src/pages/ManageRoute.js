import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ENDPOINTS } from '../config';

const ManageRoute = () => {
  const [stops, setStops] = useState([]);
  const [paths, setPaths] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedActionRoute, setExpandedActionRoute] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [stopsRes, pathsRes, routesRes] = await Promise.all([
          axios.get(ENDPOINTS.STOPS),
          axios.get(ENDPOINTS.PATHS),
          axios.get(ENDPOINTS.ROUTES)
        ]);
        const stopsData = stopsRes.data.stops || [];
        const pathsData = (pathsRes.data.paths || []).map(path => ({
          ...path,
          stops: (path.stops || []).slice().sort((a, b) => (a.order || 0) - (b.order || 0))
        }));
        const routesData = routesRes.data.routes || [];

        setStops(stopsData);
        setPaths(pathsData);
        setRoutes(routesData);
        setError('');
      } catch (err) {
        console.error('Error fetching route data:', err);
        setError('Unable to load route data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleActionClick = (routeId) => {
    setExpandedActionRoute(expandedActionRoute === routeId ? null : routeId);
  };

  const performAction = async (action, routeId, routeName) => {
    let message = '';
    switch(action) {
      case 'view':
        message = `Show me details of route '${routeName}'`;
        break;
      case 'trips':
        message = `Create trips for route '${routeName}'`;
        break;
      case 'deploy':
        message = `Deploy vehicle to route '${routeName}'`;
        break;
      case 'stops':
        message = `Show me all stops in route '${routeName}'`;
        break;
      default:
        return;
    }
    window.dispatchEvent(new CustomEvent('moviMessage', { detail: { message } }));
    setExpandedActionRoute(null);
  };

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading route management data...</div>;
  }

  return (
    <div style={{ padding: '20px', marginRight: '370px' }}>
      <h1 style={{ color: '#28a745', borderBottom: '2px solid #28a745', paddingBottom: '10px', marginBottom: '20px' }}>🗺️ Manage Routes</h1>
      {error && (
        <div style={{ marginBottom: '15px', padding: '10px', background: '#fef3c7', border: '1px solid #fcd34d', color: '#b45309', borderRadius: '5px', fontSize: '12px' }}>
          {error}
        </div>
      )}

      <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #dee2e6', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Route ID</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Route Name</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Direction</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Shift Time</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Start Point</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>End Point</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', width: '80px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {routes.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ padding: '20px', textAlign: 'center', color: '#6c757d' }}>
                  No routes found. Create a path and route to get started.
                </td>
              </tr>
            ) : (
              routes.map((route, idx) => (
                <React.Fragment key={route.id}>
                  <tr style={{ borderBottom: '1px solid #dee2e6', background: idx % 2 === 0 ? 'white' : '#f8f9fa' }}>
                    <td style={{ padding: '10px' }}>{route.id}</td>
                    <td style={{ padding: '10px', fontWeight: '500' }}>{route.route_display_name || route.path_name || 'Unnamed'}</td>
                    <td style={{ padding: '10px' }}>{route.direction || '-'}</td>
                    <td style={{ padding: '10px' }}>{route.shift_time || '-'}</td>
                    <td style={{ padding: '10px', fontSize: '12px', color: '#666' }}>{route.start_point || '-'}</td>
                    <td style={{ padding: '10px', fontSize: '12px', color: '#666' }}>{route.end_point || '-'}</td>
                    <td style={{ padding: '10px', textAlign: 'center' }}>
                      <button 
                        onClick={() => handleActionClick(route.id)}
                        style={{ 
                          background: expandedActionRoute === route.id ? '#007bff' : 'none', 
                          color: expandedActionRoute === route.id ? 'white' : '#007bff',
                          border: '1px solid #007bff', 
                          cursor: 'pointer', 
                          fontSize: '14px',
                          padding: '4px 8px',
                          borderRadius: '4px'
                        }}
                      >
                        {expandedActionRoute === route.id ? '✕' : '⋯'}
                      </button>
                    </td>
                  </tr>
                  {expandedActionRoute === route.id && (
                    <tr style={{ background: '#f0f7ff', borderBottom: '1px solid #dee2e6' }}>
                      <td colSpan="7">
                        <div style={{ padding: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          <button
                            onClick={() => performAction('view', route.id, route.route_display_name || 'Route')}
                            style={{
                              padding: '6px 12px',
                              background: '#007bff',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            👁️ View Details
                          </button>
                          <button
                            onClick={() => performAction('stops', route.id, route.route_display_name || 'Route')}
                            style={{
                              padding: '6px 12px',
                              background: '#17a2b8',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            📍 View Stops
                          </button>
                          <button
                            onClick={() => performAction('trips', route.id, route.route_display_name || 'Route')}
                            style={{
                              padding: '6px 12px',
                              background: '#28a745',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            + Create Trip
                          </button>
                          <button
                            onClick={() => performAction('deploy', route.id, route.route_display_name || 'Route')}
                            style={{
                              padding: '6px 12px',
                              background: '#ffc107',
                              color: 'black',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            🚌 Deploy Vehicle
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '8px', border: '1px solid #dee2e6' }}>
          <h3 style={{ color: '#dc3545', marginBottom: '10px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📍 Stops {stops.length > 0 && <span style={{ fontSize: '12px', background: '#dc3545', color: 'white', padding: '2px 6px', borderRadius: '12px' }}>{stops.length}</span>}
          </h3>
          <div style={{ maxHeight: '200px', overflowY: 'auto', fontSize: '12px' }}>
            {stops.length === 0 ? (
              <div style={{ color: '#6c757d', fontStyle: 'italic' }}>No stops created yet.</div>
            ) : (
              stops.map(stop => (
                <div key={stop.id} style={{ padding: '8px', margin: '5px 0', background: 'white', borderRadius: '4px', border: '1px solid #dee2e6' }}>
                  <strong>{stop.name}</strong> <span style={{ color: '#6c757d', fontSize: '11px' }}>({stop.latitude?.toFixed(4)}, {stop.longitude?.toFixed(4)})</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '8px', border: '1px solid #dee2e6' }}>
          <h3 style={{ color: '#007bff', marginBottom: '10px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            🛫 Paths {paths.length > 0 && <span style={{ fontSize: '12px', background: '#007bff', color: 'white', padding: '2px 6px', borderRadius: '12px' }}>{paths.length}</span>}
          </h3>
          <div style={{ maxHeight: '200px', overflowY: 'auto', fontSize: '12px' }}>
            {paths.length === 0 ? (
              <div style={{ color: '#6c757d', fontStyle: 'italic' }}>No paths created yet.</div>
            ) : (
              paths.map(path => (
                <div key={path.id} style={{ padding: '8px', margin: '5px 0', background: 'white', borderRadius: '4px', border: '1px solid #dee2e6' }}>
                  <strong>{path.name}</strong><br />
                  <span style={{ color: '#6c757d', fontSize: '11px' }}>{(path.stops || []).length > 0 ? (path.stops || []).map(s => s.name).join(' → ') : 'No stops'}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div style={{ marginTop: '20px', padding: '10px', background: '#e9ecef', borderRadius: '5px' }}>
        <small style={{ color: '#6c757d' }}>
          💡 <strong>Try asking Movi:</strong> "Show all paths", "Show routes for South Bangalore", "How many vehicles available?", "Assign a driver to a trip"
        </small>
      </div>
    </div>
  );
};

export default ManageRoute;
