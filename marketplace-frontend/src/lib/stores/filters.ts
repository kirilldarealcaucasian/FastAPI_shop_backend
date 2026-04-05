import { writable, derived } from 'svelte/store';
import { BOOKS } from '$lib/data/mock';

export type SortKey = 'popularity' | 'priceAsc' | 'priceDesc' | 'title' | 'new';

type Filters = {
    q: string;
    genres: Set<string>;
    min: number | null;
    max: number | null;
    sort: SortKey;
};

const initial: Filters = {
    q: '',
    genres: new Set(['Все']),
    min: null,
    max: null,
    sort: 'popularity'
};

export const filters = writable<Filters>(initial);

export const filteredBooks = derived(filters, ($f) => {
    const q = $f.q.trim().toLowerCase();

    let list = BOOKS.filter((b) => {
        const okQ = !q || (b.title + ' ' + b.author).toLowerCase().includes(q);
        const okG = $f.genres.has('Все') || $f.genres.has(b.genre);
        const okMin = $f.min == null || b.price >= $f.min;
        const okMax = $f.max == null || b.price <= $f.max;
        return okQ && okG && okMin && okMax;
    });

    switch ($f.sort) {
        case 'priceAsc': list = [...list].sort((a, b) => a.price - b.price); break;
        case 'priceDesc': list = [...list].sort((a, b) => b.price - a.price); break;
        case 'title': list = [...list].sort((a, b) => a.title.localeCompare(b.title)); break;
        case 'new': list = [...list].sort((a, b) => b.year - a.year); break;
        default: break; // popularity placeholder
    }
    return list;
});

export const resultCount = derived(filteredBooks, (b) => b.length);
