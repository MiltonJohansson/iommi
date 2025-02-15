from django.apps import AppConfig

from iommi.from_model import register_search_fields


class IommiConfig(AppConfig):
    name = 'iommi'
    verbose_name = 'iommi'
    default = True

    def ready(self):
        from django.contrib.auth.models import (
            User,
            Permission,
        )

        register_search_fields(model=User, search_fields=['username'])
        register_search_fields(model=Permission, search_fields=['codename'])

        from iommi import register_style
        from iommi import Style
        from iommi.style_test_base import test
        from iommi.style_base import base
        from iommi.style_bootstrap import bootstrap
        from iommi.style_semantic_ui import semantic_ui
        from iommi.style_foundation import foundation
        from iommi.style_django_admin import django_admin
        from iommi.style_water import water
        from iommi.style_bulma import bulma

        register_style('blank', Style())
        register_style('base', base)
        register_style('test', test)
        register_style('bulma', bulma)
        register_style('bootstrap', bootstrap)
        register_style('semantic_ui', semantic_ui)
        register_style('water', water)
        register_style('foundation', foundation)
        register_style('django_admin', django_admin)
