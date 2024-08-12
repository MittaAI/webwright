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
        
        print(f"Getting output for node: {node}")
        print(f"Node type: {node_type}")
        print(f"Key path: {key_path}")

        if node_type == ComputeText:
            output = f"{node.future.text}"
            print(f"ComputeText output: {output}")
            return output
        elif node_type == ComputeJSON:
            if key_path:
                output = f"{node.future.json_object}['{key_path}']"
                print(f"ComputeJSON output with key path: {output}")
            else:
                output = f"{node.future.json_object}"
                print(f"ComputeJSON output without key path: {output}")
            return output
        else:
            error_msg = f"Unsupported node type or output format: {node_type}"
            print(f"Error: {error_msg}")
            raise ValueError(error_msg)

    # create node needs both the prompt and the json_schema defined to create the node (schema is not used for computetext)
    """
    ComputeJSON(
    prompt="Who wrote Don Quixote?",
    json_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name of the author.",
            },
            "bio": {
                "type": "string",
                "description": "Concise biography of the author.",
            },
        },
    },
    temperature=0.4,
    max_tokens=800,
    )
    """
    def create_node(self, prompt: str, model: str, node_type: Type = ComputeText, node_name: Optional[str] = None, json_schema: Optional[Dict] = None) -> None:
        print(f"Creating a node with prompt: {prompt}, model: {model}, and type: {node_type.__name__}")

        if not node_name:
            raise ValueError("A node_name must be provided to create and reference nodes.")
        
        validated_model = self.validate_model(model, node_type)
        print(f"Validated model: {validated_model}")
        
        # 1. Extract the example JSON, if present
        cleaned_prompt, json_examples = self.extract_json_examples(prompt)
        print(f"Cleaned prompt after JSON extraction: {cleaned_prompt}")
        print(f"Extracted JSON examples: {json_examples}")

        # 2. Extract the placeholders from the cleaned version
        placeholders = self.extract_placeholders(cleaned_prompt)
        print(f"Placeholders extracted from cleaned prompt: {placeholders}")


        # 3. Put the example JSON back into the cleaned prompt
        for placeholder, json_content in json_examples.items():
            # Double the curly braces in the JSON content to encode it
            encoded_json = json_content.replace("{", "{{").replace("}", "}}")
            cleaned_prompt = cleaned_prompt.replace(placeholder, f"```json\n{encoded_json}\n```")
        print(f"Prompt after reinserting encoded JSON examples: {cleaned_prompt}")

        # 4. Extract the placeholders and deal with nested attributes
        nested_placeholders = {}
        for placeholder in placeholders:
            if '.' in placeholder:
                parts = placeholder.split('.')
                root = parts[0]
                if root not in nested_placeholders:
                    nested_placeholders[root] = []
                nested_placeholders[root].append('.'.join(parts[1:]))
        print(f"Nested placeholders: {nested_placeholders}")

        # 5. Validate all placeholders (including root placeholders) against the node registry
        all_roots = set(nested_placeholders.keys())
        print(all_roots)
        for root in all_roots:
            print(root)
            print(self.node_registry)
            if root not in self.node_registry:
                raise ValueError(f"Placeholder '{root}' not found in node registry.")
        print("All placeholders validated successfully.")

        # 5. Replace the nested attributes in the prompt with _ instead of dot notation
        for root, nested_attrs in nested_placeholders.items():
            for attr in nested_attrs:
                old_placeholder = f"{{{root}.{attr}}}"
                new_placeholder = f"{{{root}_{attr.replace('.', '_')}}}"
                cleaned_prompt = cleaned_prompt.replace(old_placeholder, new_placeholder)
                print(f"Replaced {old_placeholder} with {new_placeholder}")

        # 6. Prepare the sb_format_args
        sb_format_args = {}
        for root in all_roots:
            node_info = self.node_registry[root]
            if root in nested_placeholders:
                for attr in nested_placeholders[root]:
                    old_placeholder = f"{{{root}.{attr}}}"
                    new_placeholder = f"{{{root}_{attr.replace('.', '_')}}}"
                    cleaned_prompt = cleaned_prompt.replace(old_placeholder, new_placeholder)
                    sb_format_args[f"{root}_{attr.replace('.', '_')}"] = f"{node_info['node'].future.json_object}"
            else:
                sb_format_args[root] = node_info["node"].future.text if isinstance(node_info["node"], ComputeText) else node_info["node"].future.json_object

        print(f"sb_format_args: {sb_format_args}")

        # Print the sb.format() call representation
        sb_format_repr = f"sb.format(\n    \"\"\"{cleaned_prompt}\"\"\",\n"
        for key, value in sb_format_args.items():
            sb_format_repr += f"    {key}={value},\n"
        sb_format_repr += ")"
        print(f"Equivalent sb.format() call:\n{sb_format_repr}")

        # 7. Keep in mind the assignment will still use the json_object access
        formatted_prompt = sb.format(cleaned_prompt, **sb_format_args)
        print(f"Formatted prompt: {formatted_prompt}")
        
        if node_type == ComputeText:
            node = ComputeText(prompt=formatted_prompt, model=validated_model)
        elif node_type == ComputeJSON:
            if json_schema is None:
                raise ValueError("JSON schema must be provided for ComputeJSON nodes.")
            node = ComputeJSON(prompt=formatted_prompt, model=validated_model, json_schema=json_schema)
        else:
            raise ValueError("Unsupported node type specified.")

        self.node_registry[node_name] = {"node": node, "type": node_type}
        print(f"Created node with name '{node_name}' and prompt: {formatted_prompt}")


    def run_computation(self, final_node_name: str) -> Dict[str, Any]:
        print(f"Running the computation chain for final node: {final_node_name}")
        if final_node_name not in self.node_registry:
            raise ValueError(f"Node '{final_node_name}' not found in node registry.")
        
        final_node = self.node_registry[final_node_name]["node"]
        print(f"Retrieved final node: {final_node_name} with type {type(final_node).__name__}")
        
        try:
            response = self.substrate.run(final_node)
            print(f"Computation response received for {final_node_name}")
            
            results = {}
            for node_name, node_info in self.node_registry.items():
                node = node_info["node"]
                node_type = type(node).__name__
                print(f"Retrieving result for node: {node_name} of type {node_type}")
                
                try:
                    node_response = response.get(node)
                    if isinstance(node, ComputeText):
                        results[node_name] = {
                            "type": "text",
                            "content": node_response.text
                        }
                    elif isinstance(node, ComputeJSON):
                        try:
                            json_content = node_response.json()
                            if isinstance(json_content, str):
                                json_content = json.loads(json_content)
                        except Exception as json_error:
                            print(f"Error converting JSON for node {node_name}: {str(json_error)}")
                            json_content = str(node_response)
                        
                        results[node_name] = {
                            "type": "json",
                            "content": json_content
                        }
                    else:
                        results[node_name] = {
                            "type": "unknown",
                            "content": str(node_response)
                        }
                    print(f"Successfully retrieved result for node: {node_name}")
                except Exception as e:
                    print(f"Error retrieving result for node {node_name}: {str(e)}")
                    results[node_name] = {
                        "type": "error",
                        "content": str(e)
                    }

            print("\nResults summary:")
            for node_name, result in results.items():
                result_type = result["type"]
                content = result["content"]
                if result_type != "error":
                    content_preview = json.dumps(content)[:1000] + "..." if len(json.dumps(content)) > 1000 else json.dumps(content)
                    print(f"{node_name} ({result_type}): {content_preview}")
                else:
                    print(f"{node_name} (error): {content}")

            return results

        except Exception as e:
            print(f"Error during computation: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {str(e)}")
            raise
