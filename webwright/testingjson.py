from lib.substrate import SubstrateComputationManager, ComputeJSON
import json

# Initialize the computation manager
manager = SubstrateComputationManager()

# Schema for ingredients (to be used with Mixtral)
ingredients_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "ingredient": {"type": "string"},
            "amount": {"type": "string"}
        },
        "required": ["ingredient", "amount"]
    }
}

# Schema for temperature
temperature_schema = {
    "type": "object",
    "properties": {
        "value": {"type": "number"},
        "unit": {"type": "string"}
    },
    "required": ["value", "unit"]
}

# Ask for a cake idea (ComputeText)
manager.create_node(
    prompt="Suggest an interesting cake recipe idea.",
    model="gpt-4o-mini",
    node_name="cake_idea"
)

# Ask Claude for ingredients in JSON format (ComputeText)
manager.create_node(
    prompt="""
    For the {cake_idea}, provide a list of ingredients with their measurements.
    Format your response as a JSON array of objects, where each object has 'ingredient' and 'amount' keys.
    For example:
    ```json
    [
        {"ingredient": "all-purpose flour", "amount": "2 cups"},
        {"ingredient": "granulated sugar", "amount": "1 1/2 cups"}
    ]
    ```
    Ensure your response is valid JSON.
    """,
    model="claude-3-5-sonnet-20240620",
    node_name="claude_ingredients"
)

# Use Mixtral to extract and validate the JSON ingredients (ComputeJSON)
manager.create_node(
    prompt="""
    Extract and validate the JSON ingredients list from the following text:
    {claude_ingredients}
    
    Ensure the output conforms to the provided schema and is valid JSON.
    If any corrections are needed, make them while preserving the original intent.
    """,
    model="Mixtral8x7BInstruct",
    node_type=ComputeJSON,
    node_name="ingredients",
    json_schema=ingredients_schema
)

# Get cooking temperature with JSON schema (ComputeJSON)
manager.create_node(
    prompt="Provide the cooking temperature for {cake_idea}.",
    model="Llama3Instruct8B",
    node_type=ComputeJSON,
    node_name="temperature",
    json_schema=temperature_schema
)

# Get cooking instructions (ComputeText)
manager.create_node(
    prompt="Provide step-by-step cooking instructions for {cake_idea}, using the ingredients {ingredients}. Do not include the temperature in these instructions.",
    model="Llama3Instruct405B",
    node_name="cooking_instructions"
)

# Create the final output combining all information (ComputeText)
manager.create_node(
    prompt="""
    Create a final recipe combining all the information for the {cake_idea}.
    Use the following template:
    
    Cake Name: [Insert cake name]
    
    Ingredients:
    [List all ingredients from {ingredients}]
    
    Instructions:
    [Insert step-by-step instructions from {cooking_instructions}]
    
    Baking Temperature: {temperature.value} {temperature.unit}
    
    Ensure all placeholders are replaced with the actual information.
    """,
    model="claude-3-5-sonnet-20240620",
    node_name="final_recipe"
)

# Run the entire computation chain and retrieve the result
result = manager.run_computation("final_recipe")

# Safely access and print the final recipe
try:
    final_recipe_node = manager.node_registry['final_recipe']['node']
    final_recipe_text = result.get(final_recipe_node)
    print("Final Recipe:")
    print(final_recipe_text.text)  # Access the .text attribute for the final recipe text
except ValueError as e:
    print(f"Error retrieving final recipe: {e}")

# Access to the structured data (ingredients and temperature)
try:
    ingredients_node = manager.node_registry['ingredients']['node']
    ingredients = result.get(ingredients_node).json_object  # Directly pass the node object
    print("\nStructured Ingredients Data:")
    print(json.dumps(ingredients, indent=2))
except ValueError as e:
    print(f"Error retrieving ingredients data: {e}")

try:
    temperature_node = manager.node_registry['temperature']['node']
    temperature = result.get(temperature_node).json_object  # Directly pass the node object
    print("\nStructured Temperature Data:")
    print(json.dumps(temperature, indent=2))
except ValueError as e:
    print(f"Error retrieving temperature data: {e}")
