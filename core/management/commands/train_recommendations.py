from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import classification_report, confusion_matrix

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from core.models import Book, BookRecommendation


def _precision_at_k(sim_matrix, book_ids, categories, k):
    """Calcula precision@k usando libros de la misma categoría como relevantes."""
    precisions = []
    for index, book_id in enumerate(book_ids):
        ranked_indices = np.argsort(sim_matrix[index])[::-1]
        ranked_indices = [i for i in ranked_indices if i != index][:k]
        if not ranked_indices:
            continue
        relevant = sum(
            categories[book_ids[recommended_index]] == categories[book_id]
            for recommended_index in ranked_indices
        )
        precisions.append(relevant / len(ranked_indices))
    return float(np.mean(precisions)) if precisions else 0.0


def _model_metrics(user_item_matrix, book_ids, categories, component_values):
    metrics = []
    precision_values = {k: [] for k in (1, 3, 5, 10)}
    matrix = user_item_matrix.to_numpy(dtype=float)

    for component_count in component_values:
        model = TruncatedSVD(n_components=component_count, random_state=42)
        item_factors = model.fit_transform(user_item_matrix.T)
        reconstructed = model.inverse_transform(model.transform(matrix.T)).T
        loss = np.mean((matrix - reconstructed) ** 2)

        norms = np.linalg.norm(item_factors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        normalized_factors = item_factors / norms
        sim_matrix = np.dot(normalized_factors, normalized_factors.T)

        for k in precision_values:
            precision_values[k].append(
                _precision_at_k(sim_matrix, book_ids, categories, k)
            )
        metrics.append({
            "components": int(component_count),
            "loss": float(loss),
            "explained_variance": float(model.explained_variance_ratio_.sum()),
        })

    return metrics, [
        {
            "k": k,
            "precision": precision_values[k][-1],
        }
        for k in precision_values
    ]


def _classification_metrics(sim_matrix, book_ids, categories):
    """Evalúa la categoría del vecino más similar como clase predicha."""
    y_true = []
    y_pred = []
    for index, book_id in enumerate(book_ids):
        ranked_indices = np.argsort(sim_matrix[index])[::-1]
        ranked_indices = [i for i in ranked_indices if i != index]
        if not ranked_indices:
            continue
        y_true.append(categories[book_id])
        y_pred.append(categories[book_ids[ranked_indices[0]]])

    labels = sorted(set(y_true) | set(y_pred))
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        target_names=labels,
        zero_division=0,
    )
    return matrix, labels, report


