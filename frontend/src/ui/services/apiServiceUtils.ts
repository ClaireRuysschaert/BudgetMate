export const getErrorMessage = (error: unknown) => {
  if (error instanceof Error) return error.message;
  return String(error);
};

// In case we have a logger service
export const reportError = ({ message }: { message: string }) => {
  throw new Error(`[ApiService.logger]: ${message}`);
};

export const formatFilters = (filters: Record<string, unknown> | string) => {
  if (typeof filters === 'string') {
    return `${filters}`;
  }
  if (typeof filters === 'object') {
    const array: string[] = [];
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== '' && value !== undefined && value !== null) {
        array.push(`${key}=${value}`);
      }
    });
    return array.join('&');
  }
  return '';
};
