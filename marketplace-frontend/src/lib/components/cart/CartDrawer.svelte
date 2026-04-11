<script lang="ts">
	import { sendBookEvent } from '$lib/api/events';
	import { cart, cartItems, cartSubtotal, cartCount } from '$lib/stores/cart';
	import { fmtEUR } from '$lib/utils/money';

	// controlled by parent
	let { open, onClose } = $props<{ open: boolean; onClose?: () => void }>();

	const close = () => onClose?.();

	function checkout(): void {
		for (const item of $cartItems) {
			void sendBookEvent({
				bookId: item.book.id,
				event: 'buy',
				weight: Math.max(2, item.qty)
			});
		}

		// mock checkout for now
		alert('Оформление заказа скоро появится');
	}

	// prevent background scroll when open (nice UX)
	$effect(() => {
		if (typeof document === 'undefined') return;
		document.body.style.overflow = open ? 'hidden' : '';
		return () => {
			document.body.style.overflow = '';
		};
	});
</script>

<!-- Backdrop -->
{#if open}
	<div
		class="fixed inset-0 z-40 bg-slate-950/50 backdrop-blur-sm"
		onclick={close}
		aria-hidden="true"
	></div>
{/if}

<!-- Drawer -->
<div
	class="shadow-soft fixed inset-y-0 right-0 z-50 w-full transform border-l border-slate-200 bg-white transition-transform duration-200 sm:w-[420px] dark:border-slate-800 dark:bg-slate-950
    {open ? 'translate-x-0' : 'translate-x-full'}"
	role="dialog"
	aria-modal="true"
	aria-label="Корзина"
>
	<div class="flex h-full flex-col">
		<!-- Header -->
		<div
			class="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800"
		>
			<div>
				<h3 class="font-display text-lg font-bold">Ваша корзина</h3>
				<p class="muted text-sm">
					{#if $cartCount === 1}
						1 товар
					{:else}
						{$cartCount} товаров
					{/if}
				</p>
			</div>

			<button
				type="button"
				class="rounded-2xl border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
				onclick={close}
				aria-label="Закрыть корзину"
			>
				✕
			</button>
		</div>

		<!-- Items -->
		<div class="flex-1 overflow-auto px-5 py-4">
			{#if $cartItems.length === 0}
				<div class="rounded-2xl border border-slate-200 p-10 text-center dark:border-slate-800">
					<p class="font-semibold">Ваша корзина пуста</p>
					<p class="muted mt-2 text-sm">Добавьте книгу, чтобы начать.</p>
					<button
						class="bg-brand-600 hover:bg-brand-700 shadow-soft mt-5 rounded-2xl px-4 py-2 text-sm text-white"
						onclick={close}
					>
						Продолжить просмотр
					</button>
				</div>
			{:else}
				<ul class="space-y-4">
					{#each $cartItems as item (item.book.id)}
						<li class="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
							<div class="flex gap-4">
								<img
									src={item.book.img}
									alt={item.book.title}
									class="h-20 w-16 rounded-xl border border-slate-200 object-cover dark:border-slate-800"
								/>

								<div class="min-w-0 flex-1">
									<div class="flex items-start justify-between gap-3">
										<div class="min-w-0">
											<p class="truncate font-semibold">{item.book.title}</p>
											<p class="muted truncate text-sm">{item.book.author}</p>
											<p class="mt-1 text-sm">
												<span class="font-semibold">{fmtEUR(item.book.price)}</span>
												<span class="muted"> / шт.</span>
											</p>
										</div>

										<button
											class="muted hover:text-brand-600 text-sm underline"
											onclick={() => cart.remove(item.book.id)}
											aria-label={'Удалить ' + item.book.title}
										>
											Удалить
										</button>
									</div>

									<div class="mt-3 flex items-center justify-between">
										<div
											class="inline-flex items-center overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800"
										>
											<button
												class="px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-900"
												onclick={() => cart.dec(item.book.id)}
												aria-label="Уменьшить количество"
											>
												−
											</button>
											<div class="min-w-10 px-3 py-2 text-center text-sm">
												{item.qty}
											</div>
											<button
												class="px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-900"
												onclick={() => cart.inc(item.book.id)}
												aria-label="Увеличить количество"
											>
												+
											</button>
										</div>

										<div class="text-sm">
											<span class="muted">Сумма:</span>
											<span class="ml-1 font-semibold">{fmtEUR(item.book.price * item.qty)}</span>
										</div>
									</div>
								</div>
							</div>
						</li>
					{/each}
				</ul>
			{/if}
		</div>

		<!-- Footer / Checkout -->
		<div class="border-t border-slate-200 px-5 py-4">
			<div class="mb-3 flex items-center justify-between">
				<span class="text-sm text-slate-600">Итого</span>
				<span class="font-semibold text-slate-900">
					{fmtEUR($cartSubtotal)}
				</span>
			</div>

			<button
				type="button"
				class="shadow-soft w-full rounded-xl bg-[#f97316] px-4 py-3 text-base font-semibold text-white hover:bg-[#ea580c]"
				onclick={checkout}
			>
				Оформить заказ
			</button>
		</div>
	</div>
</div>
