# marketplace-backend

## Архитектура проекта

`marketplace-backend` построен по слойной схеме, близкой к Clean Architecture:

1. API-слой (роутеры FastAPI)
2. Сервисный слой (бизнес-логика)
3. Слой репозиториев (доступ к данным)
4. Инфраструктурный слой (PostgreSQL, Redis, MinIO, платежный провайдер)

Ключевой принцип: каждый слой зависит от абстракций (интерфейсов), а не от конкретных реализаций.

---

## 1. API-слой (routers)

Роутеры принимают HTTP-запрос, валидируют входные DTO, получают зависимости через `Depends` и делегируют выполнение сервисам.

Примеры:

- `application/api/v1/routers/book.py`
- `application/api/v1/routers/cart.py`
- `application/api/v1/routers/order.py`

Роутеры не содержат сложной бизнес-логики: они выступают как транспортный слой.

---

## 2. Сервисный слой

Сервисы реализуют бизнес-правила и сценарии использования системы.

- Простые CRUD-сервисы (например, `AuthorService`, `CategoryService`) используют базовые операции из `EntityBaseService`.
- Сложные сервисы (например, `CartService`, `OrderService`, `PaymentService`) координируют несколько репозиториев и других сервисов в рамках бизнес-процесса.

Примеры:

- `application/services/entity_base_service.py`
- `application/services/book_service.py`
- `application/services/author_service.py`
- `application/services/cart_service/cart_service.py`
- `application/services/order_service/order_service.py`
- `application/services/payment_service.py`

---

## 3. Базовый сервис: `EntityBaseService`

`EntityBaseService` выносит общую логику для CRUD-операций:

- `create`
- `get_all`
- `get_by_id`
- `update`
- `delete`
- `commit`

Преимущества:

- исключает дублирование кода в доменных сервисах;
- централизует обработку типовых ошибок;
- обеспечивает единый стиль работы с репозиториями.

Сервис принимает репозиторий как зависимость и работает через его интерфейс (`OrmEntityRepoInterface`), что упрощает расширение и тестирование.

---

## 4. Слой репозиториев

Репозитории инкапсулируют всю работу с БД (SQLAlchemy) и скрывают детали запросов от сервисов.

### 4.1 Базовый репозиторий

В `application/repositories/orm_entity_repo.py` определены:

- `OrmEntityRepoInterface[OrmModelT]` - контракт базовых CRUD-операций;
- `OrmEntityRepository[OrmModelT]` - базовая реализация CRUD.

### 4.2 Доменные репозитории

Доменные репозитории наследуются от базового и добавляют специализированные методы:

- `BookRepository` (`application/repositories/book_repo.py`)
- `CartRepository` (`application/repositories/cart_repo.py`)
- `OrderRepository` (`application/repositories/order_repo.py`)
- `BookOrderAssocRepository` (`application/repositories/book_order_assoc_repo.py`)

Они содержат доменно-ориентированные запросы (join/selectinload/raw SQL), необходимые для конкретных бизнес-сценариев.

---

## 5. Абстракции и интерфейсы (как связаны слои)

В проекте используется протокольная типизация (`typing.Protocol`) для контракта между сервисами и репозиториями.

Примеры:

- `OrmEntityRepoInterface`
- `BookRepoInterface`
- `CartRepositoryInterface`
- `OrderRepositoryInterface`

Для сервисов часто используются комбинированные интерфейсы, например:

- `CombinedBookRepoInterface`
- `CombinedCartRepositoryInterface`
- `CombinedOrderRepositoryInterface`

Они объединяют базовый CRUD-контракт и доменные методы в одном типе зависимости.

Итог: сервис зависит от интерфейса, а не от конкретного класса репозитория.

---

## 6. Dependency Injection и `service_providers`

Связывание абстракций с реализациями происходит в `application/service_providers/*`.

Примеры:

- `application/service_providers/book.py`
- `application/service_providers/cart.py`
- `application/service_providers/order.py`
- `application/service_providers/payment.py`

Именно здесь FastAPI через `Depends(...)` подставляет конкретные реализации (`BookRepository`, `CartRepository`, и т.д.) в сервисы.

Для `OrderService` дополнительно используется `SqlAlchemyUnitOfWork` (в `service_providers/order.py`) для группировки нескольких изменений в одной транзакционной операции.

---

## 7. Сквозной поток запроса

Типичный сценарий:

1. Роутер принимает запрос и получает `AsyncSession`.
2. Через DI получает сервис.
3. Сервис вызывает методы репозиториев через интерфейсы.
4. Репозитории выполняют SQLAlchemy-запросы к PostgreSQL.
5. Результат преобразуется в response-схему и возвращается клиенту.

Пример цепочки:

- `application/api/v1/routers/book.py`
- `application/services/book_service.py`
- `application/repositories/book_repo.py`

---

## 8. Инфраструктура и кросс-срезы

- Инициализация подключений и middleware: `application/cmd.py`
- PostgreSQL-коннектор: `infrastructure/postgres/__init__.py`
- Redis-кэширование (`cachify`): `application/utils/cache.py`
- Централизованное логирование и обработка ошибок: `application/utils/logging_decorator.py`
- Проверка прав доступа: `application/access_control/permission_service.py`
- Идентичность запроса: `application/access_control/identity.py`

---

## Вывод

Архитектура `marketplace-backend` основана на четком разделении ответственности:

- роутеры отвечают за HTTP и DI;
- сервисы - за бизнес-логику;
- репозитории - за доступ к данным;
- абстракции (`Protocol`) обеспечивают слабую связанность между слоями.

Такой подход повышает расширяемость, тестируемость и поддерживаемость проекта, что критично для развития ecommerce-платформы.
