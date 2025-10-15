class Recipe:
    def __init__(self, name, recipe_type, fields, sockets, fuses):
        self.name = name
        self.recipe_type = recipe_type
        self.fields = fields
        self.sockets = sockets
        self.fuses = fuses

    def __repr__(self):
        return f"<Recipe {self.name}>"