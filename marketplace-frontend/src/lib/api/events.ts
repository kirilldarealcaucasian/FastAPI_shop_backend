import { env } from '$env/dynamic/public';

export type BookEventName =
	| 'view'
	| 'long_view'
	| 'cart'
	| 'purchase';

type SendBookEventParams = {
	bookId: number;
	event: BookEventName;
};

const DEFAULT_COLLECT_ENDPOINT = 'http://localhost:8010/api/v1/events/collect';
const EVENTS_SESSION_EXPIRATION_COOKIE = 'events_session_expiration_time';
const EVENTS_SESSION_EXPIRATION_HEADER = 'X-Events-Session-Expiration-Time';

function resolveCollectorEndpoint(): string {
	const configured = env.PUBLIC_EVENTS_COLLECTOR_URL?.trim();
	if (!configured) return DEFAULT_COLLECT_ENDPOINT;

	const normalized = configured.replace(/\/$/, '');
	if (normalized.endsWith('/collect')) return normalized;
	return `${normalized}/events/collect`;
}

function readCookie(name: string): string | null {
	if (typeof document === 'undefined') return null;

	const cookie = document.cookie
		.split('; ')
		.find((part) => part.startsWith(`${name}=`));
	if (!cookie) return null;

	const value = cookie.slice(name.length + 1).replace(/^"|"$/g, '');
	return decodeURIComponent(value);
}

export async function sendBookEvent({
	bookId,
	event
}: SendBookEventParams): Promise<void> {
	const sessionExpirationTime = readCookie(EVENTS_SESSION_EXPIRATION_COOKIE);
	if (!sessionExpirationTime) {
		console.warn('Failed to send book event: missing events session expiration', {
			event,
			bookId
		});
		return;
	}

	const payload = {
		book_id: bookId,
		action: event,
		ts: Math.floor(Date.now() / 1000),
	};

	try {
		const response = await fetch(resolveCollectorEndpoint(), {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
				[EVENTS_SESSION_EXPIRATION_HEADER]: sessionExpirationTime
			},
			body: JSON.stringify(payload)
		});

		if (!response.ok) {
			console.warn('Failed to send book event', {
				status: response.status,
				event,
				bookId
			});
		}
	} catch (error) {
		console.warn('Failed to send book event', { event, bookId, error });
	}
}
