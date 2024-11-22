import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.contrib.auth.models import Group
from backend.webshop.models import Account

def add_manager(username, password):
    # Create the user
    user, created = Account.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.save()
        print(f"User '{username}' created.")
    else:
        print(f"User '{username}' already exists.")

    # Get or create the "Manager" group
    manager_group, _ = Group.objects.get_or_create(name='Manager')

    # Add user to the "Manager" group
    user.groups.add(manager_group)
    print(f"User '{username}' added to 'Manager' group.")

# Example usage
if __name__ == "__main__":
    add_manager("manager", "admin")
