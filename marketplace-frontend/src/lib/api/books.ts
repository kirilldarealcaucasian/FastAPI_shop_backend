import type { ApiBook } from './types';
import { apiRequest } from './http';

export type GetBooksParams = {
	limit?: number;
	page?: number;
	name?: string;
	minPrice?: number;
	maxPrice?: number;
	category?: string;
	orderBy?: string;
};

export async function getBooks(
	params: GetBooksParams = {},
	fetchImpl?: typeof fetch
): Promise<ApiBook[]> {
	return apiRequest<ApiBook[]>('/books', {
		fetchImpl,
		query: {
			limit: params.limit ?? 200,
			page: params.page ?? 0,
			name__ilike: params.name,
			price_with_discount__gt: params.minPrice,
			price_with_discount__lt: params.maxPrice,
			category_name__eq: params.category,
			order_by: params.orderBy
		}
	});
}
