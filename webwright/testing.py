from lib.substrate import SubstrateComputationManager

# Initialize the computation manager
manager = SubstrateComputationManager()

# Ask GPT-4o-mini for a main dish idea
manager.create_node(
    "Suggest an interesting main dish for a dinner party that's not lamb.",
    model="gpt-4o-mini",
    node_name="main_dish"
)

# Ask Claude for a side dish to complement the main dish
manager.create_node(
    "Suggest a complementary side dish for {main_dish}.",
    model="claude-3-5-sonnet-20240620",
    node_name="side_dish"
)

# Use Llama3Instruct405B to outline the meal for guests
manager.create_node(
    "Create an appealing description of a meal consisting of {main_dish} and {side_dish} to present to dinner guests.",
    model="Llama3Instruct405B",
    node_name="meal_description"
)

# Use Llama3Instruct405B to suggest a wine pairing
manager.create_node(
    "Suggest an appropriate wine pairing for a meal of {main_dish} and {side_dish}.",
    model="Llama3Instruct405B",
    node_name="wine_pairing"
)

# Create the final meal prep instructions for the cook
manager.create_node(
    "Provide detailed meal for guests and meal preparation instructions for the cook, including the following:\n"
    "Main Dish: {main_dish}\n"
    "Side Dish: {side_dish}\n"
    "Wine Pairing: {wine_pairing}\n"
    "Meal Description: {meal_description}\n"
    "Include timing and any special techniques required.",
    model="Llama3Instruct405B",
    node_name="final_meal_prep"
)

# Run the entire computation chain and retrieve the result
result = manager.run_computation("baketime_temp")

# Output the final meal prep instructions
print(f"Final Meal Preparation Instructions:\n\n{result.get(manager.node_registry['final_meal_prep']['node']).text}")