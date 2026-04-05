export type Book = {
    id: string;
    title: string;
    author: string;
    price: number;
    genre: string;
    year: number;
    img: string;
    desc: string;
};

export const BOOKS: Book[] = [
    { id: 'bk1', title: 'Тихая библиотека', author: 'М. Астер', price: 14.99, genre: 'Детектив', year: 2024, img: 'https://images.unsplash.com/photo-1521587760476-6c12a4b040da?q=80&w=1200&auto=format&fit=crop', desc: 'Камерный детектив, где каждый читатель может оказаться подозреваемым.' },
    { id: 'bk2', title: 'Ржавчина и звездный свет', author: 'Кай Люмен', price: 18.50, genre: 'Научная фантастика', year: 2025, img: 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?q=80&w=1200&auto=format&fit=crop', desc: 'Команда спасателей находит дрейфующий корабль с невозможной картой.' },
    { id: 'bk3', title: 'Гербарий', author: 'Лин Парк', price: 12.00, genre: 'Нон-фикшн', year: 2022, img: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?q=80&w=1200&auto=format&fit=crop', desc: 'Карманный путеводитель по съедобным растениям с рисованными иллюстрациями.' },
    { id: 'bk4', title: 'Алгоритмы у камина', author: 'Ана Роша', price: 29.00, genre: 'Программирование', year: 2025, img: 'https://images.unsplash.com/photo-1526318472351-c75fcf070305?q=80&w=1200&auto=format&fit=crop', desc: 'Задачи в формате собеседований с наглядными разъяснениями решений.' },
    { id: 'bk5', title: 'Двор эха', author: 'Дж. Нур', price: 16.75, genre: 'Фэнтези', year: 2023, img: 'https://images.unsplash.com/photo-1473862170186-2ae92c47a884?q=80&w=1200&auto=format&fit=crop', desc: 'Бард ищет песню, способную стереть с лица земли целый город.' },
    { id: 'bk6', title: 'Вероятностные паттерны', author: 'Э. Карим', price: 34.00, genre: 'Наука о данных', year: 2024, img: 'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?q=80&w=1200&auto=format&fit=crop', desc: 'Интуитивное введение в выводы, Байес и работу с неопределенностью.' },
    { id: 'bk7', title: 'Svelte на практике', author: 'Р. Хсу', price: 25.00, genre: 'Программирование', year: 2024, img: 'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?q=80&w=1200&auto=format&fit=crop', desc: 'Идиоматические подходы и практические советы для продакшн-проектов на SvelteKit.' },
    { id: 'bk8', title: 'Непереводимое', author: 'М. Чен', price: 11.99, genre: 'Лингвистика', year: 2021, img: 'https://images.unsplash.com/photo-1521587760476-6c12a4b040da?q=80&w=1200&auto=format&fit=crop', desc: 'Путешествие по словам, которым сложно найти точные соответствия в других языках.' },
];

export const GENRES = ['Все', 'Программирование', 'Наука о данных', 'Научная фантастика', 'Фэнтези', 'Детектив', 'Нон-фикшн', 'Лингвистика'] as const;
