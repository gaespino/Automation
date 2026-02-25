from services.data_handler import DataHandler

class UnitService:
    @staticmethod
    def get_products():
        return DataHandler.get_products()

    @staticmethod
    def get_buckets(product):
        return DataHandler.get_buckets(product)

    @staticmethod
    def get_units(product, bucket, platform):
        return DataHandler.get_units(product, bucket, platform)

    @staticmethod
    def create_product(name):
        if not name:
            return False, "Product name is required"
        # Additional validation logic can be added here
        return DataHandler.create_product(name)

    @staticmethod
    def create_bucket(product, name):
        if not product or not name:
            return False, "Product and Bucket name are required"
        return DataHandler.create_bucket(product, name)

    @staticmethod
    def create_unit(product, bucket, visual_id, platform, qdf):
        if not all([product, bucket, visual_id, platform, qdf]):
            return False, "All fields are required"
        
        # Check if unit already exists
        existing_units = DataHandler.get_units(product, bucket, platform)
        if visual_id in existing_units:
            return False, f"Unit {visual_id} already exists"

        return DataHandler.create_unit_structure(product, bucket, visual_id, platform, qdf)
