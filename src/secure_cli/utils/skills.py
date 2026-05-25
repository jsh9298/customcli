import os
import yaml
import json
import logging
from typing import Dict, List, Optional, Any

class SkillManager:
    """Agent Skills (특화된 프롬프트 및 도구 세트)를 관리하는 클래스."""
    
    def __init__(self, skill_dir: str):
        self.skill_dir = skill_dir
        self.logger = logging.getLogger("SkillManager")
        if not os.path.exists(self.skill_dir):
            os.makedirs(self.skill_dir)

    def list_skills(self) -> List[str]:
        return [f.split('.')[0] for f in os.listdir(self.skill_dir) if f.endswith(('.yaml', '.json'))]

    def load_skill(self, name: str) -> Optional[Dict[str, Any]]:
        for ext in ['.yaml', '.json']:
            path = os.path.join(self.skill_dir, f"{name}{ext}")
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        return yaml.safe_load(f) if ext == '.yaml' else json.load(f)
                except Exception as e:
                    self.logger.error(f"Error loading skill {name}: {e}")
        return None

    def save_skill(self, name: str, skill_data: Dict[str, Any]):
        path = os.path.join(self.skill_dir, f"{name}.yaml")
        try:
            with open(path, 'w') as f:
                yaml.dump(skill_data, f)
            return True
        except Exception as e:
            self.logger.error(f"Error saving skill {name}: {e}")
            return False
