from django.contrib import admin
from django.urls import path
from mysodaapp.views import (
    connections, add_counter, delete_counter, data,
    visualizations, fetch_yandex_metrics_data, delete_data, get_chart_data,
    add_visualization, visualization_chart, save_visualization, fetch_all_yandex_metrics_data, delete_visualization
)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic.base import RedirectView
from django.urls import path, reverse_lazy
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('connections/', connections, name='connections'),
    path('add-counter/', add_counter, name='add_counter'),
    path('delete-counter/<int:counter_id>/', delete_counter, name='delete_counter'),
    path('data/', data, name='data'),
    path('fetch_yandex_metrics_data/<int:counter_id>/', fetch_yandex_metrics_data, name='fetch_yandex_metrics_data'),
    path('fetch_all_yandex_metrics_data/<int:counter_id>/', fetch_all_yandex_metrics_data, name='fetch_all_yandex_metrics_data'),
    path('visualizations/', visualizations, name='visualizations'),
    path('delete_data/<int:counter_id>/', delete_data, name='delete_data'),
    path('add-visualization/', add_visualization, name='add_visualization'),
    path('visualization-chart/<int:visualization_id>/', visualization_chart, name='visualization_chart'),
    path('get_chart_data/', get_chart_data, name='get_chart_data'),
    path('save_visualization/<int:visualization_id>/', save_visualization, name='save_visualization'),
    path('visualizations/<int:visualization_id>/delete/', delete_visualization, name='delete_visualization'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('connections/', RedirectView.as_view(pattern_name='connections'), name='connections_redirect'),
    path('', RedirectView.as_view(url=reverse_lazy('connections')), name='home'),

]