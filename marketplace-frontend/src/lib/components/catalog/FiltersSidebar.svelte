<script lang="ts">
	import { filters, type SortKey } from '$lib/stores/filters';
	import { genreOptions } from '$lib/modules/catalog/store';

	function toggleGenre(genre: string) {
		filters.update((f) => {
			const nextGenres = new Set(f.genres);

			if (genre === 'Все') {
				nextGenres.clear();
				nextGenres.add('Все');
			} else {
				nextGenres.delete('Все');
				if (nextGenres.has(genre)) nextGenres.delete(genre);
				else nextGenres.add(genre);

				if (nextGenres.size === 0) nextGenres.add('Все');
			}

			return { ...f, genres: nextGenres };
		});
	}

	function setMin(v: string) {
		const n = v.trim() === '' ? null : Number(v);
		filters.update((f) => ({ ...f, min: Number.isFinite(n as number) ? (n as number) : null }));
	}

	function setMax(v: string) {
		const n = v.trim() === '' ? null : Number(v);
		filters.update((f) => ({ ...f, max: Number.isFinite(n as number) ? (n as number) : null }));
	}

	function setSort(v: string) {
		filters.update((f) => ({ ...f, sort: v as SortKey }));
	}

	function reset() {
		filters.set({
			q: '',
			genres: new Set(['Все']),
			min: null,
			max: null,
			sort: 'popularity'
		});
	}
</script>

<div
	class="sticky top-6 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-transparent"
>
	<div class="flex items-center justify-between">
		<h3 class="font-display text-lg font-bold">Фильтры</h3>
		<button class="muted text-sm underline" onclick={reset}>Сбросить</button>
	</div>

	<div class="mt-5">
		<p class="mb-2 text-sm font-semibold">Жанр</p>
		<div class="flex flex-wrap gap-2">
			{#each $genreOptions as g}
				<button
					type="button"
					onclick={() => toggleGenre(g)}
					class={'rounded-xl border px-3 py-1.5 text-sm transition ' +
						($filters.genres.has(g)
							? 'border-[#3c5de6] bg-[#3c5de6] text-white'
							: 'border-slate-200 bg-white text-slate-900 hover:bg-slate-50')}
				>
					{g}
				</button>
			{/each}
		</div>
	</div>

	<div class="mt-6">
		<p class="mb-2 text-sm font-semibold">Цена</p>
		<div class="grid grid-cols-2 gap-3">
			<label class="text-sm">
				<span class="muted">От</span>
				<input
					class="focus:ring-brand-500 focus:border-brand-500 mt-1 w-full rounded-xl border border-slate-300 bg-white px-3
                 py-2 text-sm focus:ring-2 focus:outline-none
                 dark:border-slate-700 dark:bg-slate-950"
					inputmode="decimal"
					value={$filters.min ?? ''}
					oninput={(e) => setMin((e.currentTarget as HTMLInputElement).value)}
					placeholder="0"
				/>
			</label>

			<label class="text-sm">
				<span class="muted">До</span>
				<input
					class="focus:ring-brand-500 focus:border-brand-500 mt-1 w-full rounded-xl border border-slate-300 bg-white px-3
                 py-2 text-sm focus:ring-2 focus:outline-none
                 dark:border-slate-700 dark:bg-slate-950"
					inputmode="decimal"
					value={$filters.max ?? ''}
					oninput={(e) => setMax((e.currentTarget as HTMLInputElement).value)}
					placeholder="50"
				/>
			</label>
		</div>
	</div>

	<div class="mt-6">
		<p class="mb-2 text-sm font-semibold">Сортировка</p>
		<select
			class="focus:ring-brand-500 focus:border-brand-500 w-full rounded-xl border border-slate-300 bg-white px-3
             py-2 text-sm focus:ring-2 focus:outline-none
             dark:border-slate-700 dark:bg-slate-950"
			value={$filters.sort}
			onchange={(e) => setSort((e.currentTarget as HTMLSelectElement).value)}
		>
			<option value="popularity">По популярности</option>
			<option value="new">Сначала новые</option>
			<option value="priceAsc">Цена: по возрастанию</option>
			<option value="priceDesc">Цена: по убыванию</option>
			<option value="title">Название (А-Я)</option>
		</select>
	</div>
</div>
