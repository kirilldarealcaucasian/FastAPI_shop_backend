<script lang="ts">
	import { filteredBooks, resultCount } from '$lib/stores/filters';
	import BookCard from './BookCard.svelte';
</script>

<div class="mb-4 flex items-center justify-between">
	<p class="muted text-sm">
		{#if $resultCount === 1}
			1 результат
		{:else}
			{$resultCount} результатов
		{/if}
	</p>
</div>

{#if $filteredBooks.length === 0}
	<div class="rounded-2xl border border-slate-200 p-10 text-center dark:border-slate-800">
		<p class="font-semibold">Книги не найдены</p>
		<p class="muted mt-2 text-sm">Попробуйте изменить параметры поиска или фильтры.</p>
	</div>
{:else}
	<div class="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
		{#each $filteredBooks as book (book.id)}
			<BookCard {book} />
		{/each}
	</div>
{/if}
