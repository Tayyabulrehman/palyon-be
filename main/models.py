from django.db import models

# Create your models here.
class Log(models.Model):
    """ Abstract model containing common fields."""
    created_by = models.BigIntegerField(
        db_column='CreatedBy', null=True, blank=True, default=0)
    created_on = models.DateTimeField(db_column='CreatedOn', auto_now_add=True)
    modified_by = models.BigIntegerField(
        db_column='ModifiedBy', default=0, null=True, blank=True)
    modified_on = models.DateTimeField(db_column='ModifiedOn', auto_now=True)

    class Meta:
        abstract = True