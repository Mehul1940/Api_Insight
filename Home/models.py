from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class CityMonitoring(models.Model):
    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    ZONE_CHOICES = [
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
        ('central', 'Central'),
    ]

    photo = models.ImageField(upload_to='ftp/') 
    latitude = models.FloatField()
    longitude = models.FloatField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    reported_on = models.DateTimeField(auto_now_add=True)
    identify_object = models.ImageField(upload_to='cropped_objects/')
    reason = models.TextField(blank=True) 
    completed_time = models.DateTimeField(null=True, blank=True)
    remark = models.TextField(blank=True)
    zone = models.CharField(max_length=20, choices=ZONE_CHOICES, blank=True)  
    ward = models.CharField(max_length=50, blank=True)  

    def __str__(self):
        return f"Report {self.id}"
