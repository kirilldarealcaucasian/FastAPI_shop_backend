export const fmtEUR = (n: number) =>
	new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(n);
