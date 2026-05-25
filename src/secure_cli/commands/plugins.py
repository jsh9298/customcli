import os
import json
import yaml
import logging
from typing import Dict, List, Any

class PluginManager:
    """Loads and manages external command plugins and tool hooks."""
    
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, dict] = {}
        self.hooks: Dict[str, List[callable]] = {"pre_tool": [], "post_tool": []}
        self.logger = logging.getLogger("Plugins")
        
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)

    def load_plugins(self):
        """Discovers and loads JSON/TOML/YAML plugins from the plugin directory."""
        self.plugins.clear()
        for f in os.listdir(self.plugin_dir):
            if f.endswith(('.json', '.yaml', '.yml')):
                path = os.path.join(self.plugin_dir, f)
                try:
                    with open(path, 'r') as file:
                        data = json.load(file) if f.endswith('.json') else yaml.safe_load(file)
                        if data and 'commands' in data:
                            self.plugins.update(data['commands'])
                            self.logger.info(f"Loaded plugin: {f}")
                except Exception as e:
                    self.logger.error(f"Error loading plugin {f}: {e}")

    def get_plugin_commands(self) -> List[str]:
        return list(self.plugins.keys())

    def execute_plugin_command(self, cmd_name: str) -> Optional[str]:
        """Returns the instruction/template associated with a plugin command."""
        return self.plugins.get(cmd_name, {}).get('instruction')

    def apply_hooks(self, hook_type: str, data: Any) -> Any:
        """Applies registered hooks to the data."""
        for hook in self.hooks.get(hook_type, []):
            try:
                data = hook(data)
            except Exception as e:
                self.logger.error(f"Error in hook {hook_type}: {e}")
        return data
