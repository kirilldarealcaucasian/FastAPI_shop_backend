import { getBooks } from '$lib/api/books';
import { getCategories } from '$lib/api/categories';
import { mapApiBookToBook, type Book } from '$lib/modules/catalog/types';
import type { PageLoad } from './$types';

export type CatalogPageData = {
	books: Book[];
	categories: string[];
	loadError: string | null;
};

export const load: PageLoad = async ({ fetch }) => {
	try {
		const [booksResponse, categoriesResponse] = await Promise.all([
			getBooks({ limit: 200 }, fetch),
			getCategories(fetch)
		]);

		const books = booksResponse.map(mapApiBookToBook);
		const categories = categoriesResponse.map((category) => category.name);

		return {
			books,
			categories,
			loadError: null
		} satisfies CatalogPageData;
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Не удалось загрузить каталог.';
		return {
			books: [],
			categories: [],
			loadError: message
		} satisfies CatalogPageData;
	}
};
