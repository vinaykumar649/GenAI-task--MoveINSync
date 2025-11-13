const API_HOST = process.env.REACT_APP_API_HOST || 'http://localhost';
const API_PORT = process.env.REACT_APP_API_PORT || '5000';
const API_BASE_URL = `${API_HOST}:${API_PORT}`;

const ENDPOINTS = {
  CHAT: `${API_BASE_URL}/chat`,
  SPEECH_TO_TEXT: `${API_BASE_URL}/speech-to-text`,
  TEXT_TO_SPEECH: `${API_BASE_URL}/text-to-speech`,
  HEALTH: `${API_BASE_URL}/health`,
  VEHICLES: `${API_BASE_URL}/api/vehicles`,
  DRIVERS: `${API_BASE_URL}/api/drivers`,
  TRIPS: `${API_BASE_URL}/api/trips`,
  STOPS: `${API_BASE_URL}/api/stops`,
  PATHS: `${API_BASE_URL}/api/paths`,
  ROUTES: `${API_BASE_URL}/api/routes`,
  DEPLOYMENTS: `${API_BASE_URL}/api/deployments`
};

const TIMEOUT = parseInt(process.env.REACT_APP_REQUEST_TIMEOUT || '30000', 10);

export { ENDPOINTS, API_BASE_URL, TIMEOUT };
