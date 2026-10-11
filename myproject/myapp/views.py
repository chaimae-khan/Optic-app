from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import User, Category, SubCategory,Unite, Brand ,Local, Rayon ,Fournisseur, Product,TempAchat, Achat, LigneAchat ,Vente,TempVente,LigneVente
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required, user_passes_test
from easyaudit.models import LoginEvent
import logging
from django.http import JsonResponse
from django.utils.text import slugify
from django.db import transaction
from django.db.models import F, Sum, Case, When, IntegerField
from .models import Stock
from django.db.models.functions import Coalesce

logger = logging.getLogger(__name__)


# ============================================
# HELPERS
# ============================================

def can_manage_roles(user):
    return user.is_active and (
        user.is_superuser or
        user.has_perm('auth.can_manage_roles')
    )


# ============================================
# AUDIT LOG
# ============================================


@login_required
def audit_log(request):
    event_type = request.GET.get('type', 'crud')

    category_history    = Category.history.select_related('history_user').order_by('-history_date')[:100]
    subcategory_history = SubCategory.history.select_related('history_user').order_by('-history_date')[:100]
    user_history        = User.history.select_related('history_user').order_by('-history_date')[:100]
    unite_history       = Unite.history.select_related('history_user').order_by('-history_date')[:100]  
    brand_history       = Brand.history.select_related('history_user').order_by('-history_date')[:100]
    local_history       = Local.history.select_related('history_user').order_by('-history_date')[:100]
    rayon_history       = Rayon.history.select_related('history_user').order_by('-history_date')[:100]
    fournisseur_history = Fournisseur.history.select_related('history_user').order_by('-history_date')[:100]






    crud_events = []
    for record in list(category_history) + list(subcategory_history) + list(user_history) + list(unite_history) + list(brand_history) + list(local_history) + list(rayon_history) + list(fournisseur_history):
        diff = {}
        if record.history_type == '~':
            prev = record.prev_record
            if prev:
                delta = prev.diff_against(record)  # old.diff_against(new) → correct direction
                for change in delta.changes:
                    diff[change.field] = {
                        "old": change.old if change.old not in (None, '') else '—',
                        "new": change.new if change.new not in (None, '') else '—',
                    }

        crud_events.append({
            "datetime":    record.history_date,
            "user":        record.history_user,
            "action":      record.history_type,
            "model":       record.instance.__class__.__name__,  
            "object_repr": str(record.instance),
            "diff":        diff,
        })

    crud_events.sort(key=lambda x: x["datetime"], reverse=True)

    login_events = LoginEvent.objects.select_related('user').order_by('-datetime')[:200]

    return render(request, 'audit_log.html', {
        'crud_events':  crud_events,
        'login_events': login_events,
        'event_type':   event_type,
        'create_count': sum(1 for e in crud_events if e['action'] == '+'),
        'update_count': sum(1 for e in crud_events if e['action'] == '~'),
        'delete_count': sum(1 for e in crud_events if e['action'] == '-'),
        'login_count':  login_events.count(),
        'crud_count':   len(crud_events),
    })

    crud_events.sort(key=lambda x: x["datetime"], reverse=True)

    login_events = LoginEvent.objects.select_related('user').order_by('-datetime')[:200]

    return render(request, 'audit_log.html', {
        'crud_events':  crud_events,
        'login_events': login_events,
        'event_type':   event_type,
        'create_count': sum(1 for e in crud_events if e['action'] == '+'),
        'update_count': sum(1 for e in crud_events if e['action'] == '~'),
        'delete_count': sum(1 for e in crud_events if e['action'] == '-'),
        'login_count':  login_events.count(),
        'crud_count':   len(crud_events),
    })

# ============================================
# FOURNISSEUR — List
# ============================================

@login_required
def fournisseur_list(request):
    fournisseurs = Fournisseur.objects.select_related('iduser').all()
    return render(request, 'fournisseur.html', {
        'fournisseurs': fournisseurs,
    })


# ============================================
# FOURNISSEUR — Create
# ============================================

