import logging
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from core.database import db
from bson import ObjectId
from datetime import datetime

# Initialize logger
logger = logging.getLogger('core.serializers')
# todo fix date methods
# todo fix being able to add second item with same external id

class ItemSerializer(serializers.Serializer):
    external_id = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(default=datetime.utcnow)
    updated_at = serializers.DateTimeField(default=datetime.utcnow)

    def validate(self, data):
        """Dynamic validation based on the webshop's type."""
        logger.info("Starting validation process...")
        logger.info(f"Received serializer data: {data}")

        # Access the raw request data
        raw_data = self.context.get("request").data
        logger.info(f"Received raw data: {raw_data}")

        webshop_id = self.context.get("webshop_id")
        if not webshop_id:
            logger.error("Webshop ID is missing in the context.")
            raise ValidationError({"detail": "Webshop ID is required."})

        # Fetch the webshop and its type
        webshop = db.webshops.find_one({"id": webshop_id})
        if not webshop:
            logger.error(f"Invalid webshop ID: {webshop_id}")
            raise ValidationError({"detail": "Invalid webshop ID."})

        logger.info(f"Webshop found: {webshop}")

        # Fetch the allowed attributes for the webshop type
        type_id = webshop.get("type_id")
        if not type_id:
            logger.error(f"Webshop type is not associated with webshop ID: {webshop_id}")
            raise ValidationError({"detail": "Webshop type is not associated."})

        type_data = db.attributes.find_one({"_id": ObjectId(type_id)})
        if not type_data:
            logger.error(f"Invalid type data for webshop ID: {webshop_id}")
            raise ValidationError({"detail": "Invalid type data for the webshop."})

        logger.info(f"Type data retrieved: {type_data}")

        # Extract dynamic attributes from raw data
        allowed_attributes = {attr["name"]: attr for attr in type_data.get("attributes", [])}
        dynamic_attributes = {key: value for key, value in raw_data.items() if key in allowed_attributes}

        logger.info(f"Extracted dynamic attributes: {dynamic_attributes}")

        # Validate required attributes
        for attr_name, attr_config in allowed_attributes.items():
            if attr_config.get("required", False) and attr_name not in dynamic_attributes:
                logger.error(f"Missing required attribute: {attr_name}")
                raise ValidationError({"non_field_errors": [f"Missing required attribute: {attr_name}."]})

        # Validate attribute data types
        for attr_name, attr_value in dynamic_attributes.items():
            expected_type = allowed_attributes[attr_name].get("data_type")
            if not self._validate_data_type(attr_value, expected_type):
                logger.error(f"Invalid data type for attribute '{attr_name}'. Expected {expected_type}.")
                raise ValidationError(
                    {"non_field_errors": [f"Invalid data type for attribute '{attr_name}'. Expected {expected_type}."]})

        logger.info("All attributes are valid.")

        # Merge dynamic attributes into the validated data
        data.update(dynamic_attributes)
        logger.info("Validation process completed successfully.")
        return data

    def _validate_data_type(self, value, expected_type):
        """Validate the data type of a value."""
        if expected_type == "string" and not isinstance(value, str):
            return False
        if expected_type == "number" and not isinstance(value, (int, float)):
            return False
        if expected_type == "array" and not isinstance(value, list):
            return False
        return True

    def create(self, validated_data):
        logger.info(f"Creating item with validated data: {validated_data}")
        webshop_id = self.context.get("webshop_id")
        item_data = {
            "webshop_id": webshop_id,
            "external_id": validated_data["external_id"],
            "name": validated_data["name"],
            "description": validated_data.get("description", ""),
            **{key: validated_data[key] for key in validated_data if key not in ["external_id", "name", "description"]},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = db.items.insert_one(item_data)
        item_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string
        logger.info(f"Item created successfully: {item_data}")
        return item_data

    def update(self, instance, validated_data):
        logger.info(f"Updating item {instance['_id']} with validated data: {validated_data}")
        webshop_id = self.context.get("webshop_id")
        updates = {
            "name": validated_data.get("name", instance.get("name")),
            "description": validated_data.get("description", instance.get("description")),
            **{key: validated_data[key] for key in validated_data if key not in ["external_id", "name", "description"]},
            "updated_at": datetime.utcnow(),
        }
        db.items.update_one({"_id": ObjectId(instance["_id"])}, {"$set": updates})
        updated_instance = {**instance, **updates}
        updated_instance["_id"] = str(updated_instance["_id"])  # Convert ObjectId to string
        logger.info(f"Item updated successfully: {updated_instance}")
        return updated_instance
