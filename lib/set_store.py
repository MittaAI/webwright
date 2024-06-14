import json
import os

class SetStore:
    def __init__(self, storage_path='set_store.json'):
        self.set_dict = {}
        self.storage_path = storage_path
        self.load()

    def add(self, key, values):
        """Add values to a set."""
        if key not in self.set_dict:
            self.set_dict[key] = set()
        if isinstance(values, (str, int)):
            values = [values]
        self.set_dict[key].update(values)
        self.save()

    def remove(self, key, values):
        """Remove values from a set."""
        if key in self.set_dict:
            if isinstance(values, (str, int)):
                values = [values]
            self.set_dict[key].difference_update(values)
            if not self.set_dict[key]:
                del self.set_dict[key]
            self.save()

    def get(self, key):
        """Get values from a set."""
        return self.set_dict.get(key, set())

    def contains(self, key, value):
        """Check if a value exists in a set."""
        return value in self.set_dict.get(key, set())

    def union(self, key1, key2):
        """Perform union operation on two sets."""
        set1 = self.set_dict.get(key1, set())
        set2 = self.set_dict.get(key2, set())
        return set1.union(set2)

    def intersection(self, key1, key2):
        """Perform intersection operation on two sets."""
        set1 = self.set_dict.get(key1, set())
        set2 = self.set_dict.get(key2, set())
        return set1.intersection(set2)

    def difference(self, key1, key2):
        """Perform difference operation on two sets."""
        set1 = self.set_dict.get(key1, set())
        set2 = self.set_dict.get(key2, set())
        return set1.difference(set2)

    def tanimoto(self, key1, key2):
        """Calculate the Tanimoto coefficient between two sets."""
        set1 = self.set_dict.get(key1, set())
        set2 = self.set_dict.get(key2, set())
        intersection_size = len(set1.intersection(set2))
        union_size = len(set1.union(set2))
        if union_size == 0:
            return 0.0
        return intersection_size / union_size

    def save(self):
        """Persist the set store to a JSON file."""
        serializable_dict = {k: list(v) for k, v in self.set_dict.items()}
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_dict, f, ensure_ascii=False, indent=4)

    def load(self):
        """Load the set store from a JSON file."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                serializable_dict = json.load(f)
                self.set_dict = {k: set(v) for k, v in serializable_dict.items()}