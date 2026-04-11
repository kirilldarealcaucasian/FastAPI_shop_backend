import type { ApiBook } from '$lib/api/types';

export type Book = {
	id: number;
	title: string;
	author: string;
	price: number;
	genre: string;
	year: number;
	img: string;
	desc: string;
	isbn: string;
	rating: number | null;
	inStock: number;
	discount: number;
	categories: string[];
	authors: string[];
};

const FALLBACK_IMAGE =
	'https://images.unsplash.com/photo-1521587760476-6c12a4b040da?q=80&w=1200&auto=format&fit=crop';

function toNumber(value: number | string): number {
	if (typeof value === 'number') return value;
	const parsed = Number(value);
	return Number.isFinite(parsed) ? parsed : 0;
}

export function mapApiBookToBook(book: ApiBook): Book {
	const discount = toNumber(book.discount);
	const pricePerUnit = toNumber(book.price_per_unit);
	const discountedPrice = Math.max(0, pricePerUnit * (1 - discount));

	return {
		id: book.id,
		title: book.name,
		author: book.authors.join(', '),
		price: discountedPrice,
		genre: book.categories[0] ?? 'Другое',
		year: book.year_of_publication,
		img: book.image || FALLBACK_IMAGE,
		desc: book.summary ?? 'Описание скоро появится.',
		isbn: book.isbn,
		rating: book.rating,
		inStock: book.number_in_stock,
		discount,
		categories: book.categories,
		authors: book.authors
	};
}
