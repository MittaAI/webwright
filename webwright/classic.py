from lib.substrate import SubstrateComputationManager

# Initialize the computation manager
manager = SubstrateComputationManager()

# Ask GPT-4o-mini for a classic car model to redo
manager.create_node(
    "Suggest a classic car model that would be a good candidate for a redo.",
    model="gpt-4o-mini",
    node_name="classic_car_model"
)

# Ask Claude for a color scheme to complement the classic car model
manager.create_node(
    "Suggest a color scheme that would complement the {classic_car_model}.",
    model="claude-3-5-sonnet-20240620",
    node_name="color_scheme"
)

# Use Llama3Instruct405B to outline the redo plan for the classic car
manager.create_node(
    "Create a detailed plan for redoing the {classic_car_model}, including the following:\n"
    "Color Scheme: {color_scheme}\n"
    "Interior Design: \n"
    "Exterior Design: \n"
    "Mechanical Upgrades: \n"
    "Electrical Upgrades: \n"
    "Special Features: \n"
    "Timeline: \n"
    "Budget: \n",
    model="Llama3Instruct405B",
    node_name="redo_plan"
)

# Use Llama3Instruct405B to suggest a budget for the redo project
manager.create_node(
    "Suggest a budget for the redo project based on the {redo_plan}.",
    model="Llama3Instruct405B",
    node_name="budget"
)

# Create the final redo instructions for the mechanic
manager.create_node(
    "Provide detailed redo instructions for the mechanic, including the following:\n"
    "Classic Car Model: {classic_car_model}\n"
    "Color Scheme: {color_scheme}\n"
    "Redo Plan: {redo_plan}\n"
    "Budget: {budget}\n"
    "Timeline: \n"
    "Special Techniques Required: \n",
    model="Llama3Instruct405B",
    node_name="final_redo_instructions"
)

# Run the entire computation chain and retrieve the result
result = manager.run_computation("final_redo_instructions")

# Output the final redo instructions
print(f"Final Redo Instructions:\n\n{result.get(manager.node_registry['final_redo_instructions']['node']).text}")