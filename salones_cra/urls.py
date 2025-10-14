from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from booking import views as booking_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', booking_views.index, name='index'),
    path('reservas/', booking_views.reservation_list, name='reservation_list'),
    path('panel/', booking_views.admin_dashboard, name='admin_dashboard'),
    path('reservas/mensual/', booking_views.reservation_monthly, name='reservation_monthly'),
    path('reservas/nueva/', booking_views.reservation_create, name='reservation_create'),
    path('reservas/<int:pk>/editar/', booking_views.reservation_update, name='reservation_update'),
    path('reservas/<int:pk>/cancelar/', booking_views.reservation_cancel, name='reservation_cancel'),
    path('bloqueos/', booking_views.blackout_list, name='blackout_list'),
    path('bloqueos/nuevo/', booking_views.blackout_create, name='blackout_create'),
    path('bloqueos/<int:pk>/editar/', booking_views.blackout_update, name='blackout_update'),
    path('bloqueos/<int:pk>/eliminar/', booking_views.blackout_delete, name='blackout_delete'),
    # Material Management URLs
    path('materiales/', booking_views.material_list, name='material_list'),
    path('materiales/nuevo/', booking_views.material_create, name='material_create'),
    path('materiales/<int:pk>/editar/', booking_views.material_update, name='material_update'),
    path('materiales/<int:pk>/eliminar/', booking_views.material_delete, name='material_delete'),
    # Inventory Management URLs
    path('inventario/', booking_views.inventory_list, name='inventory_list'),
    path('inventario/nuevo/', booking_views.inventory_create, name='inventory_create'),
    path('inventario/<int:pk>/actualizar/', booking_views.inventory_update, name='inventory_update'),
    path('inventario/<int:pk>/eliminar/', booking_views.inventory_delete, name='inventory_delete'),
    # User Management URLs
    path('usuarios/', booking_views.user_list, name='user_list'),
    path('usuarios/nuevo/', booking_views.user_create, name='user_create'),
    # Reports URLs
    path('reportes/', booking_views.reports_view, name='reports'),
    path('reportes/exportar/pdf/', booking_views.export_reports_pdf, name='export_reports_pdf'),
    path('reportes/exportar/excel/', booking_views.export_reports_excel, name='export_reports_excel'),
    # Authentication URLs
    path('cuentas/login/', auth_views.LoginView.as_view(), name='login'),
    path('cuentas/logout/', booking_views.custom_logout, name='logout'),
    path('cuentas/registro/', booking_views.user_register, name='register'),
    path('api/', include('booking.api.urls')),
]
