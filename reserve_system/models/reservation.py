from django.db import models

# Create your models here.


class Reservation(models.Model):
    """ 予約モデル """

    class Meta:
        """ テーブル名の定義 """
        db_table = "reservation"

    user = models.ForeignKey('User', related_name='user',
                             on_delete=models.CASCADE, blank=True, null=True)
    reservation_date = models.DateTimeField(
        "reservation_date", blank=True, null=True, )
    created_at = models.DateTimeField(
        "created_at", null=True, auto_now_add=True, blank=True)
    update_at = models.DateTimeField(
        "update_at", auto_now=False, null=True, blank=True)
    done_flag = models.BooleanField("done_flag", default=False)
    # content=models.TextField()
    #hospital_num=models.CharField("hospital_num", max_length=50)
