import type { ApiCart } from './types';
import { apiRequest } from './http';

export async function getCart(fetchImpl?: typeof fetch): Promise<ApiCart> {
	return apiRequest<ApiCart>('/cart/', { fetchImpl });
}

export async function addBookToCart(
	bookId: number,
	quantity = 1,
	fetchImpl?: typeof fetch
): Promise<ApiCart> {
	return apiRequest<ApiCart>('/cart/items', {
		method: 'POST',
		fetchImpl,
		body: {
			book_id: bookId,
			quantity
		}
	});
}

export async function deleteBookFromCart(
	bookId: number,
	quantity = 1,
	fetchImpl?: typeof fetch
): Promise<ApiCart> {
	return apiRequest<ApiCart>('/cart/items', {
		method: 'DELETE',
		fetchImpl,
		body: {
			book_id: bookId,
			quantity
		}
	});
}

export async function clearCart(fetchImpl?: typeof fetch): Promise<void> {
	await apiRequest<void>('/cart/', {
		method: 'DELETE',
		fetchImpl
	});
}
