import { writable } from 'svelte/store';
import type { Book } from '$lib/data/mock';

export const quickView = writable<Book | null>(null);