@login_required
def fournisseur_create(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        phone   = request.POST.get('phone', '').strip()
        email   = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        if not name:
            messages.error(request, 'Fournisseur name cannot be empty.')
            return redirect('fournisseur_list')

        Fournisseur.objects.create(
            name=name,
            phone=phone,
            email=email,
            address=address,
            iduser=request.user,
        )
        messages.success(request, f'Fournisseur "{name}" created successfully.')

    return redirect('fournisseur_list')


# ============================================
# FOURNISSEUR — Update
# ============================================

@login_required
def fournisseur_update(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)

    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        phone   = request.POST.get('phone', '').strip()
        email   = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        if not name:
            messages.error(request, 'Fournisseur name cannot be empty.')
            return redirect('fournisseur_list')

        fournisseur.name    = name
        fournisseur.phone   = phone
        fournisseur.email   = email
        fournisseur.address = address
        fournisseur.save()
        messages.success(request, f'Fournisseur "{fournisseur.name}" updated successfully.')

    return redirect('fournisseur_list')


# ============================================
# FOURNISSEUR — Delete
# ============================================

@login_required
def fournisseur_delete(request, pk):
    if request.method == 'POST':
        fournisseur = get_object_or_404(Fournisseur, pk=pk)
        name = fournisseur.name
        fournisseur.delete()
        messages.success(request, f'Fournisseur "{name}" deleted successfully.')
    return redirect('fournisseur_list')

# ============================================
# RAYON — List
# ============================================

@login_required
def rayon_list(request):
    rayons  = Rayon.objects.select_related('local', 'iduser').all()
    locals_ = Local.objects.all().order_by('name')
    has_locals = locals_.exists()
    if not has_locals:
        messages.warning(request, 'No locals found. You must create a Local before adding a Rayon.')
    return render(request, 'rayon.html', {
        'rayons':     rayons,
        'locals':     locals_,
        'has_locals': has_locals,
    })


# ============================================
# RAYON — Create
# ============================================

@login_required
def rayon_create(request):
    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        local_id = request.POST.get('local', '').strip()

        if not name:
            messages.error(request, 'Rayon name cannot be empty.')
            return redirect('rayon_list')

        if not local_id:
            messages.error(request, 'Please select a local.')
            return redirect('rayon_list')

        local = get_object_or_404(Local, pk=local_id)
        Rayon.objects.create(name=name, local=local, iduser=request.user)
        messages.success(request, f'Rayon "{name}" created successfully.')

    return redirect('rayon_list')


# ============================================
# RAYON — Update
# ============================================

@login_required
def rayon_update(request, pk):
    rayon = get_object_or_404(Rayon, pk=pk)

    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        local_id = request.POST.get('local', '').strip()

        if not name:
            messages.error(request, 'Rayon name cannot be empty.')
            return redirect('rayon_list')

        if not local_id:
            messages.error(request, 'Please select a local.')
            return redirect('rayon_list')

        rayon.name  = name
        rayon.local = get_object_or_404(Local, pk=local_id)
        rayon.save()
        messages.success(request, f'Rayon "{rayon.name}" updated successfully.')

    return redirect('rayon_list')


# ============================================
# RAYON — Delete
# ============================================

@login_required
def rayon_delete(request, pk):
    if request.method == 'POST':
        rayon = get_object_or_404(Rayon, pk=pk)
        name  = rayon.name
        rayon.delete()
        messages.success(request, f'Rayon "{name}" deleted successfully.')
    return redirect('rayon_list')
# ============================================
# CATEGORY — List
# ============================================

@login_required
def category_list(request):
    categories = Category.objects.select_related('brand').all().order_by('nom')
    brands     = Brand.objects.all().order_by('nom')
    return render(request, 'category.html', {
        'categories': categories,
        'brands':     brands,
    })


# ============================================
# CATEGORY — Create
# ============================================

@login_required
def category_create(request):
    if request.method == 'POST':
        nom         = request.POST.get('nom', '').strip()
        description = request.POST.get('description', '').strip()
        slug        = request.POST.get('slug', '').strip()
        brand_id    = request.POST.get('brand', '').strip()

        if not nom:
            messages.error(request, 'Category name cannot be empty.')
            return redirect('category_list')

        if Category.objects.filter(slug=slug).exists():
            messages.error(request, f'Slug "{slug}" already exists.')
            return redirect('category_list')

        brand = Brand.objects.filter(pk=brand_id).first() if brand_id else None

        Category.objects.create(nom=nom, description=description, slug=slug, brand=brand)
        messages.success(request, f'Category "{nom}" created successfully.')

    return redirect('category_list')


# ============================================
# CATEGORY — Update
# ============================================

@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        brand_id = request.POST.get('brand', '').strip()
        new_data = {
            'nom':         request.POST.get('nom', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'slug':        request.POST.get('slug', '').strip(),
        }

        if not new_data['nom']:
            messages.error(request, 'Category name cannot be empty.')
            return redirect('category_list')

        if Category.objects.filter(slug=new_data['slug']).exclude(pk=pk).exists():
            messages.error(request, f'Slug "{new_data["slug"]}" already used by another category.')
            return redirect('category_list')

        for field, value in new_data.items():
            setattr(category, field, value)

        category.brand = Brand.objects.filter(pk=brand_id).first() if brand_id else None
        category.save()

        messages.success(request, f'Category "{category.nom}" updated successfully.')

    return redirect('category_list')

# ============================================
# CATEGORY — Delete
# ============================================

@login_required
def category_delete(request, pk):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=pk)
        nom = category.nom
        category.delete()
        messages.success(request, f'Category "{nom}" deleted successfully.')
    return redirect('category_list')


# ============================================
# SUBCATEGORY — List
# ============================================

@login_required
def subcategory_list(request):
    subcategories = SubCategory.objects.select_related('category').order_by('nom')
    categories    = Category.objects.all().order_by('nom')

    if not categories.exists():
        messages.warning(request, 'No categories found. You must create a Category before adding a Subcategory.')

    return render(request, 'subcategory.html', {
        'subcategories':  subcategories,
        'categories':     categories,
        'has_categories': categories.exists(),
    })


# ============================================
# SUBCATEGORY — Create
# ============================================

@login_required
def subcategory_create(request):
    if request.method == 'POST':
        nom         = request.POST.get('nom', '').strip()
        description = request.POST.get('description', '').strip()
        slug        = request.POST.get('slug', '').strip()
        category_id = request.POST.get('category', '').strip()

        if not nom:
            messages.error(request, 'Subcategory name cannot be empty.')
            return redirect('subcategory_list')

        if not category_id:
            messages.error(request, 'Please select a parent category.')
            return redirect('subcategory_list')

        if SubCategory.objects.filter(slug=slug).exists():
            messages.error(request, f'Slug "{slug}" already exists.')
            return redirect('subcategory_list')

        category = get_object_or_404(Category, pk=category_id)
        SubCategory.objects.create(
            nom=nom,
            description=description,
            slug=slug,
            category=category,
        )
        messages.success(request, f'Subcategory "{nom}" created successfully.')

    return redirect('subcategory_list')


# ============================================
# SUBCATEGORY — Update
# ============================================

@login_required
def subcategory_update(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)

    if request.method == 'POST':
        category_id = request.POST.get('category', '').strip()
        new_data = {
            'nom':         request.POST.get('nom', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'slug':        request.POST.get('slug', '').strip(),
        }

        if not new_data['nom']:
            messages.error(request, 'Subcategory name cannot be empty.')
            return redirect('subcategory_list')

        if SubCategory.objects.filter(slug=new_data['slug']).exclude(pk=pk).exists():
            messages.error(request, f'Slug "{new_data["slug"]}" already used by another subcategory.')
            return redirect('subcategory_list')

        for field, value in new_data.items():
            setattr(subcategory, field, value)
        subcategory.category = get_object_or_404(Category, pk=category_id)
        subcategory.save()

        messages.success(request, f'Subcategory "{subcategory.nom}" updated successfully.')

    return redirect('subcategory_list')


# ============================================
# SUBCATEGORY — Delete
# ============================================

@login_required
def subcategory_delete(request, pk):
    if request.method == 'POST':
        subcategory = get_object_or_404(SubCategory, pk=pk)
        nom = subcategory.nom
        subcategory.delete()
        messages.success(request, f'Subcategory "{nom}" deleted successfully.')
    return redirect('subcategory_list')


# ============================================
# PERMISSIONS MANAGER — List
# ============================================

@login_required
@user_passes_test(can_manage_roles, login_url='login')
def permissions_manager(request):
    groups = Group.objects.prefetch_related('permissions').all()
    return render(request, 'permissions_manager.html', {'groups': groups})


# ============================================
# PERMISSIONS MANAGER — Edit Group
# ============================================

@login_required
@user_passes_test(can_manage_roles, login_url='login')
def edit_group_permissions(request, group_id):
    group = get_object_or_404(
        Group.objects.prefetch_related('permissions'),
        id=group_id,
    )

    all_permissions = (
        Permission.objects
        .select_related('content_type')
        .order_by('content_type__app_label', 'content_type__model', 'codename')
    )

    current_permission_ids = set(group.permissions.values_list('id', flat=True))

    if request.method == 'POST':
        selected_ids = request.POST.getlist('permissions')
        group.permissions.set(selected_ids)
        messages.success(request, f'Permissions for "{group.name}" updated successfully.')
        return redirect('permissions_manager')

    permissions_by_app = {}
    for perm in all_permissions:
        app = perm.content_type.app_label.replace('_', ' ').title()
        permissions_by_app.setdefault(app, []).append(perm)

    return render(request, 'permissions_manager.html', {
        'group':                  group,
        'permissions_by_app':     permissions_by_app,
        'current_permission_ids': current_permission_ids,
        'groups':                 Group.objects.prefetch_related('permissions').all(),
    })


# ============================================
# CREATE GROUP
# ============================================

@login_required
@user_passes_test(can_manage_roles, login_url='login')
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'Role name cannot be empty.')
            return redirect('permissions_manager')

        if Group.objects.filter(name=name).exists():
            messages.error(request, f'Role "{name}" already exists.')
            return redirect('permissions_manager')

        Group.objects.create(name=name)
        messages.success(request, f'Role "{name}" created successfully.')

    return redirect('permissions_manager')


# ============================================
# DELETE GROUP
# ============================================

@login_required
@user_passes_test(can_manage_roles, login_url='login')
def delete_group(request, group_id):
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        name = group.name
        group.delete()
        messages.success(request, f'Role "{name}" deleted.')
    return redirect('permissions_manager')


# ============================================
# AUTH — Login / Logout / Register
# ============================================

def login(request):
    if request.user.is_authenticated:
        return redirect('index')

    next_url = request.GET.get('next')

    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next')

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Welcome back!')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
                return redirect(next_url)
            return redirect('index')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'login.html', {'next': next_url})


