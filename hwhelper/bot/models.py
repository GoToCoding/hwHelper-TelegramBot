from django.db import models


class User(models.Model):
    username = models.CharField(max_length=128, null=True, unique=True)
    uid = models.CharField(max_length=128, unique=True)
    state = models.CharField(max_length=128)


class Group(models.Model):
    pass


class Deadline(models.Model):
    name = models.CharField(max_length=128)
    group = models.ForeignKey(to=Group)
    date_from = models.DateField()
    date_to = models.DateField()


class GroupEntry(models.Model):
    user = models.ForeignKey(to=User)
    group = models.ForeignKey(to=Group)
    name = models.CharField(max_length=128)
    order = models.IntegerField(default=0)


class File(models.Model):
    deadline = models.ForeignKey(to=Deadline)
    file_id = models.CharField(max_length=128, unique=True)
