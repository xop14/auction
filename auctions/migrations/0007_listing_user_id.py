# Generated by Django 4.1.3 on 2022-11-29 03:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0006_alter_listing_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='user_id',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
