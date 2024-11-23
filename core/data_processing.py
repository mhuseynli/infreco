from pymongo import MongoClient
from collections import defaultdict
from .database import db

def fetch_webshop_data(webshop_id):
    """Fetch users, items, and events for a specific webshop."""
    users = list(db.users.find({"webshop_id": webshop_id}))
    items = list(db.items.find({"webshop_id": webshop_id}))
    events = list(db.events.find({"webshop_id": webshop_id}))
    return users, items, events

def validate_user_attributes(user):
    """Ensure required user attributes are present."""
    required_attrs = {"location", "age", "gender"}
    user_attrs = user.get("attributes", {})
    return all(attr in user_attrs for attr in required_attrs)

def validate_item_attributes(item):
    """Ensure required item attributes are present."""
    required_attrs = {"name", "price", "categories", "brand", "description"}
    item_attrs = item.get("attributes", {})
    return all(attr in item_attrs for attr in required_attrs)

def group_users_by_age(users):
    """Group users into age ranges."""
    age_groups = defaultdict(list)
    for user in users:
        age = user.get("attributes", {}).get("age")
        if age is not None:
            age_group = f"{(age // 5) * 5}-{(age // 5) * 5 + 4}"  # E.g., 20-24
            age_groups[age_group].append(user["_id"])
    return age_groups