def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


def register(request):
    if request.method == 'POST':
        shop_name = request.POST.get('shop_name')
        email     = request.POST.get('email')
        password  = request.POST.get('password')
        language  = request.POST.get('language', 'en')
        group_id  = request.POST.get('group')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return redirect('users')

        user = User.objects.create_user(
            username=shop_name,
            email=email,
            password=password,
        )
        user.shop_name = shop_name
        user.language  = language
        user.save()

        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
            except Group.DoesNotExist:
                pass

        messages.success(request, f'Account for "{shop_name}" created successfully.')
        return redirect('users')

    return render(request, 'register.html')


# ============================================
# USERS
# ============================================

def users_list(request):
    users  = User.objects.all()
    groups = Group.objects.all().order_by('name')
    return render(request, 'users.html', {'users': users, 'groups': groups})


def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.shop_name = request.POST.get('shop_name')
        user.email     = request.POST.get('email')
        user.language  = request.POST.get('language', 'en')

        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)

        user.save()
        messages.success(request, 'User updated successfully.')

    return redirect('users')

# ============================================
# UNITE — List
# ============================================

@login_required
def unite_list(request):
    unites     = Unite.objects.select_related('iduser').all()
    categories = Category.objects.exists()          # only a boolean check — cheap query
    return render(request, 'unite.html', {
        'unites':          unites,
        'has_categories':  categories,
    })


# ============================================
# UNITE — Create
# ============================================

@login_required
def unite_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'Unite name cannot be empty.')
            return redirect('unite_list')

        Unite.objects.create(name=name, iduser=request.user)
        messages.success(request, f'Unite "{name}" created successfully.')

    return redirect('unite_list')


# ============================================
# UNITE — Update
# ============================================

@login_required
def unite_update(request, pk):
    unite = get_object_or_404(Unite, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'Unite name cannot be empty.')
            return redirect('unite_list')

        unite.name = name
        unite.save()
        messages.success(request, f'Unite "{unite.name}" updated successfully.')

    return redirect('unite_list')


