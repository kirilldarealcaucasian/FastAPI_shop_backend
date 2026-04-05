<script lang="ts">
	import Header from '$lib/components/layout/Header.svelte';
	import Footer from '$lib/components/layout/Footer.svelte';
	import FiltersSidebar from '$lib/components/catalog/FiltersSidebar.svelte';
	import ActiveChips from '$lib/components/catalog/ActiveChips.svelte';
	import BookGrid from '$lib/components/catalog/BookGrid.svelte';
	import QuickViewModal from '$lib/components/modal/QuickViewModal.svelte';
	import CartDrawer from '$lib/components/cart/CartDrawer.svelte';

	let cartOpen = false;
</script>

<Header onOpenCart={() => (cartOpen = true)} />

<main class="mx-auto grid max-w-7xl grid-cols-12 gap-8 px-4 py-8 sm:px-6 lg:px-8">
	<aside class="col-span-12 lg:col-span-3">
		<FiltersSidebar />
	</aside>

	<section class="col-span-12 lg:col-span-9">
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
