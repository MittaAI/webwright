from typing import Any, Dict, Optional, Type
from substrate import Substrate, ComputeText, ComputeJSON, sb
from typing import Any, Dict, Optional, Type, List, Tuple
from lib.config import Config
import json
import re
import hashlib

class SubstrateComputationManager:
    COMPUTE_TEXT_MODELS = [
        "Mixtral8x7BInstruct", "Llama3Instruct8B", "Llama3Instruct70B",
        "Llama3Instruct405B", "Firellava13B", "gpt-4o", "gpt-4o-mini",
        "claude-3-5-sonnet-20240620"
    ]
    COMPUTE_JSON_MODELS = ["Mixtral8x7BInstruct", "Llama3Instruct8B"]
    DEFAULT_MODEL = "Llama3Instruct8B"

    def __init__(self):
        print("Initializing SubstrateComputationManager...")
        self.config = Config()  # Load configuration
        self.substrate = self.initialize_substrate()
        self.node_registry: Dict[str, Dict[str, Any]] = {}
        print("SubstrateComputationManager initialized.")

    def initialize_substrate(self) -> Substrate:
        print("Retrieving Substrate API token...")
        token_result = self.config.get_substrate_token()
        if token_result["error"]:
            print(f"Failed to get Substrate token: {token_result['error']}")
            raise ValueError(f"Failed to get Substrate token: {token_result['error']}")
        print("Substrate API token retrieved successfully.")
        print("Initializing Substrate instance...")
        substrate_instance = Substrate(api_key=token_result["token"])
        print("Substrate instance created.")
        return substrate_instance

    def validate_model(self, model: str, node_type: Type) -> str:
        """Validate the model based on the node type and return the appropriate model."""
        print(f"Validating model '{model}' for node type '{node_type.__name__}'")
        if node_type == ComputeText:
            valid_models = self.COMPUTE_TEXT_MODELS
        elif node_type == ComputeJSON:
            valid_models = self.COMPUTE_JSON_MODELS
        else:
            raise ValueError(f"Unsupported node type: {node_type}")

        if model not in valid_models:
            print(f"Warning: Invalid model '{model}' for {node_type.__name__}. Using default model '{self.DEFAULT_MODEL}'.")
            return self.DEFAULT_MODEL
        return model

    def extract_placeholders(self, prompt: str) -> List[str]:
        print(f"Extracting placeholders from prompt: {prompt}")
        placeholders = re.findall(r'\{([^{}]+)\}', prompt)
        root_placeholders = [p.split('.')[0] for p in placeholders]
        all_placeholders = list(set(placeholders + root_placeholders))
        print(f"Placeholders extracted: {all_placeholders}")
        return all_placeholders

    def extract_json_examples(self, prompt: str) -> Tuple[str, Dict[str, str]]:
        json_examples = {}
        def replace_json(match):
            json_content = match.group(1)
            content_hash = hashlib.md5(json_content.encode()).hexdigest()[:8]
            placeholder = f'<<<JSON_EXAMPLE_{content_hash}>>>'
            json_examples[placeholder] = json_content
            return placeholder
        
        cleaned_prompt = re.sub(r'```json\s*([\s\S]*?)```', replace_json, prompt)
        return cleaned_prompt, json_examples

    def get_node_output(self, node_info: Dict[str, Any], key_path: Optional[str] = None) -> str:
        node = node_info["node"]
        node_type = node_info["type"]

        if node_type == ComputeText:
            return f"{node.future.text}"
        elif node_type == ComputeJSON:
            if key_path:
                return f"{node.future.json_object}.get('{key_path}')"
            else:
                return f"{node.future.json_object}"
        else:
            raise ValueError("Unsupported node type or output format.")

    def create_node(self, prompt: str, model: str, node_type: Type = ComputeText, node_name: Optional[str] = None, json_schema: Optional[Dict] = None) -> None:
        print(f"Creating a node with prompt: {prompt}, model: {model}, and type: {node_type.__name__}")

        if not node_name:
            raise ValueError("A node_name must be provided to create and reference nodes.")
        
        # Validate the model
        validated_model = self.validate_model(model, node_type)
        
        # Extract JSON examples
        cleaned_prompt, json_examples = self.extract_json_examples(prompt)
        
        # Extract placeholders from the cleaned prompt
        placeholders = self.extract_placeholders(cleaned_prompt)
        print(f"Placeholders found: {placeholders}")
        
        # Create a mapping from placeholders to the appropriate output
        format_kwargs = {}
        for placeholder in placeholders:
            parts = placeholder.split('.')
            root_placeholder = parts[0]
            
            if root_placeholder in self.node_registry:
                node_info = self.node_registry[root_placeholder]
                try:
                    if len(parts) > 1:
                        # Nested attribute
                        format_kwargs[placeholder] = self.get_node_output(node_info, '.'.join(parts[1:]))
                    else:
                        # Root placeholder
                        format_kwargs[placeholder] = self.get_node_output(node_info)
                    print(f"Mapping placeholder '{placeholder}' to {format_kwargs[placeholder]}")
                except Exception as e:
                    print(f"Error retrieving output for placeholder '{placeholder}': {str(e)}")
                    raise ValueError(f"Error processing placeholder '{placeholder}': {str(e)}")
            else:
                raise ValueError(f"Placeholder '{root_placeholder}' not found in node registry.")
        
        # Now, add JSON examples back to the cleaned prompt
        for placeholder, json_content in json_examples.items():
            cleaned_prompt = cleaned_prompt.replace(f'"{placeholder}"', f'```json\n{json_content}\n```')
        
        # Finally, format the cleaned prompt using sb.format with the extracted placeholders
        try:
            formatted_prompt = sb.format(cleaned_prompt, **format_kwargs)
            print(f"Formatted prompt: {formatted_prompt}")
        except Exception as e:
            print(f"Error formatting prompt: {str(e)}")
            raise ValueError(f"Error formatting prompt: {str(e)}")
        
        # Create the node
        if node_type == ComputeText:
            node = ComputeText(prompt=formatted_prompt, model=validated_model)
        elif node_type == ComputeJSON:
            print(f"Creating ComputeJSON node with prompt: {formatted_prompt} and JSON schema: {json_schema}")
            if json_schema is None:
                raise ValueError("JSON schema must be provided for ComputeJSON nodes.")
            node = ComputeJSON(prompt=formatted_prompt, model=validated_model, json_schema=json.dumps(json_schema))
        else:
            raise ValueError("Unsupported node type specified.")

        # Register the node using the node_name
        self.node_registry[node_name] = {"node": node, "type": node_type}
        print(f"Created node with name '{node_name}' and prompt: {formatted_prompt}")




    def run_computation(self, final_node_name: str) -> Any:
        print("Running the computation chain...")
        if final_node_name not in self.node_registry:
            raise ValueError(f"Node '{final_node_name}' not found in node registry.")
        
        final_node = self.node_registry[final_node_name]["node"]
        try:
            response = self.substrate.run(final_node)
            print(f"Computation response received: {response}")
            
            # Print out the full response for inspection
            print("Full Response Content:")
            print(response)

            # Check if the response includes errors or missing nodes
            if not response:
                print("Response is empty or not as expected.")
            
            return response
        except Exception as e:
            print(f"Error during computation: {e}")
        raise