# ============================================
# UNITE — Delete
# ============================================

@login_required
def unite_delete(request, pk):
    if request.method == 'POST':
        unite = get_object_or_404(Unite, pk=pk)
        name  = unite.name
        unite.delete()
        messages.success(request, f'Unite "{name}" deleted successfully.')
    return redirect('unite_list')
# ============================================
# MISC PAGES
# ============================================

LOW_STOCK_THRESHOLD = 5


@login_required
def index(request):
    low_stock_products = list(
        Product.objects.filter(is_active=True)
        .select_related('category')
        .annotate(
            computed_stock=Coalesce(
                Sum(
                    Case(
                        When(stocks__movement_type='in', then=F('stocks__quantity')),
                        When(stocks__movement_type='out', then=F('stocks__quantity') * -1),
                        default=0,
                        output_field=IntegerField(),
                    )
                ),
                0,
            )
        )
        .filter(computed_stock__lte=LOW_STOCK_THRESHOLD)
        .order_by('computed_stock', 'name')
    )

    return render(request, 'index.html', {
        'total_users':           User.objects.count(),
        'total_achats':          Achat.objects.exclude(status='livraison').count(),
        'unvalidated_ventes':    Vente.objects.filter(status='creation').count(),
        'low_stock_products':    low_stock_products,
        'out_of_stock_count':    sum(1 for p in low_stock_products if p.computed_stock == 0),
        'low_stock_count':       sum(1 for p in low_stock_products if p.computed_stock > 0),
        'low_stock_threshold':   LOW_STOCK_THRESHOLD,
    })

def about(request):
    return render(request, 'about-templatemo.html')

def analytics(request):
    return render(request, 'analytics.html')

def settings(request):
    return render(request, 'settings.html')

def users(request):
    return render(request, 'users.html')

# ============================================
# BRAND — List
# ============================================
 
@login_required
def brand_list(request):
    brands = Brand.objects.all().order_by('nom')
    return render(request, 'brand.html', {'brands': brands})
 
 
# ============================================
# BRAND — Create
# ============================================
 
@login_required
def brand_create(request):
    if request.method == 'POST':
        nom         = request.POST.get('nom', '').strip()
        description = request.POST.get('description', '').strip()
        slug        = request.POST.get('slug', '').strip()
 
        if not nom:
            messages.error(request, 'Brand name cannot be empty.')
            return redirect('brand_list')
 
        if Brand.objects.filter(slug=slug).exists():
            messages.error(request, f'Slug "{slug}" already exists.')
            return redirect('brand_list')
 
        Brand.objects.create(nom=nom, description=description, slug=slug)
        messages.success(request, f'Brand "{nom}" created successfully.')
 
    return redirect('brand_list')
 
 
# ============================================
# BRAND — Update
# ============================================
 
