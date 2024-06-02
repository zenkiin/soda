import json
import logging
from datetime import datetime
import requests
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.db.models import (
    Case,
    CharField,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Concat, Cast
from django.http import JsonResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.csrf import csrf_exempt
from tapi_yandex_metrika import YandexMetrikaStats

from .forms import CounterForm
from .models import Counter, MetricData, Visualization

logger = logging.getLogger(__name__)

def connections(request):
    counters = Counter.objects.all()
    return render(request, 'connections.html', {'counters': counters})

def add_counter(request):
    if request.method == 'POST':
        form = CounterForm(request.POST)
        if form.is_valid():
            counter = form.save(commit=False)
            try:
                api = YandexMetrikaStats(access_token=counter.token, receive_all_data=True)
                params = dict(
                    ids=counter.counter_id,
                    metrics="ym:s:users,ym:s:visits,ym:s:pageviews",
                    dimensions="ym:s:date",
                    date1="2024-01-01",
                    date2="today",
                    sort="ym:s:date",
                    accuracy="full",
                    limit=1
                )
                result = api.stats().get(params=params)
                result = result().data
                if result:
                    counter.save()
                    return redirect('connections')
            except Exception as e:
                form.add_error(None, f'Произошла ошибка при проверке счетчика: {e}')
    else:
        form = CounterForm()
    return render(request, 'add_counter.html', {'form': form})

def data(request):
    counters = Counter.objects.all()
    current_date = datetime.today().strftime('%Y-%m-%d')
    metrics_data = {
        counter.id: list(MetricData.objects.filter(counter=counter).values('date', 'users', 'visits', 'pageviews'))
        for counter in counters
    }
    return render(request, 'data.html', {'counters': counters, 'current_date': current_date, 'metrics_data': metrics_data})

def visualizations(request):
    return render(request, 'visualizations.html')

def delete_counter(request, counter_id):
    counter = get_object_or_404(Counter, id=counter_id)
    counter.delete()
    return redirect('connections')

@csrf_exempt
def fetch_yandex_metrics_data(request, counter_id):
    counter = get_object_or_404(Counter, id=counter_id)
    if request.method == 'POST':
        data = json.loads(request.body)
        start_date = data.get('startDate')
        end_date = data.get('endDate')

        # Проверка даты
        if datetime.strptime(start_date, '%Y-%m-%d') < datetime(2023, 1, 1) or datetime.strptime(end_date, '%Y-%m-%d') > datetime.today():
            return JsonResponse({'error': 'Invalid date range'}, status=400)

        # Вызов API Яндекс Метрики
        params = dict(
            ids=counter.counter_id,
            metrics="ym:s:users,ym:s:visits,ym:s:pageviews",
            dimensions="ym:s:date",
            date1=start_date,
            date2=end_date,
            sort="ym:s:date",
            accuracy="full",
            limit=10000
        )

        headers = {'Authorization': f'OAuth {counter.token}'}

        try:
            response = requests.get('https://api-metrika.yandex.net/stat/v1/data', headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            if 'data' not in result:
                logger.error('No data field in response: %s', result)
                return JsonResponse({'error': 'Invalid response from Yandex Metrika'}, status=500)

            result_data = result['data']
            if not result_data:
                logger.error('Empty data in response: %s', result)
                return JsonResponse({'error': 'No data returned from Yandex Metrika'}, status=500)

            results = []
            for row in result_data:
                if 'dimensions' in row and len(row['dimensions']) > 0:
                    date = row['dimensions'][0]['name']
                    users = row['metrics'][0]
                    visits = row['metrics'][1]
                    pageviews = row['metrics'][2]

                    MetricData.objects.create(
                        counter=counter,
                        date=date,
                        users=users,
                        visits=visits,
                        pageviews=pageviews,
                    )

                    results.append({
                        'date': date,
                        'users': users,
                        'visits': visits,
                        'pageviews': pageviews
                    })
                else:
                    logger.error('Missing dimensions in row: %s', row)

            return JsonResponse({'message': 'Data fetched and saved successfully', 'results': results})

        except requests.exceptions.RequestException as e:
            logger.error(f'Network error while accessing Yandex.Metrika API: {e}')
            return JsonResponse({'error': 'Network error while accessing Yandex.Metrika API'}, status=500)
        except json.JSONDecodeError as e:
            logger.error(f'Error decoding JSON: {e}')
            return JsonResponse({'error': 'Error decoding JSON from Yandex.Metrika API'}, status=500)
        except KeyError as e:
            logger.error(f'Error accessing data in API response: {e}')
            return JsonResponse({'error': 'Error accessing data in Yandex.Metrika API response'}, status=500)
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            return JsonResponse({'error': 'Unexpected error occurred'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def delete_data(request, counter_id):
    if request.method == 'POST':
        counter = get_object_or_404(Counter, id=counter_id)
        MetricData.objects.filter(counter=counter).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def fetch_all_yandex_metrics_data(request, counter_id):
    counter = get_object_or_404(Counter, id=counter_id)
    if request.method == 'GET':
        results = list(MetricData.objects.filter(counter=counter).values('date', 'users', 'visits', 'pageviews'))
        return JsonResponse({'results': results})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def delete_data(request, counter_id):
    if request.method == 'POST':
        counter = get_object_or_404(Counter, id=counter_id)
        MetricData.objects.filter(counter=counter).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def visualizations(request):
    visualizations = Visualization.objects.all()
    return render(request, 'visualizations.html', {'visualizations': visualizations})
@csrf_exempt
def get_chart_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            x_axis = data.get('xAxis')
            y_axes = data.get('yAxes')

            if not x_axis or not y_axes:
                return JsonResponse({'error': 'Missing xAxis or yAxes'}, status=400)

            labels = []
            datasets = []

            for y_axis in y_axes:
                if y_axis is None:
                    return JsonResponse({'error': 'yAxis is None'}, status=400)

                if '.' not in y_axis:
                    return JsonResponse({'error': f'Invalid yAxis format: {y_axis}'}, status=400)

                counter_id, metric = y_axis.split('.')
                counter = get_object_or_404(Counter, id=counter_id)
                metric_data = MetricData.objects.filter(counter=counter)

                if x_axis == 'month':
                    metric_data = metric_data.annotate(
                        month=Concat(
                            Cast('date__year', CharField()),
                            Value('-'),
                            Cast('date__month', CharField())
                        )
                    ).values('month').annotate(
                        value=Sum(metric)
                    ).order_by('month')
                    labels = [item['month'] for item in metric_data]
                elif x_axis == 'quarter':
                    metric_data = metric_data.annotate(
                        quarter=Case(
                            When(date__month__in=[1, 2, 3], then=Value('Q1')),
                            When(date__month__in=[4, 5, 6], then=Value('Q2')),
                            When(date__month__in=[7, 8, 9], then=Value('Q3')),
                            When(date__month__in=[10, 11, 12], then=Value('Q4')),
                            output_field=CharField(),
                        )
                    ).annotate(
                        quarter_str=Concat(
                            Cast('date__year', CharField()),
                            Value('-'),
                            'quarter'
                        )
                    ).values('quarter_str').annotate(
                        value=Sum(metric)
                    ).order_by('quarter_str')
                    labels = [item['quarter_str'] for item in metric_data]
                else:  # date
                    metric_data = metric_data.values('date').annotate(
                        value=Sum(metric)
                    ).order_by('date')
                    labels = [item['date'].strftime('%Y-%m-%d') for item in metric_data]

                values = [item['value'] for item in metric_data]
                datasets.append({'label': y_axis, 'data': values})

            return JsonResponse({'labels': labels, 'datasets': datasets})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def save_visualization(request, visualization_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        x_axis = data.get('xAxis')
        y_axes = data.get('yAxes')
        colors = data.get('colors')

        visualization = get_object_or_404(Visualization, id=visualization_id)
        visualization.x_axis = x_axis
        visualization.y_axes = y_axes
        visualization.colors = colors
        visualization.save()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def add_visualization(request):
    if request.method == 'POST':
        name = request.POST.get('visualization_name')
        visualization = Visualization.objects.create(name=name)
        return redirect('visualization_chart', visualization_id=visualization.id)
    return redirect('visualizations')

def visualization_chart(request, visualization_id):
    visualization = get_object_or_404(Visualization, id=visualization_id)
    counters = Counter.objects.all()
    return render(request, 'visualization_chart.html', {
        'visualization': visualization,
        'counters': counters
    })

def delete_visualization(request, visualization_id):
    if request.method == 'POST':
        visualization = get_object_or_404(Visualization, id=visualization_id)
        visualization.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

class CustomLoginView(LoginView):
    template_name = 'login.html'  # ваш шаблон страницы входа

    def form_invalid(self, form):
        messages.error(self.request, 'Неверные учетные данные. Пожалуйста, попробуйте снова.')
        return super().form_invalid(form)
