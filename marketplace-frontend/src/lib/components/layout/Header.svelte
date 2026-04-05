<script lang="ts">
	import { filters } from '$lib/stores/filters';
	import { cartCount } from '$lib/stores/cart';
	import { theme } from '$lib/stores/theme';

	let { onOpenCart } = $props<{ onOpenCart?: () => void }>();

	function setQuery(v: string) {
		filters.update((f) => ({ ...f, q: v }));
	}
</script>

<header
	class="sticky top-0 z-40 border-b border-slate-100 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-900/70"
>
	<div class="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
		<a href="/" class="flex items-center gap-2">
			<div class="bg-brand-600 grid h-9 w-9 place-items-center rounded-xl font-bold text-white">
				📚
			</div>
			<span class="font-display text-xl"> BookShop </span>
		</a>

		<div class="flex-1">
			<label class="sr-only" for="q">Поиск</label>
			<input
				id="q"
				value={$filters.q}
				oninput={(e) => setQuery((e.currentTarget as HTMLInputElement).value)}
				placeholder="Поиск по книгам, авторам, ISBN…"
				class="focus:ring-brand-500 w-full rounded-xl border border-slate-200 bg-white/70 px-4 py-2.5 focus:ring-2 focus:outline-none dark:border-slate-700 dark:bg-slate-950/40"
			/>
		</div>

		<button
			id="themeToggle"
			class="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700"
			type="button"
			onclick={() => theme.toggle()}
			aria-label="Сменить тему"
			title="Сменить тему"
		>
			🌓
		</button>

		<button
			type="button"
			onclick={() => onOpenCart?.()}
			class="shadow-soft relative rounded-xl bg-[#3c5de6] px-4 py-2 font-medium text-white hover:bg-[#2f47b8]"
		>
			Корзина
			<span
				class="ml-2 inline-flex h-6 min-w-6 items-center justify-center rounded-full bg-white/90 px-1 text-xs text-[#2f47b8]"
				aria-label="Количество товаров в корзине"
			>
				{$cartCount}
			</span>
		</button>
	</div>
</header>
