# Generated by Django 3.1.3 on 2023-07-18 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teprunner', '0002_auto_20230718_1329'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='case',
            name='creator_nickname',
        ),
        migrations.RemoveField(
            model_name='taskresult',
            name='elapsed',
        ),
        migrations.RemoveField(
            model_name='taskresult',
            name='output',
        ),
        migrations.RemoveField(
            model_name='taskresult',
            name='run_user_nickname',
        ),
        migrations.AddField(
            model_name='case',
            name='creator_id',
            field=models.IntegerField(default=0, verbose_name='创建人id'),
        ),
        migrations.AddField(
            model_name='taskresult',
            name='report_path',
            field=models.CharField(default='', max_length=300, verbose_name='测试报告'),
        ),
        migrations.AddField(
            model_name='taskresult',
            name='run_user_id',
            field=models.IntegerField(default=0, verbose_name='运行人id'),
        ),
    ]
