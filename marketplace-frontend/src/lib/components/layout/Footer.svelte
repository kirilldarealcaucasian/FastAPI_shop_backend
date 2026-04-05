<script lang="ts">
	const year = new Date().getFullYear();
</script>

<footer class="mt-14 border-t border-slate-200 dark:border-slate-800">
	<div class="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
		<div class="grid grid-cols-1 gap-10 md:grid-cols-4">
			<!-- Brand -->
			<div class="md:col-span-2">
				<div class="flex items-center gap-2">
					<div
						class="bg-brand-600 shadow-soft grid h-9 w-9 place-items-center rounded-2xl text-white"
					>
						<span class="font-display font-bold">B</span>
					</div>
					<div>
						<div class="font-display text-lg font-bold">BookShop</div>
						<div class="muted -mt-0.5 text-sm">Отобранные книги. Удобный выбор.</div>
					</div>
				</div>

				<p class="muted mt-4 max-w-prose text-sm">
					Изучайте подборку книг с быстрыми фильтрами, быстрым просмотром и простой корзиной.
					Сегодня это демоданные, завтра - подключение реального бэкенда.
				</p>

				<div class="mt-5 flex gap-3">
					<a class="muted hover:text-brand-600 text-sm underline" href="/">Главная</a>
					<a class="muted hover:text-brand-600 text-sm underline" href="#catalog">Каталог</a>
					<a class="muted hover:text-brand-600 text-sm underline" href="#support">Поддержка</a>
				</div>
			</div>

			<!-- Links -->
			<div>
				<h4 class="font-semibold">Магазин</h4>
				<ul class="mt-3 space-y-2 text-sm">
					<li><a class="muted hover:text-brand-600" href="#">Новинки</a></li>
					<li><a class="muted hover:text-brand-600" href="#">Бестселлеры</a></li>
					<li><a class="muted hover:text-brand-600" href="#">Жанры</a></li>
					<li><a class="muted hover:text-brand-600" href="#">Подарочные карты</a></li>
				</ul>
			</div>

			<!-- Newsletter -->
			<div>
				<h4 class="font-semibold">Получать обновления</h4>
				<p class="muted mt-3 text-sm">Ежемесячные подборки и новости сервиса.</p>

				<form class="mt-4 flex gap-2" on:submit|preventDefault={() => {}}>
					<input
						type="email"
						placeholder="ваш@email.ru"
						class="focus:ring-brand-500 flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm focus:ring-2 focus:outline-none dark:border-slate-800 dark:bg-slate-950"
					/>
					<button
						class="bg-accent-500 hover:bg-accent-600 shadow-soft rounded-2xl px-4 py-2 text-sm text-white"
						type="submit"
					>
						Подписаться
					</button>
				</form>

				<p class="muted mt-3 text-xs">Без спама. Можно отписаться в любой момент.</p>
			</div>
		</div>

		<div
			class="mt-10 flex flex-col items-start justify-between gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:items-center dark:border-slate-800"
		>
			<p class="muted text-xs">© {year} BookShop. Все права защищены.</p>
			<div class="flex gap-4 text-xs">
				<a class="muted hover:text-brand-600" href="#">Конфиденциальность</a>
				<a class="muted hover:text-brand-600" href="#">Условия</a>
				<a class="muted hover:text-brand-600" href="#">Файлы cookie</a>
			</div>
		</div>
	</div>
</footer>
