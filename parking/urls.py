from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('spaces/', views.SpaceManagementView.as_view(), name='space_management'),
    path('parkings/', views.ParkingListView.as_view(), name='parking_list'),
    path('vehicles/', views.VehicleRegistryView.as_view(), name='vehicle_registry'),
    path('search/', views.VehicleSearchView.as_view(), name='vehicle_search'),
    path('checkin/<str:plate>/', views.CheckInView.as_view(), name='checkin'),
    path('checkout/<str:plate>/', views.CheckOutView.as_view(), name='checkout'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('rates/', views.RatesBillingView.as_view(), name='rates_billing'),
]
