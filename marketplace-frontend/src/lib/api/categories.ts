import type { ApiCategory } from './types';
import { apiRequest } from './http';

export async function getCategories(fetchImpl?: typeof fetch): Promise<ApiCategory[]> {
	return apiRequest<ApiCategory[]>('/categories/', { fetchImpl });
}
