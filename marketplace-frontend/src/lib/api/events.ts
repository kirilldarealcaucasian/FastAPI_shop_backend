import { env } from '$env/dynamic/public';

export type BookEventName =
	| 'description_open'
	| 'description_long_read'
	| 'add_to_cart'
	| 'buy';

type SendBookEventParams = {
	bookId: number;
	event: BookEventName;
	weight?: number;
};

const DEFAULT_COLLECT_ENDPOINT = 'http://localhost:8010/api/v1/events/collect';
const MOCK_SESSION_ID = 'mock-session-frontend';
const MOCK_USER_ID = 1;

function resolveCollectorEndpoint(): string {
	const configured = env.PUBLIC_EVENTS_COLLECTOR_URL?.trim();
	if (!configured) return DEFAULT_COLLECT_ENDPOINT;

	const normalized = configured.replace(/\/$/, '');
	if (normalized.endsWith('/collect')) return normalized;
	return `${normalized}/events/collect`;
}

export async function sendBookEvent({
	bookId,
	event,
	weight = 1
}: SendBookEventParams): Promise<void> {
	const payload = {
		session_id: MOCK_SESSION_ID,
		user_id: MOCK_USER_ID,
		book_id: bookId,
		event,
		ts: Math.floor(Date.now() / 1000),
		weight
	};

	try {
		const response = await fetch(resolveCollectorEndpoint(), {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
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
