export type ApiBook = {
	id: number;
	isbn: string;
	name: string;
	summary: string | null;
	price_per_unit: number | string;
	number_in_stock: number;
	categories: string[];
	authors: string[];
	year_of_publication: number;
	language: string;
	country: string;
	publisher: string;
	rating: number | null;
	image: string;
	discount: number | string;
};

export type ApiCategory = {
	name: string;
};

export type ApiAssocBook = {
	book_id: number;
	book_title: string;
	authors: string[];
	categories: string[];
	rating: number;
	discount: number | string;
	count_ordered: number;
	price_per_unit: number | string;
};

export type ApiCart = {
	cart_id: string;
	books: ApiAssocBook[];
};
