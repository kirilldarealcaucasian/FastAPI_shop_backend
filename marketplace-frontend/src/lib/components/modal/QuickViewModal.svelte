<script lang="ts">
	import { sendBookEvent } from '$lib/api/events';
	import { quickView } from '$lib/stores/modal';
	import { cart } from '$lib/stores/cart';
	import { fmtEUR } from '$lib/utils/money';

	const LONG_READ_TIMEOUT_MS = 15_000;

	const close = () => quickView.set(null);

	function onKeydown(e: KeyboardEvent) {
		if (!$quickView) return;
		if (e.key === 'Escape') close();
	}

	function addToCartFromQuickView(): void {
		if (!$quickView) return;
		const selectedBook = $quickView;
		cart.add(selectedBook);
		void sendBookEvent({ bookId: selectedBook.id, event: 'cart' });
		close();
	}

	$effect(() => {
		if (!$quickView || typeof window === 'undefined') return;
		const bookId = $quickView.id;
		const timerId = window.setTimeout(() => {
			void sendBookEvent({ bookId, event: 'long_view' });
		}, LONG_READ_TIMEOUT_MS);

		return () => window.clearTimeout(timerId);
	});
</script>

<svelte:window onkeydown={onKeydown} />

{#if $quickView}
	<div class="fixed inset-0 z-50">
		<div class="absolute inset-0 bg-black/50" onclick={close} aria-hidden="true"></div>

		<div class="absolute inset-x-0 top-10 mx-auto max-w-4xl px-4">
			<div class="shadow-soft overflow-hidden rounded-2xl bg-white">
				<div class="grid md:grid-cols-2">
					<img
						class="h-80 w-full object-cover md:h-full"
						src={$quickView.img}
						alt={$quickView.title}
					/>

					<div class="p-6">
						<div class="flex items-start justify-between gap-4">
							<div>
								<h3 class="font-display text-2xl font-bold text-slate-900">{$quickView.title}</h3>
								<p class="mt-1 text-sm text-slate-600">
									{$quickView.author} • {$quickView.genre} • {$quickView.year}
								</p>
							</div>

							<button
								type="button"
								onclick={close}
								class="rounded-xl border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50"
								aria-label="Закрыть"
							>
								✕
							</button>
						</div>

						<p class="mt-5 text-sm text-slate-700">{$quickView.desc}</p>

						<div class="mt-6 flex items-center justify-between">
							<div class="text-lg font-semibold text-slate-900">{fmtEUR($quickView.price)}</div>

							<button
								type="button"
								onclick={addToCartFromQuickView}
								class="shadow-soft rounded-xl bg-[#3c5de6] px-4 py-2 text-sm font-medium text-white hover:bg-[#2f47b8]"
							>
								В корзину
							</button>
						</div>

						<!-- optional: secondary action -->
						<button
							type="button"
							onclick={close}
							class="mt-4 text-sm font-medium text-[#3c5de6] hover:underline"
						>
							Продолжить просмотр
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}
