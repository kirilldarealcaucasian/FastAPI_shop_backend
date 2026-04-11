import { derived, writable } from 'svelte/store';
import type { Book } from './types';

export type CatalogState = {
	books: Book[];
	categories: string[];
	loading: boolean;
	error: string | null;
};

const initialState: CatalogState = {
	books: [],
	categories: [],
	loading: false,
	error: null
};

function createCatalogStore() {
	const { subscribe, update, set } = writable<CatalogState>(initialState);

	return {
		subscribe,
		hydrate: (books: Book[], categories: string[]) =>
			set({ books, categories, loading: false, error: null }),
		setLoading: (loading: boolean) => update((state) => ({ ...state, loading })),
		setError: (error: string | null) => update((state) => ({ ...state, error, loading: false }))
	};
}

export const catalog = createCatalogStore();

export const catalogBooks = derived(catalog, (state) => state.books);

export const genreOptions = derived(catalog, (state) => {
	const categories = Array.from(new Set(state.categories)).sort((a, b) => a.localeCompare(b));
	return ['Все', ...categories] as const;
});
