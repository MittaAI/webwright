import json
from substrate import Substrate, ComputeJSON, ComputeText, sb

print("there")

# Original JSON object
original = {
    "personalInfo": {
        "name": "John Doe",
        "age": 30,
    },
    "occupation": "Software Engineer",
    "fullAddress": "123 Main St, Anytown",
    "address": {
        "street": "123 Main St",
        "city": "Anytown",
    },
}

print("here")

# Initialize Substrate with an API key
substrate = Substrate(api_key="apik_z6hKNptn4woYRLKsXgFDW1nZwV1byUe5")

# Define target JSON schema
target_schema = {
    "type": "object",
    "properties": {
        "fullName": {"type": "string"},
        "yearsOld": {"type": "integer", "minimum": 0},
        "profession": {"type": "string"},
        "location": {
            "type": "object",
            "properties": {
                "streetAddress": {"type": "string"},
                "cityName": {"type": "string"}
            },
            "required": ["streetAddress", "cityName"]
        }
    },
    "required": ["fullName", "yearsOld", "profession", "location"]
}

# Create ComputeJSON node to translate JSON object to target schema
json_node = ComputeJSON(
    prompt=f"Translate the following JSON object to the target schema.\n{json.dumps(original)}",
    json_schema=target_schema
)

# Create ComputeText nodes using sb.format with futures from the ComputeJSON node
name_node = ComputeText(
    prompt=sb.format("Tell me more about {fullName}", fullName=json_node.future.json_object["fullName"]),
)

age_prompt = sb.format("What are the typical responsibilities of a {profession}", profession=json_node.future.json_object["profession"])

age_node = ComputeText(
    prompt=age_prompt
)

print(age_prompt)

# Example using sb.format with another scenario
story = ComputeText(prompt="tell me a story")
summary = ComputeText(prompt=sb.format("summarize: {story}", story=story.future.text))
