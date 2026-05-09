<script lang="ts">
	import type { Book } from '$lib/modules/catalog/types';
	import { sendBookEvent } from '$lib/api/events';
	import { fmtEUR } from '$lib/utils/money';
	import { cart } from '$lib/stores/cart';
	import { quickView } from '$lib/stores/modal';

	let { book } = $props<{ book: Book }>();

	const open = () => {
		quickView.set(book);
		void sendBookEvent({ bookId: book.id, event: 'view' });
	};

	const add = () => {
		cart.add(book);
		void sendBookEvent({ bookId: book.id, event: 'cart' });
	};
</script>

<article
	class="
    group hover:shadow-soft overflow-hidden rounded-2xl border
    border-slate-200 bg-white transition dark:border-slate-800
    dark:bg-gradient-to-b dark:from-slate-900 dark:to-slate-950
  "
>
	<!-- Image -->
	<div class="relative">
		<img src={book.img} alt={book.title} class="h-48 w-full object-cover" />

		<button
			type="button"
			onclick={open}
			class="
        absolute top-3 right-3 rounded-xl border border-slate-200 bg-white/90
        px-3 py-1
        text-sm text-slate-900
        backdrop-blur dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100
      "
		>
			Быстрый просмотр
		</button>
	</div>

	<!-- Content -->
	<div class="p-4">
		<div class="flex items-start justify-between gap-4">
			<div>
				<h3 class="leading-tight font-semibold text-slate-900 dark:text-slate-100">
					{book.title}
				</h3>
				<p class="text-sm text-slate-600 dark:text-slate-400">
					{book.author} • {book.genre}
				</p>
			</div>

			<div class="font-semibold text-slate-900 dark:text-slate-100">
				{fmtEUR(book.price)}
			</div>
		</div>

		<p class="mt-3 line-clamp-2 text-sm text-slate-700 dark:text-slate-400">
			{book.desc}
		</p>

		<!-- Actions -->
		<div class="mt-4 flex items-center gap-3">
			<button
				type="button"
				onclick={add}
				class="shadow-soft rounded-xl bg-[#3c5de6] px-4 py-2 text-sm font-medium text-white hover:bg-[#2f47b8]"
			>
				В корзину
			</button>

			<button
				type="button"
				onclick={open}
				class="text-sm font-medium text-[#3c5de6] hover:underline"
			>
				Подробнее
			</button>
		</div>
	</div>
</article>
