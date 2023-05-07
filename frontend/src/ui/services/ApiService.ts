import { getCookie } from 'utils/session';
import { formatFilters, getErrorMessage, reportError } from './apiServiceUtils';

const stripTrailingSlash = (str:string) =>
  str.endsWith('/') ? str.slice(0, -1) : str;

const basePath = stripTrailingSlash(import.meta.env.BASE_URL);

let serverPath = '';
if (import.meta.env.DEV) {
  serverPath = '/api';
} else if (import.meta.env.PROD) {
  serverPath = `${basePath}/api/v1`;
}

const get = async (
  endpoint: string,
  filters: string | Record<string, unknown> = {},
  paginated?: boolean
) => {
  try {
    const response = await fetch(
      `${serverPath}${endpoint}?${formatFilters(filters)}${
        paginated ? '&page_size=10000' : ''
      }`,
      {
        method: 'GET',
        credentials: 'include',
      }
    );
    if (response.status === 204) {
      return undefined;
    }

    // Authentication credentials were not provided.
    if (response.status === 401) {
      const data = await response.json();
      throw new Error(data.detail);
    }

    if (response.headers.get('content-type') === 'application/json') {
      const data = await response.json();
      return data;
    }
    if (response.headers.get('content-type') === 'text/csv; charset=utf-8') {
      const data = await response.text();
      return data;
    }
  } catch (error) {
    reportError({ message: getErrorMessage(error) });
  }
};

  const post = async <T>(endpoint: string, body: T) => {
    try {
      const response = await fetch(`${serverPath}${endpoint}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken') ?? '',
        },
        body: JSON.stringify(body),
      });
  
      const data = await response.json();
      return data;
    } catch (error) {
      reportError({ message: getErrorMessage(error) });
    }
  };

export const api = {
    get,
    post,
}