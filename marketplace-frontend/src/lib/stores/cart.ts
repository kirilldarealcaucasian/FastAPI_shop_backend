import { writable, derived } from 'svelte/store';
import type { Book } from '$lib/data/mock';

type CartEntry = { book: Book; qty: number };
type CartState = Map<string, CartEntry>;

function createCart() {
    const { subscribe, update, set } = writable<CartState>(new Map());

    return {
        subscribe,
        add: (book: Book) =>
            update((m) => {
                const next = new Map(m);
                const cur = next.get(book.id) ?? { book, qty: 0 };
                next.set(book.id, { book: cur.book, qty: cur.qty + 1 });
                return next;
            }),
        inc: (id: string) =>
            update((m) => {
                const next = new Map(m);
                const e = next.get(id);
                if (e) next.set(id, { ...e, qty: e.qty + 1 });
                return next;
            }),
        dec: (id: string) =>
            update((m) => {
                const next = new Map(m);
                const e = next.get(id);
                if (e) next.set(id, { ...e, qty: Math.max(1, e.qty - 1) });
                return next;
            }),
        remove: (id: string) =>
            update((m) => {
                const next = new Map(m);
                next.delete(id);
                return next;
            }),
        clear: () => set(new Map())
    };
}

export const cart = createCart();

export const cartCount = derived(cart, ($c) =>
    Array.from($c.values()).reduce((n, e) => n + e.qty, 0)
);

export const cartSubtotal = derived(cart, ($c) =>
    Array.from($c.values()).reduce((sum, e) => sum + e.book.price * e.qty, 0)
);

export const cartItems = derived(cart, ($c) => Array.from($c.values()));
