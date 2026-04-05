<script lang="ts">
	import { filters } from '$lib/stores/filters';

	function removeGenre(g: string) {
		filters.update((f) => {
			const next = new Set(f.genres);
			next.delete(g);
			if (next.size === 0) next.add('Все');
			// если удален последний жанр, возвращаемся к значению по умолчанию
			if (!next.has('Все') && next.size === 0) next.add('Все');
			return { ...f, genres: next };
		});
	}

	function clearGenres() {
		filters.update((f) => ({ ...f, genres: new Set(['Все']) }));
	}

	function clearSearch() {
		filters.update((f) => ({ ...f, q: '' }));
	}

	function clearPrice() {
		filters.update((f) => ({ ...f, min: null, max: null }));
	}

	function clearAll() {
		filters.set({
			q: '',
			genres: new Set(['Все']),
			min: null,
			max: null,
			sort: 'popularity'
		});
	}

	const hasPrice = () => $filters.min != null || $filters.max != null;
	const hasSearch = () => $filters.q.trim().length > 0;
	const hasGenres = () => !($filters.genres.size === 1 && $filters.genres.has('Все'));
	const hasAnything = () => hasSearch() || hasGenres() || hasPrice();
</script>

{#if hasAnything()}
	<div class="mb-4 flex flex-wrap items-center gap-2">
		{#if hasSearch()}
			<button
				class="rounded-xl border border-slate-200 bg-slate-100 px-3 py-1.5 text-sm dark:border-slate-800 dark:bg-slate-900"
				on:click={clearSearch}
				title="Убрать поиск"
			>
				Поиск: «{$filters.q}» <span class="muted ml-1">×</span>
			</button>
		{/if}

		{#if hasGenres()}
			{#each Array.from($filters.genres).filter((g) => g !== 'Все') as g}
				<button
					class="rounded-xl border border-slate-200 bg-slate-100 px-3 py-1.5 text-sm dark:border-slate-800 dark:bg-slate-900"
					on:click={() => removeGenre(g)}
					title="Убрать жанр"
				>
					{g} <span class="muted ml-1">×</span>
				</button>
			{/each}
			<button class="muted ml-2 text-sm underline" on:click={clearGenres}>Очистить жанры</button>
		{/if}

		{#if hasPrice()}
			<button
				class="rounded-xl border border-slate-200 bg-slate-100 px-3 py-1.5 text-sm dark:border-slate-800 dark:bg-slate-900"
				on:click={clearPrice}
				title="Убрать цену"
			>
				Цена:
				{$filters.min ?? '0'}–{$filters.max ?? '∞'}
				<span class="muted ml-1">×</span>
			</button>
		{/if}

		<button class="ml-auto text-sm underline" on:click={clearAll}>Очистить все</button>
	</div>
{/if}
