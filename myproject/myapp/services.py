# myapp/services.py

from django.db import transaction
from django.db.models import F

from .models import TempAchat, Achat, LigneAchat, Stock


@transaction.atomic
def finalize_achat(user, fournisseur):
    """
    Converts all TempAchat rows for this user + fournisseur into a real
    Achat + LigneAchat set, updates Stock, then clears the cart.
    """
    temp_items = TempAchat.objects.select_for_update().filter(
        user=user, fournisseur=fournisseur
    )

    if not temp_items.exists():
        raise ValueError("Panier vide pour ce fournisseur.")

    total = sum(
        item.qte * item.produit.price_achat for item in temp_items
    )

    achat = Achat.objects.create(
        total=total,
        fournisseur=fournisseur,
        user=user,
    )

    for item in temp_items:
        LigneAchat.objects.create(
            achat=achat,
            produit=item.produit,
            user=user,
            qte=item.qte,
        )

        stock, _ = Stock.objects.select_for_update().get_or_create(
            product=item.produit, defaults={'quantity': 0}
        )
        stock.quantity = F('quantity') + item.qte
        stock.save()

    temp_items.delete()
    return achat