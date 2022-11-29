# Generated by Django 4.1.3 on 2022-11-29 02:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0002_bid_listing'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_stamp', models.DateTimeField(auto_now=True)),
                ('listing_id', models.IntegerField()),
                ('user_id', models.IntegerField()),
                ('comment', models.CharField(max_length=1024)),
            ],
        ),
    ]
