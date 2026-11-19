/**
 * BizAdvisor API Client Service
 * Interacts with FastAPI server backend (http://127.0.0.1:8000)
 * Scoped with JWT Bearer Token stored safely in sessionStorage.
 */

const API_BASE_URL = '/api';

// Token Management via sessionStorage (cleared when browser tab/session closes)
const TOKEN_KEY = 'bizadvisor_auth_token';
const USER_KEY = 'bizadvisor_auth_user';

export function getAuthToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token) {
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(TOKEN_KEY);
  }
}

export function getStoredUser() {
  const userJson = sessionStorage.getItem(USER_KEY);
  if (!userJson) return null;
  try {
    return JSON.parse(userJson);
  } catch {
    return null;
  }
}

export function setStoredUser(user) {
  if (user) {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    sessionStorage.removeItem(USER_KEY);
  }
}

export function clearAuth() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
}

function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export function extractErrorMessage(errorData, fallback = 'An unexpected error occurred.') {
  if (!errorData) return fallback;
  const detail = errorData.detail ?? errorData.message;
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item) return '';
        if (typeof item === 'string') return item;
        if (typeof item === 'object') {
          const field = Array.isArray(item.loc) && item.loc.length > 1 ? item.loc[item.loc.length - 1] : null;
          const msg = item.msg || item.message;
          if (field && msg) {
            const fieldName = String(field).charAt(0).toUpperCase() + String(field).slice(1);
            return `${fieldName}: ${msg}`;
          }
          return msg || JSON.stringify(item);
        }
        return String(item);
      })
      .filter(Boolean);
    return messages.length > 0 ? messages.join('. ') : fallback;
  }
  if (typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  return String(detail) || fallback;
}

// -----------------------------------------------------------------------------
// Authentication Endpoints
// -----------------------------------------------------------------------------
export async function loginUser(usernameOrEmail, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username_or_email: usernameOrEmail,
      password,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(extractErrorMessage(errorData, 'Login failed. Please check your credentials.'));
  }

  const data = await response.json();
  setAuthToken(data.access_token);
  setStoredUser(data.user);
  return data;
}

export async function registerUser(username, email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username,
      email,
      password,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(extractErrorMessage(errorData, 'Registration failed. Please check your input.'));
  }

  const data = await response.json();
  setAuthToken(data.access_token);
  setStoredUser(data.user);
  return data;
}

export async function getCurrentUserProfile() {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuth();
    }
    throw new Error('Failed to retrieve user profile');
  }

  return await response.json();
}

// -----------------------------------------------------------------------------
// Business & Chat Endpoints (Protected)
// -----------------------------------------------------------------------------
export async function sendChatMessage(message, sessionId = null, parametersOverride = null) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      message,
      session_id: sessionId,
      parameters_override: parametersOverride,
    }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuth();
      window.dispatchEvent(new CustomEvent('bizadvisor:auth_expired'));
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(extractErrorMessage(errorData, 'Failed to analyze request with backend AI'));
  }

  return await response.json();
}

export async function runDirectAnalysis(params) {
  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuth();
      window.dispatchEvent(new CustomEvent('bizadvisor:auth_expired'));
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(extractErrorMessage(errorData, 'Failed to execute business analysis'));
  }

  return await response.json();
}

export async function getHistory(searchQuery = '') {
  const url = searchQuery
    ? `${API_BASE_URL}/history?search=${encodeURIComponent(searchQuery)}`
    : `${API_BASE_URL}/history`;
  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuth();
      window.dispatchEvent(new CustomEvent('bizadvisor:auth_expired'));
    }
    throw new Error('Failed to fetch analysis history');
  }

  return await response.json();
}

export async function getHistoryDetail(sessionId) {
  const response = await fetch(`${API_BASE_URL}/history/${sessionId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuth();
      window.dispatchEvent(new CustomEvent('bizadvisor:auth_expired'));
    }
    throw new Error('Failed to fetch session detail');
  }

  return await response.json();
}

export async function deleteHistoryItem(sessionId) {
  const response = await fetch(`${API_BASE_URL}/history/${sessionId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuth();
      window.dispatchEvent(new CustomEvent('bizadvisor:auth_expired'));
    }
    throw new Error('Failed to delete history item');
  }

  return await response.json();
}