@login_required
def brand_update(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
 
    if request.method == 'POST':
        new_data = {
            'nom':         request.POST.get('nom', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'slug':        request.POST.get('slug', '').strip(),
        }
 
        if not new_data['nom']:
            messages.error(request, 'Brand name cannot be empty.')
            return redirect('brand_list')
 
        if Brand.objects.filter(slug=new_data['slug']).exclude(pk=pk).exists():
            messages.error(request, f'Slug "{new_data["slug"]}" already used by another brand.')
            return redirect('brand_list')
 
        for field, value in new_data.items():
            setattr(brand, field, value)
        brand.save()
 
        messages.success(request, f'Brand "{brand.nom}" updated successfully.')
 
    return redirect('brand_list')
 
 
# ============================================
# BRAND — Delete
# ============================================
 
@login_required
def brand_delete(request, pk):
    if request.method == 'POST':
        brand = get_object_or_404(Brand, pk=pk)
        nom = brand.nom
        brand.delete()
        messages.success(request, f'Brand "{nom}" deleted successfully.')
    
    return redirect('brand_list')

# ============================================
# LOCAL — List
# ============================================

@login_required
def local_list(request):
    locals_ = Local.objects.select_related('iduser').all()
    return render(request, 'local.html', {
        'locals': locals_,
    })


# ============================================
# LOCAL — Create
# ============================================

@login_required
def local_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'Local name cannot be empty.')
            return redirect('local_list')

        Local.objects.create(name=name, iduser=request.user)
        messages.success(request, f'Local "{name}" created successfully.')

    return redirect('local_list')


# ============================================
# LOCAL — Update
# ============================================

@login_required
def local_update(request, pk):
    local = get_object_or_404(Local, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'Local name cannot be empty.')
            return redirect('local_list')

        local.name = name
        local.save()
        messages.success(request, f'Local "{local.name}" updated successfully.')

    return redirect('local_list')


# ============================================
# LOCAL — Delete
# ============================================

@login_required
def local_delete(request, pk):
    if request.method == 'POST':
        local = get_object_or_404(Local, pk=pk)
        name  = local.name
        local.delete()
        messages.success(request, f'Local "{name}" deleted successfully.')
    return redirect('local_list')
# ============================================
# PRODUCT — List
# ============================================


@login_required
def product_list(request):
    # 1. Fetch only this user's products
    # Note: 'user' is removed from select_related because we already have request.user
    products = Product.objects.filter(user=request.user).select_related(
        'brand', 'category', 'subcategory', 'unit', 'location_rayon', 'supplier', 'local'
    ).order_by('name')

    # 2. Get the dictionary from your helper
    ctx = _product_form_context(request)
    
    # 3. Add the products to that dictionary
    ctx['products'] = products

    # 4. Render (Make sure the template name 'product.html' is correct)
    return render(request, 'product.html', ctx)
def _product_form_context(request):
    return {
        'brands'        : Brand.objects.all(),
        'categories'    : Category.objects.all(),
        'subcategories' : SubCategory.objects.all(),
        'unites'        : Unite.objects.all(),
        'locals'        : Local.objects.all(),  
        'rayons'        : Rayon.objects.all(),
        'fournisseurs'  : Fournisseur.objects.all(),
    }

# ============================================
# PRODUCT — Create
# ============================================
@login_required
def product_create(request):
    if request.method != 'POST':
        return redirect('product_list')

    def fk_or_none(model, pk):
        try:
            return model.objects.get(pk=int(pk)) if pk else None
        except (model.DoesNotExist, ValueError):
            return None

    name    = request.POST.get('name', '').strip()
    slug_val = request.POST.get('slug', '').strip() or slugify(name)

    # Make slug unique
    base, counter = slug_val, 1
    while Product.objects.filter(slug=slug_val).exists():
        slug_val = f"{base}-{counter}"
        counter += 1

    Product.objects.create(
        user           = request.user,
        name           = name,
        slug           = slug_val,
        description    = request.POST.get('description', '').strip(),
        price_achat    = request.POST.get('price_achat') or 0,
        price_vente    = request.POST.get('price_vente') or 0,
        brand          = fk_or_none(Brand,       request.POST.get('brand')),
        category       = fk_or_none(Category,    request.POST.get('category')),
        subcategory    = fk_or_none(SubCategory, request.POST.get('subcategory')),
        unit           = fk_or_none(Unite,       request.POST.get('unit')),
        location_rayon = fk_or_none(Rayon,       request.POST.get('location_rayon')),
        supplier       = fk_or_none(Fournisseur, request.POST.get('supplier')),
    )
    messages.success(request, f'Product "{name}" created successfully.')
    return redirect('product_list')

# ============================================
# PRODUCT — Update
# ============================================

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)

    if request.method != 'POST':
        return redirect('product_list')

    def fk_or_none(model, val):
        try:
            return model.objects.get(pk=int(val)) if val else None
        except (model.DoesNotExist, ValueError):
            return None

    product.name           = request.POST.get('name', '').strip()
    product.slug           = request.POST.get('slug', '').strip()
    product.description    = request.POST.get('description', '').strip()
    product.price_achat    = request.POST.get('price_achat') or 0
    product.price_vente    = request.POST.get('price_vente') or 0
    product.brand          = fk_or_none(Brand,       request.POST.get('brand'))
    product.category       = fk_or_none(Category,    request.POST.get('category'))
    product.subcategory    = fk_or_none(SubCategory, request.POST.get('subcategory'))
    product.unit           = fk_or_none(Unite,       request.POST.get('unit'))
    product.location_rayon = fk_or_none(Rayon,       request.POST.get('location_rayon'))
    product.supplier       = fk_or_none(Fournisseur, request.POST.get('supplier'))
    product.save()

    messages.success(request, f'Product "{product.name}" updated.')
    return redirect('product_list')


# ============================================
# PRODUCT — Delete
# ============================================

@login_required
def product_delete(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" deleted successfully.')
    return redirect('product_list')

@login_required
def rayons_by_local(request):
    local_id = request.GET.get('local_id')
    if not local_id:
        return JsonResponse({'rayons': []})
    rayons = Rayon.objects.filter(local_id=local_id).values('pk', 'name')
    return JsonResponse({'rayons': list(rayons)})


# ============================================
# ACHAT — Page principale (search + cart UI)
# ============================================

@login_required
def achat_create(request):
    fournisseurs = Fournisseur.objects.all()
    achats = Achat.objects.select_related('fournisseur', 'user').order_by('-created_at')
    return render(request, 'achat.html', {
        'fournisseurs': fournisseurs,
        'achats': achats,
    })

# ============================================
# ACHAT — Product search (AJAX, for the search box)
# ============================================

@login_required
def achat_product_search(request):
    q = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True)
    if q:
        products = products.filter(name__icontains=q)

    data = list(products.values('id', 'name', 'price_achat')[:20])
    return JsonResponse({'products': data})


# ============================================
# ACHAT — Add product to cart (TempAchat)
# ============================================

@login_required
def achat_temp_add(request):
    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})
 
    produit_id     = request.POST.get('produit_id')
    fournisseur_id = request.POST.get('fournisseur_id')
 
    try:
        qte = int(request.POST.get('qte', 1))
    except (TypeError, ValueError):
        qte = 1
    if qte < 1:
        qte = 1
 
    produit = get_object_or_404(Product, pk=produit_id)
    fournisseur = get_object_or_404(Fournisseur, pk=fournisseur_id)
 
    temp, created = TempAchat.objects.get_or_create(
        user=request.user,
        produit=produit,
        fournisseur=fournisseur,
        defaults={'qte': qte},
    )
    if not created:
        temp.qte = F('qte') + qte
        temp.save()
 
    return JsonResponse({'status': 200, 'message': 'Produit ajouté au panier'})


# ============================================
# ACHAT — Get cart items for a fournisseur (for the modal)
# ============================================

@login_required
def achat_temp_list(request):
    fournisseur_id = request.GET.get('fournisseur_id')

    items = TempAchat.objects.filter(
        user=request.user, fournisseur_id=fournisseur_id
    ).select_related('produit')

    data = [{
        'id': item.id,
        'produit': item.produit.name,
        'qte': item.qte,
        'price_achat': str(item.produit.price_achat),
        'total': str(item.qte * item.produit.price_achat),
    } for item in items]

    total_general = sum(item.qte * item.produit.price_achat for item in items)

    return JsonResponse({'items': data, 'total': str(total_general)})


