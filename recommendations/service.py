from __future__ import annotations

from functools import cached_property
from pathlib import Path

import numpy as np

from recommendations.schemas import CandidateScore, UserInteraction


class BookFactorsStore:
    def __init__(self, factors_path: str, book_ids_path: str | None = None) -> None:
        self._factors_path = Path(factors_path)
        self._book_ids_path = Path(book_ids_path) if book_ids_path else None

    @cached_property
    def factors(self) -> np.ndarray:
        if not self._factors_path.exists():
            raise FileNotFoundError(
                f"Books factors file does not exist: {self._factors_path}"
            )
        factors = np.load(self._factors_path, mmap_mode="r")
        if factors.ndim != 2:
            raise ValueError(
                "Books factors must be a 2D matrix of shape "
                "[n_books, embedding_dim]."
            )
        return factors

    @cached_property
    def index_to_book_id(self) -> np.ndarray:
        if not self._book_ids_path:
            return np.arange(self.factors.shape[0], dtype=np.int64)

        if not self._book_ids_path.exists():
            raise FileNotFoundError(
                f"Book ids mapping file does not exist: {self._book_ids_path}"
            )

        book_ids = np.load(self._book_ids_path, mmap_mode="r")
        if book_ids.ndim != 1:
            raise ValueError("Book ids file must be a 1D vector.")
        if book_ids.shape[0] != self.factors.shape[0]:
            raise ValueError(
                "Book ids vector length must match number of rows in books factors."
            )
        return book_ids.astype(np.int64, copy=False)

    @cached_property
    def book_id_to_index(self) -> dict[int, int]:
        return {
            int(book_id): int(idx)
            for idx, book_id in enumerate(self.index_to_book_id.tolist())
        }


class RecommendationService:
    def __init__(self, factors_store: BookFactorsStore, candidates_limit: int) -> None:
        if candidates_limit <= 0:
            raise ValueError("RECOMMENDATIONS_CANDIDATES must be greater than zero.")
        self._factors_store = factors_store
        self._candidates_limit = candidates_limit

    def recommend(self, interactions: list[UserInteraction]) -> list[CandidateScore]:
        if not interactions:
            raise ValueError("recent_interactions cannot be empty.")

        factors = self._factors_store.factors
        book_id_to_index = self._factors_store.book_id_to_index

        valid_indexes: list[int] = []
        weights: list[float] = []
        seen_interacted: set[int] = set()
        for interaction in interactions:
            if interaction.book_id in book_id_to_index:
                index = book_id_to_index[interaction.book_id]
                valid_indexes.append(index)
                weights.append(interaction.weight)
                seen_interacted.add(index)

        if not valid_indexes:
            raise ValueError(
                "None of the recent_interactions book_id values exists in factors map."
            )

        interaction_factors = factors[np.array(valid_indexes, dtype=np.int64)]
        interaction_weights = np.array(weights, dtype=np.float32).reshape(-1, 1)
        # Weighted mean of interacted item embeddings as the user embedding.
        user_embedding = np.sum(interaction_factors * interaction_weights, axis=0)
        weight_sum = float(np.sum(interaction_weights))
        if weight_sum <= 0:
            raise ValueError("Sum of interaction weights must be positive.")
        user_embedding /= weight_sum

        scores = factors @ user_embedding
        if seen_interacted:
            scores[np.array(list(seen_interacted), dtype=np.int64)] = -np.inf

        total_books = scores.shape[0]
        top_k = min(self._candidates_limit, total_books)
        if top_k == 0:
            return []

        top_indices_unsorted = np.argpartition(scores, -top_k)[-top_k:]
        top_indices = top_indices_unsorted[np.argsort(scores[top_indices_unsorted])[::-1]]

        index_to_book_id = self._factors_store.index_to_book_id
        recommendations: list[CandidateScore] = []
        for idx in top_indices.tolist():
            score = float(scores[idx])
            if not np.isfinite(score):
                continue
            recommendations.append(
                CandidateScore(book_id=int(index_to_book_id[idx]), score=score)
            )
        return recommendations