def _save_confusion_matrix(matrix, labels, output_path):
    figure_size = max(8, min(18, len(labels) * 0.75))
    plt.figure(figsize=(figure_size, figure_size * 0.8))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
    )
    plt.title("Matriz de Confusión - Recomendador TruncatedSVD")
    plt.ylabel("Categoría real")
    plt.xlabel("Categoría predicha")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _save_metrics_charts(model_metrics, precision_at_k, output_path):
    """Genera y guarda los 3 gráficos de métricas en formato PNG."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # 1. Gráfico de Pérdida
    components = [m["components"] for m in model_metrics]
    losses = [m["loss"] for m in model_metrics]
    axes[0].plot(components, losses, marker='o', color='#e74c3c', linewidth=2)
    axes[0].set_title("Pérdida del Modelo vs Componentes", fontsize=12, fontweight='bold')
    axes[0].set_xlabel("Número de Componentes")
    axes[0].set_ylabel("Error de Reconstrucción (MSE)")
    axes[0].grid(True, linestyle='--', alpha=0.7)

    # 2. Gráfico de Varianza Explicada
    variances = [m["explained_variance"] * 100 for m in model_metrics]
    axes[1].plot(components, variances, marker='s', color='#2ecc71', linewidth=2)
    axes[1].set_title("Varianza Explicada vs Componentes", fontsize=12, fontweight='bold')
    axes[1].set_xlabel("Número de Componentes")
    axes[1].set_ylabel("Varianza Explicada (%)")
    axes[1].grid(True, linestyle='--', alpha=0.7)

    # 3. Gráfico de Precisión
    ks = [m["k"] for m in precision_at_k]
    precisions = [m["precision"] * 100 for m in precision_at_k]
    axes[2].plot(ks, precisions, marker='^', color='#3498db', linewidth=2)
    axes[2].set_title("Precisión vs K (Top Recomendaciones)", fontsize=12, fontweight='bold')
    axes[2].set_xlabel("K (Cantidad de recomendaciones mostradas)")
    axes[2].set_ylabel("Precisión (%)")
    axes[2].set_xticks(ks)
    axes[2].grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _terminal_line_chart(title, labels, series, width=58, height=12):
    """Imprime un gráfico de líneas compacto y legible en la terminal."""
    values = [value for _, values in series for value in values]
    minimum = min(values)
    maximum = max(values)
    value_range = maximum - minimum or 1
    chart = [[" " for _ in range(width)] for _ in range(height)]

    for _, values in series:
        for index, value in enumerate(values):
            x = round(index * (width - 1) / max(len(labels) - 1, 1))
            y = round((maximum - value) * (height - 1) / value_range)
            chart[y][x] = "*"

    print(f"\n{title}")
    print(f"{maximum:>8.4f} |" + "".join("".join(row) for row in chart))
    for row_index, row in enumerate(chart):
        if row_index:
            print("         |" + "".join(row))
    print(f"{minimum:>8.4f} |" + "-" * width)
    print("          " + " ".join(str(label) for label in labels))
    print("          " + " " * max(0, width - 18) + "Componentes")
    for name, _ in series:
        print(f"  * {name}")


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
        category_by_id = df_books.set_index("id")["category"].to_dict()

        # Simular compras
        np.random.seed(42)
        purchases = []
        # Aumentado a 1000 usuarios sintéticos para dar volumen a la matriz
        for user_id in range(1, 1001):
            fav_category = np.random.choice(categories)
            is_fav = df_books["category"] == fav_category
            # Sesgo mucho más estricto (99.5% hacia su categoría)
            probs = np.where(is_fav, 0.995, 0.005)
            probs /= probs.sum()
            
            # Aumentamos las compras promedio (entre 5 y 12 por usuario)
            num_purchases = min(len(df_books), np.random.randint(5, 13))
            bought_ids = np.random.choice(df_books["id"].values, size=num_purchases, replace=False, p=probs)
            
            for b_id in bought_ids:
                purchases.append({"user_id": user_id, "book_id": b_id, "interaction": 1})

        # Entrenar modelo
        self.stdout.write("Entrenando TruncatedSVD...")
        df_purchases = pd.DataFrame(purchases)
        user_item_matrix = df_purchases.pivot_table(index="user_id", columns="book_id", values="interaction", fill_value=0)
        
        # Aumentamos el límite de componentes a 35 para cubrir las 16 categorías
        n_components = max(2, min(len(categories) + 10, user_item_matrix.shape[1] - 1, 35))
        # Evaluamos en saltos de 3 en 3 para mantener la consola legible
        component_values = list(range(2, n_components + 1, 3))
        
        model_metrics, precision_at_k = _model_metrics(
            user_item_matrix,
            list(user_item_matrix.columns),
            category_by_id,
            component_values,
        )
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

        # --- GENERACIÓN DE IMÁGENES Y REPORTES ---
        confusion, labels, classification = _classification_metrics(
            sim_matrix,
            book_ids,
            category_by_id,
        )
        
        # Rutas de guardado
        report_directory = Path(__file__).resolve().parents[2] / "ml_reports"
        report_directory.mkdir(parents=True, exist_ok=True)
        
        confusion_path = report_directory / "matriz_confusion_recomendaciones.png"
        charts_path = report_directory / "graficos_metricas_modelo.png"
        
        # Guardar las imágenes
        _save_confusion_matrix(confusion, labels, confusion_path)
        _save_metrics_charts(model_metrics, precision_at_k, charts_path)

        with transaction.atomic():
            BookRecommendation.objects.all().delete()
            BookRecommendation.objects.bulk_create(recs_to_create, batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f"¡Éxito! {len(recs_to_create)} recomendaciones guardadas."
        ))
        
        # --- SALIDAS EN LA TERMINAL ---
        self.stdout.write("\nMÉTRICAS DEL MODELO")
        self.stdout.write(
            f"Libros activos: {len(df_books)} | "
            f"Usuarios sintéticos: 1000 | "
            f"Interacciones: {len(df_purchases)} | "
            f"Componentes usados: {n_components}"
        )
        self.stdout.write("\nComponentes | Pérdida | Varianza explicada")
        for metric in model_metrics:
            self.stdout.write(
                f"{metric['components']:>10} | "
                f"{metric['loss']:.6f} | "
                f"{metric['explained_variance']:.2%}"
            )
        self.stdout.write("\nPrecisión de recomendaciones")
        for metric in precision_at_k:
            self.stdout.write(
                f"Precision@{metric['k']}: {metric['precision']:.2%}"
            )
        component_labels = [metric["components"] for metric in model_metrics]
        
        _terminal_line_chart(
            "GRÁFICO DE PÉRDIDA",
            component_labels,
            [("Pérdida", [metric["loss"] for metric in model_metrics])],
        )
        _terminal_line_chart(
            "GRÁFICO DE RENDIMIENTO",
            component_labels,
            [("Varianza explicada", [metric["explained_variance"] for metric in model_metrics])],
        )
        _terminal_line_chart(
            "GRÁFICO DE PRECISIÓN",
            [metric["k"] for metric in precision_at_k],
            [("Precision@k", [metric["precision"] for metric in precision_at_k])],
        )
        
        self.stdout.write("\nREPORTE DE CLASIFICACIÓN")
        self.stdout.write(classification)
        self.stdout.write(f"Matriz de Confusión guardada en: {confusion_path}")
        self.stdout.write(f"Gráficos de Métricas guardados en: {charts_path}")