# ============================================
# ACHAT — Update quantity in cart
# ============================================

@login_required
def achat_temp_update_qte(request):
    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})
 
    temp_id = request.POST.get('id')
 
    try:
        qte = int(request.POST.get('qte'))
    except (TypeError, ValueError):
        return JsonResponse({'status': 400, 'message': 'Quantité invalide'})
 
    if qte < 1:
        return JsonResponse({'status': 400, 'message': 'La quantité doit être au moins 1'})
 
    temp = get_object_or_404(TempAchat, pk=temp_id, user=request.user)
    temp.qte = qte
    temp.save()
 
    return JsonResponse({'status': 200, 'message': 'Quantité mise à jour'})


# ============================================
# ACHAT — Remove one item from cart
# ============================================

@login_required
def achat_temp_delete(request):
    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})

    temp_id = request.POST.get('id')
    TempAchat.objects.filter(pk=temp_id, user=request.user).delete()

    return JsonResponse({'status': 200, 'message': 'Article supprimé'})


# ============================================
# ACHAT — Validate: cart → real Achat + LigneAchat
# ============================================

@login_required
def achat_validate(request):
    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})

    fournisseur_id = request.POST.get('fournisseur_id')
    fournisseur    = get_object_or_404(Fournisseur, pk=fournisseur_id)

    temp_items = TempAchat.objects.filter(
        user=request.user, fournisseur=fournisseur
    ).select_related('produit')

    if not temp_items.exists():
        return JsonResponse({'status': 400, 'message': 'Panier vide'})

    total = sum(item.qte * item.produit.price_achat for item in temp_items)

    with transaction.atomic():
        achat = Achat.objects.create(
            total=total,
            fournisseur=fournisseur,
            user=request.user,
        )

        for item in temp_items:
            LigneAchat.objects.create(
                achat=achat,
                produit=item.produit,
                user=request.user,
                qte=item.qte,
            )

        temp_items.delete()

    return JsonResponse({'status': 200, 'message': 'Achat validé avec succès', 'achat_id': achat.id})
@login_required
def achat_save_cart(request):
    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})

    fournisseur_id = request.POST.get('fournisseur_id')
    fournisseur    = get_object_or_404(Fournisseur, pk=fournisseur_id)

    temp_items = TempAchat.objects.filter(
        user=request.user, fournisseur=fournisseur
    ).select_related('produit')

    if not temp_items.exists():
        return JsonResponse({'status': 400, 'message': 'Panier vide'})

    total = sum(item.qte * item.produit.price_achat for item in temp_items)

    with transaction.atomic():
        achat = Achat.objects.create(total=total, fournisseur=fournisseur, user=request.user)
        for item in temp_items:
            LigneAchat.objects.create(achat=achat, produit=item.produit, user=request.user, qte=item.qte)
        temp_items.delete()

    return JsonResponse({'status': 200, 'message': 'Achat enregistré avec succès', 'achat_id': achat.id})
@login_required
def achat_advance_status(request, pk):

    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})

    achat = get_object_or_404(Achat, pk=pk)

    if achat.status == 'livraison':
        return JsonResponse({'status': 400, 'message': "Cet achat est déjà livré, son statut ne peut plus être modifié."})

    status_field = Achat._meta.get_field('status')
    choices = [choice_value for choice_value, _label in status_field.choices]

    try:
        current_index = choices.index(achat.status)
    except ValueError:
        return JsonResponse({'status': 400, 'message': 'Statut actuel invalide'})

    if current_index + 1 >= len(choices):
        return JsonResponse({'status': 400, 'message': "Cet achat est déjà au dernier statut"})

    next_status = choices[current_index + 1]

    if next_status == 'livraison':
        with transaction.atomic():
            for ligne in achat.lignes.select_related('produit'):
                Stock.objects.create(
                    product=ligne.produit,
                    quantity=ligne.qte,
                    movement_type='in',
                    ligne_achat=ligne,
                    user=request.user,
                )
            achat.status = next_status
            achat.save(update_fields=['status', 'updated_at'])
    else:
        achat.status = next_status
        achat.save(update_fields=['status'])

    return JsonResponse({
        'status': 200,
        'message': 'Statut mis à jour',
        'new_status': achat.status,
        'new_status_display': achat.get_status_display(),
        'is_last': (current_index + 2) >= len(choices),
    })
# ============================================
# ACHAT — Delete (from the main list)
# ============================================

@login_required
def achat_delete(request, pk):
    if request.method == 'POST':
        achat = get_object_or_404(Achat, pk=pk)
        if achat.status == 'livraison':
            messages.error(request, "Cet achat est déjà livré et ne peut plus être supprimé.")
            return redirect('achat_create')
        achat.delete()
        messages.success(request, 'Achat supprimé avec succès.')
    return redirect('achat_create')
# @login_required
# def achat_detail(request, pk):
#     achat = get_object_or_404(
#         Achat.objects.select_related('fournisseur', 'user'),
#         pk=pk
#     )
#     lignes = achat.lignes.select_related('produit').all()

#     return render(request, 'achat_detail.html', {
#         'achat': achat,
#         'lignes': lignes,
#     })
# ============================================
# STOCK — Current stock levels (one row per product)
# ============================================

