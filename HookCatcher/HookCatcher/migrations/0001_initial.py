# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-17 18:34
from __future__ import unicode_literals

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Commit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('git_repo', models.CharField(max_length=200)),
                ('git_branch', models.CharField(max_length=200)),
                ('git_hash', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Diff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('diff_img_file', models.ImageField(max_length=500, upload_to='media/img')),
                ('diff_percent', models.DecimalField(decimal_places=5, default=0, max_digits=6)),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img_file', models.ImageField(max_length=500, upload_to='media/img')),
                ('browser_type', models.CharField(max_length=200)),
                ('operating_system', models.CharField(max_length=200)),
                ('device_res_width', models.IntegerField()),
                ('device_res_height', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='PR',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('git_repo', models.CharField(max_length=200)),
                ('git_pr_number', models.IntegerField(unique=True)),
                ('git_pr_commit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='merge_commit_in_PR', to='HookCatcher.Commit')),
                ('git_source_commit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_commit_in_PR', to='HookCatcher.Commit')),
                ('git_target_commit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_commit_in_PR', to='HookCatcher.Commit')),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state_uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('state_name', models.CharField(max_length=200)),
                ('state_desc', models.TextField()),
                ('state_url', models.TextField()),
                ('git_commit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='HookCatcher.Commit')),
            ],
        ),
        migrations.AddField(
            model_name='image',
            name='state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='HookCatcher.State'),
        ),
        migrations.AddField(
            model_name='diff',
            name='source_img',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_img_in_Diff', to='HookCatcher.Image'),
        ),
        migrations.AddField(
            model_name='diff',
            name='target_img',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_img_in_Diff', to='HookCatcher.Image'),
        ),
    ]
