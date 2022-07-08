from django.db import models

# Create your models here.
class Users(models.Model):
    user_id = models.CharField(primary_key=True, max_length=48)
    angry = models.FloatField()
    disgusted = models.FloatField()
    sad = models.FloatField()
    fearful = models.FloatField()
    happy = models.FloatField()
    neutral = models.FloatField()
    surprised = models.FloatField()
    createdby = models.DateTimeField(db_column='createdBy', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Users'
