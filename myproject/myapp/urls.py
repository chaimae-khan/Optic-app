# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('',              views.index,       name='index'),
    path('login/',        views.login,       name='login'),
    path('logout/',       views.logout,      name='logout'),
    path('register/',     views.register,    name='register'),
    path('about/',        views.about,       name='about'),

    # Protected
    path('analytics/',    views.analytics,   name='analytics'),
    path('settings/',     views.settings,    name='settings'),

    # User management
    path('users/',                        views.users_list,  name='users'),
    path('users/edit/<int:user_id>/',     views.edit_user,   name='edit_user'),
    # path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    # ── Permissions Manager ──────────────────────────────────────
    path('permissions/',                        views.permissions_manager,    name='permissions_manager'),
    path('permissions/group/<int:group_id>/',   views.edit_group_permissions, name='edit_group_permissions'),
    path('permissions/create/',                 views.create_group,           name='create_group'),
    path('permissions/delete/<int:group_id>/',  views.delete_group,           name='delete_group'),
    
    
    # ── Category  Manager ──────────────────────────────────────
    path('category/', views.category_list, name='category_list'),
    path('category/add/', views.category_create, name='category_add'),
    path('category/edit/<int:pk>/', views.category_update, name='category_edit'),
    path('category/delete/<int:pk>/', views.category_delete, name='category_delete'),
    # ── SubCategory  Manager ──────────────────────────────────────
    path('subcategory/',                    views.subcategory_list,    name='subcategory_list'),
    path('subcategory/add/',               views.subcategory_create,  name='subcategory_add'),
    path('subcategory/edit/<int:pk>/',     views.subcategory_update,  name='subcategory_edit'),
    path('subcategory/delete/<int:pk>/',   views.subcategory_delete,  name='subcategory_delete'),
    # ── unite  Manager ──────────────────────────────────────
    path('unite/',                   views.unite_list,   name='unite_list'),
    path('unite/add/',               views.unite_create, name='unite_add'),
    path('unite/edit/<int:pk>/',     views.unite_update, name='unite_edit'),
    path('unite/delete/<int:pk>/',   views.unite_delete, name='unite_delete'),
    # Brand Manager ──────────────────────────────────────
    path('brand/',               views.brand_list,   name='brand_list'),
    path('brand/add/',           views.brand_create, name='brand_add'),
    path('brand/edit/<int:pk>/', views.brand_update, name='brand_edit'),
    path('brand/delete/<int:pk>/', views.brand_delete, name='brand_delete'),
    path('audit-log/', views.audit_log, name='audit_log'),
    path('local/',                views.local_list,   name='local_list'),
    # Local Manager ──────────────────────────────────────
    path('local/add/',            views.local_create, name='local_add'),
    path('local/edit/<int:pk>/',  views.local_update, name='local_edit'),
    path('local/delete/<int:pk>/', views.local_delete, name='local_delete'),
     # Rayon  Manager ──────────────────────────────────────
    path('rayon/',              views.rayon_list,   name='rayon_list'),
    path('rayon/add/',          views.rayon_create, name='rayon_add'),
    path('rayon/edit/<int:pk>/', views.rayon_update, name='rayon_edit'),
    path('rayon/delete/<int:pk>/', views.rayon_delete, name='rayon_delete'),
    # fournisseur  Manager ──────────────────────────────────────
    path('fournisseur/',               views.fournisseur_list,   name='fournisseur_list'),
    path('fournisseur/add/',           views.fournisseur_create, name='fournisseur_add'),
    path('fournisseur/edit/<int:pk>/', views.fournisseur_update, name='fournisseur_edit'),
    path('fournisseur/delete/<int:pk>/', views.fournisseur_delete, name='fournisseur_delete'),
    # Produckt  Manager ──────────────────────────────────────
    path('product/',                 views.product_list,    name='product_list'),
    path('product/add/',             views.product_create,  name='product_add'),
    path('product/edit/<int:pk>/',   views.product_update,  name='product_edit'),
    path('product/delete/<int:pk>/', views.product_delete,  name='product_delete'),
    path('api/rayons-by-local/',     views.rayons_by_local, name='rayons_by_local'),
    # achat  Manager ──────────────────────────────────────
    path('achat/', views.achat_create, name='achat_create'),
    path('achat/product-search/', views.achat_product_search, name='achat_product_search'),
    path('achat/temp/add/', views.achat_temp_add, name='achat_temp_add'),
    path('achat/temp/list/', views.achat_temp_list, name='achat_temp_list'),
    path('achat/temp/update/', views.achat_temp_update_qte, name='achat_temp_update_qte'),
    path('achat/temp/delete/', views.achat_temp_delete, name='achat_temp_delete'),
    path('achat/validate/', views.achat_validate, name='achat_validate'),
    path('achat/<int:pk>/advance-status/', views.achat_advance_status, name='achat_advance_status'),
    path('achat/save-cart/', views.achat_save_cart, name='achat_save_cart'),
    path('achat/<int:pk>/delete/', views.achat_delete, name='achat_delete'), 
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/history/', views.stock_history, name='stock_history'),
    path('stock/history/<int:product_id>/', views.stock_history_ajax, name='stock_history_ajax'),
    
    ]