@login_required
def stock_list(request):
    products = (
        Product.objects.filter(is_active=True)
        .select_related('brand', 'category')
        .annotate(
            computed_stock=Coalesce(
                Sum(
                    Case(
                        When(stocks__movement_type='in', then=F('stocks__quantity')),
                        When(stocks__movement_type='out', then=F('stocks__quantity') * -1),
                        default=0,
                        output_field=IntegerField(),
                    )
                ),
                0,
            )
        )
    )

    data = [{'product': p, 'quantity': p.computed_stock} for p in products]
    return render(request, 'stock.html', {'stock_data': data})


# ============================================
# STOCK — Movement history (ledger), optionally filtered by product
# ============================================

@login_required
def stock_history(request):
    product_id = request.GET.get('product_id')

    movements = Stock.objects.select_related('product', 'user', 'ligne_achat').order_by('-date')
    if product_id:
        movements = movements.filter(product_id=product_id)

    return render(request, 'stock_history.html', {'movements': movements})


# ============================================
# STOCK — Movement history for one product (AJAX, e.g. modal on stock_list)
# ============================================

@login_required
def stock_history_ajax(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    movements = Stock.objects.filter(product=product).select_related('user').order_by('-date')

    data = [{
        'quantity': m.quantity,
        'movement_type': m.get_movement_type_display(),
        'date': m.date.strftime('%Y-%m-%d %H:%M'),
        'user': str(m.user),
    } for m in movements]

    return JsonResponse({
        'product': product.name,
        'current_stock': product.stock_quantity,
        'movements': data,
    })
# ============================================================
# myapp/views.py
# 1) Change the models import line to also include the new models:
#    from .models import (User, Category, SubCategory, Unite, Brand, Local, Rayon,
#        Fournisseur, Product, TempAchat, Achat, LigneAchat,
#        TempVente, Vente, LigneVente)
# 2) APPEND everything below at the end of the file.
# ============================================================

# ============================================
# VENTE — helper
# ============================================

def can_validate_vente(user):
    return user.is_active and (
        user.is_superuser or
        user.has_perm('myapp.can_validate_vente')
    )


# ============================================
# VENTE — Page principale (search + cart UI)
# ============================================

@login_required
def vente_create(request):
    ventes = Vente.objects.select_related('user').order_by('-created_at')
    return render(request, 'vente.html', {
        'ventes': ventes,
        'can_validate': can_validate_vente(request.user),
    })


# ============================================
# VENTE — Product search (AJAX)
# ============================================

@login_required
def vente_product_search(request):
    q = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True)
    if q:
        products = products.filter(name__icontains=q)

    data = list(products.values('id', 'name', 'price_vente')[:20])
    return JsonResponse({'products': data})


# ============================================
# VENTE — Add product to cart (TempVente)
# ============================================

@login_required
def vente_temp_add(request):
    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})

    produit_id = request.POST.get('produit_id')

    try:
        qte = int(request.POST.get('qte', 1))
    except (TypeError, ValueError):
        qte = 1
    if qte < 1:
        qte = 1

    produit = get_object_or_404(Product, pk=produit_id)

    temp, created = TempVente.objects.get_or_create(
        user=request.user,
        produit=produit,
        defaults={'qte': qte},
    )
    if not created:
        temp.qte = F('qte') + qte
        temp.save()

    return JsonResponse({'status': 200, 'message': 'Produit ajouté au panier'})


# ============================================
# VENTE — Get cart items
# ============================================

@login_required
def vente_temp_list(request):
    items = TempVente.objects.filter(user=request.user).select_related('produit')

    data = [{
        'id': item.id,
        'produit': item.produit.name,
        'qte': item.qte,
        'price_vente': str(item.produit.price_vente),
        'total': str(item.qte * item.produit.price_vente),
    } for item in items]

    total_general = sum(item.qte * item.produit.price_vente for item in items)

    return JsonResponse({'items': data, 'total': str(total_general)})


# ============================================
# VENTE — Update quantity in cart
# ============================================

@login_required
def vente_temp_update_qte(request):
    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})

    temp_id = request.POST.get('id')

    try:
        qte = int(request.POST.get('qte'))
    except (TypeError, ValueError):
        return JsonResponse({'status': 400, 'message': 'Quantité invalide'})

    if qte < 1:
        return JsonResponse({'status': 400, 'message': 'La quantité doit être au moins 1'})

    temp = get_object_or_404(TempVente, pk=temp_id, user=request.user)
    temp.qte = qte
    temp.save()

    return JsonResponse({'status': 200, 'message': 'Quantité mise à jour'})


# ============================================
# VENTE — Remove one item from cart
# ============================================

@login_required
def vente_temp_delete(request):
    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})

    temp_id = request.POST.get('id')
    TempVente.objects.filter(pk=temp_id, user=request.user).delete()

    return JsonResponse({'status': 200, 'message': 'Article supprimé'})


# ============================================
# VENTE — Save: cart → Vente + LigneVente (stock NOT touched)
# ============================================

@login_required
def vente_save_cart(request):
    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})

    temp_items = TempVente.objects.filter(user=request.user).select_related('produit')

    if not temp_items.exists():
        return JsonResponse({'status': 400, 'message': 'Panier vide'})

    total = sum(item.qte * item.produit.price_vente for item in temp_items)

    with transaction.atomic():
        vente = Vente.objects.create(total=total, user=request.user)
        for item in temp_items:
            LigneVente.objects.create(vente=vente, produit=item.produit, user=request.user, qte=item.qte)
        temp_items.delete()

    return JsonResponse({'status': 200, 'message': 'Vente enregistrée avec succès', 'vente_id': vente.id})


# ============================================
# VENTE — Admin validation: decreases stock (once, all-or-nothing)
# ============================================

