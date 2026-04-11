import { derived, get, writable } from 'svelte/store';

import {
	addBookToCart,
	clearCart as clearCartApi,
	deleteBookFromCart,
	getCart
} from '$lib/api/cart';
import type { ApiCart } from '$lib/api/types';
import { catalogBooks } from '$lib/modules/catalog/store';
import type { Book } from '$lib/modules/catalog/types';
import { mapCartItem, type CartEntry } from '$lib/modules/cart/types';

type CartState = Map<number, CartEntry>;

function toMap(items: CartEntry[]): CartState {
	return new Map(items.map((item) => [item.book.id, item]));
}

function toBookLookup(books: Book[]): Map<number, Book> {
	return new Map(books.map((book) => [book.id, book]));
}

function createCart() {
	const { subscribe, update, set } = writable<CartState>(new Map());

	const applyApiCart = (payload: ApiCart) => {
		const lookup = toBookLookup(get(catalogBooks));
		const mapped = payload.books.map((item) => mapCartItem(item, lookup));
		set(toMap(mapped));
	};

	const fallbackAdd = (book: Book) => {
		update((m) => {
			const next = new Map(m);
			const cur = next.get(book.id) ?? { book, qty: 0 };
			next.set(book.id, { book: cur.book, qty: cur.qty + 1 });
			return next;
		});
	};

	const fallbackDec = (id: number) => {
		update((m) => {
			const next = new Map(m);
			const entry = next.get(id);
			if (!entry) return next;
			if (entry.qty <= 1) {
				next.delete(id);
				return next;
			}
			next.set(id, { ...entry, qty: entry.qty - 1 });
			return next;
		});
	};

	return {
		subscribe,
		sync: async () => {
			try {
				const payload = await getCart();
				applyApiCart(payload);
			} catch {
				// Cart can be unavailable before auth/session init.
			}
		},
		add: async (book: Book) => {
			fallbackAdd(book);
			try {
				const payload = await addBookToCart(book.id, 1);
				applyApiCart(payload);
			} catch {
				// Keep optimistic local cart when backend cart is unavailable.
			}
		},
		inc: async (id: number) => {
			const book = get(catalogBooks).find((item) => item.id === id);
			if (book) fallbackAdd(book);
			try {
				const payload = await addBookToCart(id, 1);
				applyApiCart(payload);
			} catch {
				// Keep optimistic local cart when backend cart is unavailable.
			}
		},
		dec: async (id: number) => {
			fallbackDec(id);
			try {
				const payload = await deleteBookFromCart(id, 1);
				applyApiCart(payload);
			} catch {
				// Keep optimistic local cart when backend cart is unavailable.
			}
		},
		remove: async (id: number) => {
			const qty = get(cartItems).find((entry) => entry.book.id === id)?.qty ?? 0;
			if (qty === 0) return;

			update((m) => {
				const next = new Map(m);
				next.delete(id);
				return next;
			});

			try {
				const payload = await deleteBookFromCart(id, qty);
				applyApiCart(payload);
			} catch {
				// Keep optimistic local cart when backend cart is unavailable.
			}
		},
		clear: async () => {
			set(new Map());
			try {
				await clearCartApi();
			} catch {
				// Ignore backend clear errors in optimistic mode.
			}
		}
	};
}

export const cart = createCart();

export const cartCount = derived(cart, ($c) =>
	Array.from($c.values()).reduce((n, entry) => n + entry.qty, 0)
);

export const cartSubtotal = derived(cart, ($c) =>
	Array.from($c.values()).reduce((sum, entry) => sum + entry.book.price * entry.qty, 0)
);

export const cartItems = derived(cart, ($c) => Array.from($c.values()));
