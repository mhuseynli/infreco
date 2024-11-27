import pandas as pd
from bson import ObjectId
from core.database import db


def fetch_webshop_data(webshop_id):
    """
    Fetch users, items, events, and attributes for a specific webshop by `id`.
    :param webshop_id: ID (string) of the webshop to fetch data for.
    :return: Tuple of users, items, events, and attributes.
    """
    # Ensure the webshop exists
    webshop = db.webshops.find_one({"id": webshop_id})
    if not webshop:
        raise ValueError(f"Webshop with id '{webshop_id}' not found.")

    # Fetch related data
    users = list(db.users.find({"webshop_id": webshop_id}))
    items = list(db.items.find({"webshop_id": webshop_id}))
    events = list(db.events.find({"webshop_id": webshop_id}))
    attributes = db.attributes.find_one({"_id": webshop.get("type_id")})

    # Convert ObjectId fields to strings for all collections
    for collection in [users, items, events]:
        for doc in collection:
            doc["_id"] = str(doc["_id"])
            if "user_id" in doc:
                doc["user_id"] = str(doc["user_id"])
            if "product_id" in doc:
                doc["product_id"] = str(doc["product_id"])
            if "event_id" in doc:
                doc["event_id"] = str(doc["event_id"])

    return users, items, events, attributes


def preprocess_items(items, attributes):
    """
    Preprocess items with dynamic attribute weights.
    """
    if not attributes or "attributes" not in attributes:
        raise ValueError("Attributes data is missing or invalid.")

    attributes_dict = {attr["name"]: attr["weight"] for attr in attributes.get("attributes", [])}

    # Flatten item attributes into a DataFrame
    items_df = pd.DataFrame(items)
    for attr, weight in attributes_dict.items():
        if attr in items_df.columns:
            items_df[attr] = items_df[attr].apply(
                lambda x: weight * x if isinstance(x, (int, float)) else weight
            )
    return items_df


def preprocess_events(events):
    """Prepare event data with event type weights."""
    event_types = {et["name"]: et["weight"] for et in db.event_types.find()}
    events_df = pd.DataFrame(events)
    events_df["event_weight"] = events_df["event_id"].apply(
        lambda eid: event_types.get(db.event_types.find_one({"_id": ObjectId(eid)})["name"], 0)
    )
    return events_df


def merge_user_item_events(users, items, events):
    """Merge user, item, and event data into a single dataset."""
    users_df = pd.DataFrame(users)
    items_df = pd.DataFrame(items)
    events_df = preprocess_events(events)

    # Merge events with users and items
    merged_df = events_df.merge(users_df, left_on="user_id", right_on="_id", how="left")
    merged_df = merged_df.merge(items_df, left_on="product_id", right_on="_id", how="left")
    return merged_df
