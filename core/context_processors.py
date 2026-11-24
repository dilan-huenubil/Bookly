from .models import Book


def book_categories(request):
    categories = (
        Book.objects
        .filter(is_active=True)
        .exclude(category__isnull=True)
        .exclude(category__exact='')
        .values_list('category', flat=True)
        .distinct()
    )
    categories = sorted(
        {category.strip() for category in categories if category and category.strip()},
        key=str.casefold,
    )
    return {'book_categories': categories}
