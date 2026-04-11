import { writable } from 'svelte/store';
import type { Book } from '$lib/modules/catalog/types';

export const quickView = writable<Book | null>(null);
