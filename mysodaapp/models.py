from django.db import models

class Counter(models.Model):
    name = models.CharField(max_length=100)
    counter_id = models.CharField(max_length=50)
    token = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class MetricData(models.Model):
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE)
    date = models.DateField()
    users = models.IntegerField()
    visits = models.IntegerField()
    pageviews = models.IntegerField()

class Visualization(models.Model):
    name = models.CharField(max_length=255)
    x_axis = models.CharField(max_length=255, default='date')
    y_axes = models.JSONField(default=list)
    colors = models.JSONField(default=list)