import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ENDPOINTS } from '../config';
import './Dashboard.css';

const BusDashboard = () => {
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [trips, setTrips] = useState([]);
  const [deployments, setDeployments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [vehiclesRes, driversRes, tripsRes, deploymentsRes] = await Promise.all([
          axios.get(ENDPOINTS.VEHICLES),
          axios.get(ENDPOINTS.DRIVERS),
          axios.get(ENDPOINTS.TRIPS),
          axios.get(ENDPOINTS.DEPLOYMENTS)
        ]);
        
        const vehicleList = vehiclesRes.data.vehicles || [];
        const driverList = driversRes.data.drivers || [];
        const tripList = tripsRes.data.trips || [];
        const deploymentList = deploymentsRes.data.deployments || [];

        const vehicleAssignments = new Set(deploymentList.map(item => item.vehicle_id));
        const driverAssignments = new Set(deploymentList.map(item => item.driver_id));

        setVehicles(vehicleList.map(vehicle => ({
          ...vehicle,
          status: vehicleAssignments.has(vehicle.id) ? 'assigned' : 'available'
        })));
        
        setDrivers(driverList.map(driver => ({
          ...driver,
          status: driverAssignments.has(driver.id) ? 'assigned' : 'available'
        })));
        
        setTrips(tripList);
        setDeployments(deploymentList);
        setError('');
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Unable to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const availableVehicles = vehicles.filter(v => v.status === 'available').length;
  const availableDrivers = drivers.filter(d => d.status === 'available').length;
  const bookedTrips = trips.filter(t => ((t.booking_status_percentage || 0) > 0)).length;

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading operations dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h1>Operations Dashboard</h1>
          <p>Real-time fleet management and monitoring</p>
        </div>
      </div>

      {error && (
        <div className="error-alert">
          <span>⚠️</span>
          <div>
            <strong>Error Loading Data</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      <div className="metrics-grid">
        <div className="metric-card vehicles-card">
          <div className="metric-header">
            <h3>🚐 Vehicles</h3>
            <span className="metric-badge">{vehicles.length}</span>
          </div>
          <div className="metric-content">
            <div className="metric-stat">
              <div className="stat-value">{availableVehicles}</div>
              <div className="stat-label">Available</div>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${(availableVehicles / vehicles.length) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="metric-card drivers-card">
          <div className="metric-header">
            <h3>👨‍💼 Drivers</h3>
            <span className="metric-badge">{drivers.length}</span>
          </div>
          <div className="metric-content">
            <div className="metric-stat">
              <div className="stat-value">{availableDrivers}</div>
              <div className="stat-label">Available</div>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${(availableDrivers / drivers.length) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="metric-card trips-card">
          <div className="metric-header">
            <h3>🗓️ Trips</h3>
            <span className="metric-badge">{trips.length}</span>
          </div>
          <div className="metric-content">
            <div className="metric-stat">
              <div className="stat-value">{bookedTrips}</div>
              <div className="stat-label">Booked</div>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${(bookedTrips / trips.length) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="metric-card deployments-card">
          <div className="metric-header">
            <h3>🔗 Deployments</h3>
            <span className="metric-badge">{deployments.length}</span>
          </div>
          <div className="metric-content">
            <div className="metric-stat">
              <div className="stat-value">{deployments.length}</div>
              <div className="stat-label">Active</div>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${deployments.length > 0 ? 100 : 0}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div className="details-grid">
        <div className="details-card">
          <div className="card-header">
            <h2>Fleet Status</h2>
            <div className="filter-tabs">
              <button 
                className={`tab ${filter === 'all' ? 'active' : ''}`}
                onClick={() => setFilter('all')}
              >
                All ({vehicles.length})
              </button>
              <button 
                className={`tab ${filter === 'available' ? 'active' : ''}`}
                onClick={() => setFilter('available')}
              >
                Available ({availableVehicles})
              </button>
            </div>
          </div>
          <div className="card-content">
            <div className="items-list">
              {vehicles
                .filter(v => filter === 'all' || v.status === 'available')
                .map(vehicle => (
                  <div key={vehicle.id} className={`item-card ${vehicle.status}`}>
                    <div className="item-header">
                      <div className="item-title">{vehicle.license_plate}</div>
                      <span className={`status-badge ${vehicle.status}`}>
                        {vehicle.status === 'available' ? '○ Available' : '● Assigned'}
                      </span>
                    </div>
                    <div className="item-details">
                      <span className="detail">{vehicle.model}</span>
                      <span className="detail">•</span>
                      <span className="detail">Cap: {vehicle.capacity}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>

        <div className="details-card">
          <div className="card-header">
            <h2>Driver Assignments</h2>
            <div className="filter-tabs">
              <button 
                className={`tab ${filter === 'all' ? 'active' : ''}`}
                onClick={() => setFilter('all')}
              >
                All ({drivers.length})
              </button>
              <button 
                className={`tab ${filter === 'available' ? 'active' : ''}`}
                onClick={() => setFilter('available')}
              >
                Available ({availableDrivers})
              </button>
            </div>
          </div>
          <div className="card-content">
            <div className="items-list">
              {drivers
                .filter(d => filter === 'all' || d.status === 'available')
                .map(driver => (
                  <div key={driver.id} className={`item-card ${driver.status}`}>
                    <div className="item-header">
                      <div className="item-title">{driver.name}</div>
                      <span className={`status-badge ${driver.status}`}>
                        {driver.status === 'available' ? '○ Available' : '● Assigned'}
                      </span>
                    </div>
                    <div className="item-details">
                      <span className="detail">Lic: {driver.license_number}</span>
                      <span className="detail">•</span>
                      <span className="detail">{driver.phone}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>

      <div className="details-grid">
        <div className="details-card full-width">
          <div className="card-header">
            <h2>Scheduled Trips</h2>
            <span className="info-text">{trips.length} trips scheduled for today</span>
          </div>
          <div className="card-content">
            <div className="trips-table">
              {trips.length === 0 ? (
                <div className="empty-state">
                  <p>No trips scheduled</p>
                </div>
              ) : (
                <div className="table-content">
                  {trips.map(trip => {
                    const bookingPercent = (trip.booking_status_percentage || trip.booked_percentage || 0) * 100;
                    return (
                      <div key={trip.id} className="trip-row">
                        <div className="trip-info">
                          <div className="trip-name">{trip.display_name || `Trip ${trip.id}`}</div>
                          <div className="trip-meta">
                            Status: <strong>{trip.live_status || trip.status || 'N/A'}</strong>
                            <span className="separator">•</span>
                            Date: <strong>{trip.date}</strong>
                          </div>
                        </div>
                        <div className="trip-booking">
                          <div className="booking-label">Booking</div>
                          <div className="booking-bar">
                            <div 
                              className="booking-fill"
                              style={{ width: `${bookingPercent}%` }}
                            ></div>
                          </div>
                          <div className="booking-percent">{bookingPercent.toFixed(0)}%</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="details-grid">
        <div className="details-card full-width">
          <div className="card-header">
            <h2>Active Deployments</h2>
            <span className="info-text">{deployments.length} vehicle-driver assignments</span>
          </div>
          <div className="card-content">
            {deployments.length === 0 ? (
              <div className="empty-state">
                <p>No active deployments</p>
              </div>
            ) : (
              <div className="deployments-grid">
                {deployments.map((deployment) => (
                  <div key={deployment.id} className="deployment-card">
                    <div className="deployment-route">
                      <strong>{deployment.route_name}</strong>
                    </div>
                    <div className="deployment-info">
                      <div className="deployment-item">
                        <span className="label">Vehicle</span>
                        <span className="value">{deployment.license_plate}</span>
                      </div>
                      <div className="deployment-item">
                        <span className="label">Driver</span>
                        <span className="value">{deployment.driver_name}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="help-section">
        <div className="help-icon">💡</div>
        <div className="help-content">
          <strong>Need help?</strong> Ask Movi: "Show me available vehicles", "Assign driver to trip", or "What's the status of Metro Corridor?"
        </div>
      </div>
    </div>
  );
};

export default BusDashboard;
