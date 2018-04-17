from django.db import models


class MyModel(models.Model):
    heading = models.CharField(max_length=5)
    img = models.ImageField(upload_to='my_model/img')
    number = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.heading


class AnotherModel(models.Model):
    title = models.CharField(max_length=10)
    thumb = models.ImageField(upload_to='another_model/thumb')
    image = models.ImageField(upload_to='another_model/image')

    def __str__(self):
        return self.title


class GreatModel(models.Model):
    name = models.CharField(max_length=10)
    picture = models.ImageField(upload_to='great_model/picture')
    large_img = models.ImageField(upload_to='great_model/large_img')

    def __str__(self):
        return self.name