@login_required
def vente_validate(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Méthode invalide'})

    if not can_validate_vente(request.user):
        return JsonResponse({'status': 403, 'message': "Seul un administrateur peut valider une vente."})

    with transaction.atomic():
        # Lock the vente row so two simultaneous validations can't both pass the status check.
        vente = Vente.objects.select_for_update().filter(pk=pk).first()
        if vente is None:
            return JsonResponse({'status': 404, 'message': 'Vente introuvable'})

        if vente.status == 'validation':
            return JsonResponse({'status': 400, 'message': "Cette vente est déjà validée."})

        lignes = list(vente.lignes.select_related('produit'))
        if not lignes:
            return JsonResponse({'status': 400, 'message': 'Vente sans lignes'})

        # Total quantity needed per product (a product could appear on several lines).
        needed = {}
        for ligne in lignes:
            needed[ligne.produit_id] = needed.get(ligne.produit_id, 0) + ligne.qte

        # Lock products (ordered, to avoid deadlocks) and check stock BEFORE any write.
        products = Product.objects.select_for_update().filter(pk__in=needed.keys()).order_by('pk')
        shortages = []
        for p in products:
            available = p.stock_quantity
            if available < needed[p.pk]:
                shortages.append(f"{p.name} (disponible: {available}, demandé: {needed[p.pk]})")

        if shortages:
            return JsonResponse({
                'status': 400,
                'message': "Stock insuffisant : " + " ; ".join(shortages),
            })

        for ligne in lignes:
            Stock.objects.create(
                product=ligne.produit,
                quantity=ligne.qte,
                movement_type='out',
                ligne_vente=ligne,
                user=request.user,
            )
        vente.status = 'validation'
        vente.save(update_fields=['status', 'updated_at'])

    return JsonResponse({
        'status': 200,
        'message': 'Vente validée',
        'new_status': vente.status,
        'new_status_display': vente.get_status_display(),
    })


# ============================================
# VENTE — Delete (not allowed once validated)
# ============================================

@login_required
def vente_delete(request, pk):
    if request.method == 'POST':
        vente = get_object_or_404(Vente, pk=pk)
        if vente.status == 'validation':
            messages.error(request, "Cette vente est déjà validée et ne peut plus être supprimée.")
            return redirect('vente_create')
        vente.delete()
        messages.success(request, 'Vente supprimée avec succès.')
    return redirect('vente_create')
# ============================================
# VENTE — Details page (read-only)
# ============================================

@login_required
def vente_detail(request, pk):
    vente = get_object_or_404(Vente.objects.select_related('user'), pk=pk)

    lignes = list(
        vente.lignes.select_related('produit', 'produit__unit').order_by('pk')
    )

    # Current stock per product (single query, no N+1) — only useful while pending.
    product_ids = {l.produit_id for l in lignes}
    stock_map = {
        row['product_id']: row['total']
        for row in (
            Stock.objects.filter(product_id__in=product_ids)
            .values('product_id')
            .annotate(
                total=Coalesce(
                    Sum(
                        Case(
                            When(movement_type='in', then=F('quantity')),
                            When(movement_type='out', then=F('quantity') * -1),
                            default=0,
                            output_field=IntegerField(),
                        )
                    ),
                    0,
                )
            )
        )
    }

    # Total quantity needed per product (a product may appear on several lines).
    needed = {}
    for l in lignes:
        needed[l.produit_id] = needed.get(l.produit_id, 0) + l.qte

    computed_total = 0
    total_qte = 0
    for l in lignes:
        l.unit_price = l.produit.price_vente
        l.subtotal   = l.unit_price * l.qte
        l.stock_now  = stock_map.get(l.produit_id, 0)
        l.stock_ok   = l.stock_now >= needed[l.produit_id]
        computed_total += l.subtotal
        total_qte      += l.qte

    # Stock movements generated by the validation (empty while pending).
    movements = list(
        Stock.objects.filter(ligne_vente__vente=vente)
        .select_related('product', 'user')
        .order_by('date')
    )
    validated_at = movements[0].date if movements else None
    validated_by = movements[0].user if movements else None

    return render(request, 'vente_detail.html', {
        'vente':          vente,
        'lignes':         lignes,
        'total_qte':      total_qte,
        'computed_total': computed_total,
        'total_mismatch': computed_total != vente.total,
        'movements':      movements,
        'validated_at':   validated_at,
        'validated_by':   validated_by,
        'is_validated':   vente.status == 'validation',
        'can_validate':   can_validate_vente(request.user),
    })
# ============================================
# ACHAT — Details page (read-only)
# ============================================

@login_required
def achat_detail(request, pk):
    achat = get_object_or_404(
        Achat.objects.select_related('fournisseur', 'user'), pk=pk
    )

    lignes = list(
        achat.lignes.select_related('produit', 'produit__unit').order_by('pk')
    )

    computed_total = 0
    total_qte = 0
    for l in lignes:
        l.unit_price = l.produit.price_achat
        l.subtotal   = l.unit_price * l.qte
        computed_total += l.subtotal
        total_qte      += l.qte

    # Stock "in" movements created when the achat moved to 'livraison'.
    movements = list(
        Stock.objects.filter(ligne_achat__achat=achat)
        .select_related('product', 'user')
        .order_by('date')
    )
    delivered_at = movements[0].date if movements else None
    delivered_by = movements[0].user if movements else None

    return render(request, 'achat_detail.html', {
        'achat':          achat,
        'lignes':         lignes,
        'total_qte':      total_qte,
        'computed_total': computed_total,
        'total_mismatch': computed_total != achat.total,
        'movements':      movements,
        'delivered_at':   delivered_at,
        'delivered_by':   delivered_by,
        'can_advance':    achat.status != 'livraison',
    })