<script lang="ts">
	import Header from '$lib/components/layout/Header.svelte';
	import Footer from '$lib/components/layout/Footer.svelte';
	import FiltersSidebar from '$lib/components/catalog/FiltersSidebar.svelte';
	import ActiveChips from '$lib/components/catalog/ActiveChips.svelte';
	import BookGrid from '$lib/components/catalog/BookGrid.svelte';
	import QuickViewModal from '$lib/components/modal/QuickViewModal.svelte';
	import CartDrawer from '$lib/components/cart/CartDrawer.svelte';
	import { catalog } from '$lib/modules/catalog/store';
	import { cart } from '$lib/stores/cart';
	import type { CatalogPageData } from './+page';

	let { data } = $props<{ data: CatalogPageData }>();

	let cartOpen = $state(false);

	$effect(() => {
		catalog.hydrate(data.books, data.categories);
		void cart.sync();
	});
</script>

<Header onOpenCart={() => (cartOpen = true)} />

<main class="mx-auto grid max-w-7xl grid-cols-12 gap-8 px-4 py-8 sm:px-6 lg:px-8">
	<aside class="col-span-12 lg:col-span-3">
		<FiltersSidebar />
	</aside>

	<section class="col-span-12 lg:col-span-9">
		{#if data.loadError}
			<div class="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
				{data.loadError}
			</div>
		{/if}
		<div class="mb-4 flex items-center justify-between">
			<h2 class="font-display text-2xl font-bold">Каталог книг</h2>
			<!-- resultCount rendered inside BookGrid or a small component -->
		</div>

		<ActiveChips />
		<BookGrid />
	</section>
</main>

<QuickViewModal />
<CartDrawer open={cartOpen} onClose={() => (cartOpen = false)} />

<Footer />
