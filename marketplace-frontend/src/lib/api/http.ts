import { env } from '$env/dynamic/public';

export class ApiError extends Error {
	status: number;
	detail: unknown;

	constructor(message: string, status: number, detail: unknown) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
		this.detail = detail;
	}
}

export type ApiRequestInit = {
	method?: 'GET' | 'POST' | 'DELETE' | 'PATCH' | 'PUT';
	query?: Record<string, string | number | boolean | null | undefined>;
	body?: unknown;
	fetchImpl?: typeof fetch;
	headers?: Record<string, string>;
};

const DEFAULT_API_BASE = '/api/v1';

function buildUrl(path: string, query?: ApiRequestInit['query']): string {
	const base = (env.PUBLIC_API_BASE_URL || DEFAULT_API_BASE).replace(/\/$/, '');
	const normalizedPath = path.startsWith('/') ? path : `/${path}`;
	const url = new URL(`${base}${normalizedPath}`, 'http://local');

	if (query) {
		for (const [key, value] of Object.entries(query)) {
			if (value == null) continue;
			url.searchParams.set(key, String(value));
		}
	}

	return base.startsWith('http')
		? url.toString().replace('http://local', '')
		: `${url.pathname}${url.search}`;
}

export async function apiRequest<T>(path: string, init: ApiRequestInit = {}): Promise<T> {
	const fetchImpl = init.fetchImpl ?? fetch;
	const response = await fetchImpl(buildUrl(path, init.query), {
		method: init.method ?? 'GET',
		credentials: 'include',
		headers: {
			'Content-Type': 'application/json',
			...init.headers
		},
		body: init.body == null ? undefined : JSON.stringify(init.body)
	});

	if (response.status === 204) {
		return undefined as T;
	}

	let payload: unknown = null;
	try {
		payload = await response.json();
	} catch {
		payload = null;
	}

	if (!response.ok) {
		const message =
			typeof payload === 'object' && payload && 'detail' in payload
				? String((payload as { detail: unknown }).detail)
				: `Request failed with status ${response.status}`;
		throw new ApiError(message, response.status, payload);
	}

	return payload as T;
}
