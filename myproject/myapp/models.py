# myapp/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.db.models import F, Sum, Case, When, IntegerField



class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    We keep your existing fields and add custom permissions via Meta.
    
    AbstractUser already gives us: username, email, password (hashed!),
    is_staff, is_active, groups, user_permissions, etc.
    """
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'French'),
        ('ar', 'Arabic'),
    ]

    shop_name = models.CharField(max_length=100, blank=True)
    language  = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='en'
    )
    history = HistoricalRecords() 

    # Note: email and password are inherited from AbstractUser.
    # AbstractUser hashes passwords automatically — no more hashlib needed!

    class Meta:
        # ── Custom Permissions ──────────────────────────────────────────
        # Format: ('codename', 'Human-readable description')
        # Access in code as: user.has_perm('myapp.can_view_analytics')
        permissions = [
            ('can_view_analytics',  'Can view the analytics dashboard'),
            ('can_export_users',    'Can export the users list'),
            ('can_manage_settings', 'Can change application settings'),
            ('can_publish_post',    'Can publish posts/announcements'),
        ]

    def __str__(self):
        return self.shop_name or self.username
    
class Brand(models.Model):
    nom         = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug        = models.SlugField(unique=True)
    history     = HistoricalRecords()
 
    def __str__(self):
        return self.nom
 
    class Meta:
        ordering = ['nom']
    
class Category(models.Model):
    brand       = models.ForeignKey(
                      'Brand',
                      on_delete=models.SET_NULL,
                      null=True,
                      blank=True,
                      related_name='categories'
                  )
    nom         = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug        = models.SlugField(unique=True)
    history     = HistoricalRecords()
 
    def __str__(self):
        return self.nom
 
    class Meta:
        ordering = ['nom']

class SubCategory(models.Model):
    category    = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    nom         = models.CharField(max_length=100)   # ← was max_lenth
    description = models.TextField(blank=True)
    slug        = models.SlugField(unique=True)
    history     = HistoricalRecords()

    def __str__(self):
        return f"{self.category.nom} → {self.nom}"


class Unite(models.Model):
    name   = models.CharField(max_length=100)
    iduser = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='unites'
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
    
     
class Local(models.Model):
    name    = models.CharField(max_length=100)
    iduser  = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='locals'
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Rayon(models.Model):
    name   = models.CharField(max_length=100)
    local  = models.ForeignKey(
        Local,
        on_delete=models.CASCADE,
        related_name='rayons'
    )
    iduser = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rayons'
    )
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.local.name} → {self.name}"

    class Meta:
        ordering = ['local', 'name']

class Fournisseur(models.Model):
    name    = models.CharField(max_length=100)
    phone   = models.CharField(max_length=20, blank=True)
    email   = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    iduser  = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fournisseurs'
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
class Product(models.Model):
    name = models.CharField(max_length=200)

    # ADDED: This allows the user to select the Local first
    local = models.ForeignKey(
        Local,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    # UPDATED: This will be filtered based on the 'local' selection above
    location_rayon = models.ForeignKey(
        Rayon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    unit = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    supplier = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')

    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    price_achat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_vente = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.slug:
            # Tip: Adding a unique ID to slug prevents errors if two products have the same name
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def stock_quantity(self):
        """
        Computed on the fly from the Stock ledger (sum of 'in' movements
        minus sum of 'out' movements). Not stored on Product itself —
        this keeps stock as a single source of truth in the Stock table.

        NOTE: for single-object lookups only (e.g. stock_history_ajax).
        When listing many products (e.g. stock_list), annotate the
        queryset instead to avoid N+1 queries — see the view.
        """
        agg = self.stocks.aggregate(
            total_in=models.Sum('quantity', filter=models.Q(movement_type='in')),
            total_out=models.Sum('quantity', filter=models.Q(movement_type='out')),
        )
        return (agg['total_in'] or 0) - (agg['total_out'] or 0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']



# ── Soft delete support (Django has no built-in equivalent) ────────────
class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(deleted_at=timezone.now())

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # Default manager hides soft-deleted rows, like Laravel's global scope
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()      # default: excludes deleted
    all_objects = models.Manager()     # explicit: includes deleted

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


# ── Achat (purchase header) ─────────────────────────────────────────────
class Achat(SoftDeleteModel):
    # No "Validation"/"Refus" gate — purchase is confirmed the moment it's
    # created. Status here only tracks physical delivery progress.
    STATUS_CHOICES = [
        ('creation', 'Création'),
        ('livraison', 'Livraison'),
        ('reception', 'Réception'),
    ]

    total       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='creation')
    fournisseur = models.ForeignKey(
        'Fournisseur', on_delete=models.CASCADE, related_name='achats'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achats'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Achat #{self.pk} - {self.fournisseur.name} ({self.total} DH)"


# ── LigneAchat (line items of a confirmed Achat) ────────────────────────
class LigneAchat(SoftDeleteModel):
    achat   = models.ForeignKey(Achat, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='lignes_achat')
    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lignes_achat'
    )
    qte = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.qte} x {self.produit.name} (Achat #{self.achat_id})"


# ── TempAchat (cart, before the purchase is confirmed) ──────────────────
class TempAchat(models.Model):
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='temp_achats'
    )
    produit     = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='temp_achats')
    fournisseur = models.ForeignKey(
        'Fournisseur', on_delete=models.CASCADE, related_name='temp_achats',
        null=True, blank=True
    )
    qte = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # No soft delete here — this is a scratchpad, not real business data.

    def __str__(self):
        return f"[cart] {self.qte} x {self.produit.name} ({self.user})"
class Stock(models.Model):
    MOVEMENT_TYPES = [
        ('in', 'Entrée'),   # stock increase (e.g. Achat delivered)
        ('out', 'Sortie'),  # stock decrease (e.g. Vente confirmed)
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    quantity = models.PositiveIntegerField()
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES)
    date = models.DateTimeField(auto_now_add=True)

    # Traceability: where did this movement come from?
    ligne_achat = models.ForeignKey(
        LigneAchat,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stock_movements'
    )
    ligne_vente = models.ForeignKey(          
        'LigneVente',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stock_movements'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    history = HistoricalRecords()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        sign = '+' if self.movement_type == 'in' else '-'
        return f"{sign}{self.quantity} {self.product.name} ({self.date:%Y-%m-%d})"
# ============================================================
# myapp/models.py — APPEND these classes AFTER LigneAchat / TempAchat
# and BEFORE `class Stock` (Stock needs LigneVente to exist).
# ============================================================

# ── Vente (sale header) ─────────────────────────────────────
class Vente(SoftDeleteModel):
    # creation  = sale submitted, stock NOT touched
    # validation = admin validated, stock decreased (once)
    STATUS_CHOICES = [
        ('creation', 'Création'),
        ('validation', 'Validation'),
    ]

    total  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='creation')
    user   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ventes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_validate_vente', 'Can validate a vente (decreases stock)'),
        ]

    def __str__(self):
        return f"Vente #{self.pk} ({self.total} DH)"


# ── LigneVente (line items) ─────────────────────────────────
class LigneVente(SoftDeleteModel):
    vente   = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='lignes_vente')
    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lignes_vente'
    )
    qte = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.qte} x {self.produit.name} (Vente #{self.vente_id})"


# ── TempVente (cart, before the sale is saved) ──────────────
class TempVente(models.Model):
    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='temp_ventes'
    )
    produit = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='temp_ventes')
    qte = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[cart vente] {self.qte} x {self.produit.name} ({self.user})"


# ============================================================
# In class Stock, ADD this field right after `ligne_achat`:
# ============================================================
#     ligne_vente = models.ForeignKey(
#         LigneVente,
#         on_delete=models.SET_NULL,
#         null=True, blank=True,
#         related_name='stock_movements'
#     )