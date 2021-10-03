from django.db import models

# Create your models here.


class User(models.Model):
    """ ユーザーモデル """

    class Meta:
        """ テーブル名の定義 """
        db_table = "user"

    user_id = models.CharField("user_id", max_length=50, primary_key=True)
    display_name = models.CharField(
        "user_name", max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(
        "created_at", null=True, auto_now_add=True)
    deleted_flag = models.BooleanField("deleted_flag", default=False)

    def __str__(self):
        return self.display_name
