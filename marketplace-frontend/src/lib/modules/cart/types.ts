import type { ApiAssocBook } from '$lib/api/types';
import type { Book } from '$lib/modules/catalog/types';

export type CartEntry = { book: Book; qty: number };

const FALLBACK_IMAGE =
	'https://images.unsplash.com/photo-1521587760476-6c12a4b040da?q=80&w=1200&auto=format&fit=crop';

function toNumber(value: number | string): number {
	if (typeof value === 'number') return value;
	const parsed = Number(value);
	return Number.isFinite(parsed) ? parsed : 0;
}

function buildFallbackBook(item: ApiAssocBook): Book {
	const category = item.categories[0] ?? 'Другое';
	return {
		id: item.book_id,
		title: item.book_title,
		author: item.authors.join(', '),
		price: toNumber(item.price_per_unit),
		genre: category,
		year: new Date().getFullYear(),
		img: FALLBACK_IMAGE,
		desc: 'Описание скоро появится.',
		isbn: '',
		rating: item.rating,
		inStock: 0,
		discount: toNumber(item.discount),
		categories: item.categories,
		authors: item.authors
	};
}

export function mapCartItem(item: ApiAssocBook, booksById: Map<number, Book>): CartEntry {
	const existing = booksById.get(item.book_id);
	return {
		book: existing ?? buildFallbackBook(item),
		qty: item.count_ordered
	};
}
