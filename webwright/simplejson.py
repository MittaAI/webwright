from lib.substrate import SubstrateComputationManager, ComputeJSON, ComputeText
import json

from pydantic import BaseModel, Field
from typing import List

class Ingredient(BaseModel):
    ingredient: str = Field(..., description="Name of the ingredient")
    amount: str = Field(..., description="Amount of the ingredient")

class Recipe(BaseModel):
    name: str = Field(..., description="The recipe's name")
    ingredients: List[Ingredient] = Field(..., description="List of ingredients")

class BakingInstructions(BaseModel):
    temperature: int = Field(..., description="Baking temperature")
    time: int = Field(..., description="Baking time")
    unit: str = Field(..., description="Temperature unit (e.g., 'F' for Fahrenheit, 'C' for Celsius)")

# Generate the JSON schemas
recipe_schema = Recipe.model_json_schema()
baking_schema = BakingInstructions.model_json_schema()

# Initialize the computation manager
manager = SubstrateComputationManager()

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
    json_schema=recipe_schema
)

manager.create_node(
    prompt="What is the baking temperature, temp unit, and time for the {cake_idea} with {claude_ingredients}?",
    model="gpt-4o-mini",
    node_name="temperature",
    node_type=ComputeJSON,
    json_schema=baking_schema
)

# Create the final output combining all information (ComputeText)
manager.create_node(
    prompt="""Baking Temperature: {temperature.temperature}{temperature.unit}\n
    Baking time: {temperature.time}.\n""",
    model="claude-3-5-sonnet-20240620",
    node_name="baking_time_temp",
    node_type=ComputeText
)

# Run the entire computation chain and retrieve the result
result = manager.run_computation("baking_time_temp")
print(dir(result))

