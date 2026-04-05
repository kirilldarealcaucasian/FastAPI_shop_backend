import { writable } from 'svelte/store';
import { browser } from '$app/environment';

function createTheme() {
    const { subscribe, set, update } = writable<'light' | 'dark'>('light');

    function apply(mode: 'light' | 'dark') {
        if (!browser) return;
        document.documentElement.classList.toggle('dark', mode === 'dark');
    }

    return {
        subscribe,
        init: () => {
            if (!browser) return;
            const saved = (localStorage.getItem('theme') as 'light' | 'dark' | null) ?? 'light';
            set(saved);
            apply(saved);
        },
        toggle: () =>
            update((m) => {
                const next = m === 'dark' ? 'light' : 'dark';
                if (browser) localStorage.setItem('theme', next);
                apply(next);
                return next;
            })
    };
}

export const theme = createTheme();
