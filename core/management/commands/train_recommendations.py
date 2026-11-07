import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from sklearn.decomposition import TruncatedSVD
from core.models import Book, BookRecommendation # Ajusta 'books.models' al nombre de tu app

class Command(BaseCommand):
    help = "Entrena el modelo de recomendaciones con datos sintéticos basados en arquetipos"

    def handle(self, *args, **options):
        self.stdout.write("Extrayendo libros de la base de datos...")
        books_qs = Book.objects.filter(is_active=True).values("id", "category")
        df_books = pd.DataFrame(list(books_qs))
        
        if len(df_books) < 5:
            self.stdout.write(self.style.ERROR("Faltan libros para entrenar el modelo."))
            return

        df_books["category"] = df_books["category"].fillna("General").str.strip()
        categories = df_books["category"].unique()

        # Simular compras
        np.random.seed(42)
        purchases = []
        for user_id in range(1, 151):
            fav_category = np.random.choice(categories)
            is_fav = df_books["category"] == fav_category
            probs = np.where(is_fav, 0.98, 0.02)
            probs /= probs.sum()
            
            num_purchases = min(len(df_books), np.random.randint(3, 9))
            bought_ids = np.random.choice(df_books["id"].values, size=num_purchases, replace=False, p=probs)
            
            for b_id in bought_ids:
                purchases.append({"user_id": user_id, "book_id": b_id, "interaction": 1})

        # Entrenar modelo
        self.stdout.write("Entrenando TruncatedSVD...")
        df_purchases = pd.DataFrame(purchases)
        user_item_matrix = df_purchases.pivot_table(index="user_id", columns="book_id", values="interaction", fill_value=0)
        
        n_components = max(2, min(len(categories) + 2, user_item_matrix.shape[1] - 1, 10))
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        item_factors = svd.fit_transform(user_item_matrix.T)
        
        norms = np.linalg.norm(item_factors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        sim_matrix = np.dot(item_factors / norms, (item_factors / norms).T)

        # Guardar resultados
        book_ids = list(user_item_matrix.columns)
        books_map = {b.id: b for b in Book.objects.filter(id__in=book_ids)}
        recs_to_create = []

        for idx, b_id in enumerate(book_ids):
            scores = sim_matrix[idx]
            ranked_indices = np.argsort(scores)[::-1]
            ranked_indices = [i for i in ranked_indices if i != idx][:15] # Top 15

            for rank, r_idx in enumerate(ranked_indices, start=1):
                recs_to_create.append(BookRecommendation(
                    book=books_map[b_id],
                    recommended_book=books_map[book_ids[r_idx]],
                    score=float(scores[r_idx]),
                    rank=rank
                ))

        with transaction.atomic():
            BookRecommendation.objects.all().delete()
            BookRecommendation.objects.bulk_create(recs_to_create, batch_size=500)

        self.stdout.write(self.style.SUCCESS(f"¡Éxito! {len(recs_to_create)} recomendaciones guardadas."))