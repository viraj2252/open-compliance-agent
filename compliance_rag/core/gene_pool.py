import json
import os
import logging
from typing import Dict
from compliance_rag.core.sop import ComplianceSOP
from compliance_rag.core.defaults import get_baseline_sop
from compliance_rag.config import DATA_DIR

logger = logging.getLogger("compliance_rag.gene_pool")

SOP_DB_PATH = os.path.join(DATA_DIR, "sop_gene_pool.json")


class SOPGenePool:
    """
    Manages the evolution of Compliance SOPs.
    Acts as a persistent store for different versions of the agent's 'genome'.
    """
    def __init__(self):
        self.sops: Dict[str, ComplianceSOP] = {}
        self.load_db()
    
    def load_db(self):
        """Loads SOP history from disk or initializes baseline."""
        if os.path.exists(SOP_DB_PATH):
            try:
                with open(SOP_DB_PATH, "r") as f:
                    data = json.load(f)
                    for version, sop_data in data.items():
                        self.sops[version] = ComplianceSOP(**sop_data)
                logger.info(f"Loaded {len(self.sops)} SOP generations from disk.")
            except Exception as e:
                logger.error(f"Error loading SOP DB: {e}. Starting fresh.")
                self._init_baseline()
        else:
            self._init_baseline()
            
    def _init_baseline(self):
        """Creates the v0 baseline from defaults."""
        logger.info("Initializing new SOP Gene Pool with Baseline v0.")
        baseline = get_baseline_sop()
        self.add_sop("v0", baseline)

    def add_sop(self, version: str, sop: ComplianceSOP):
        """Persists a new SOP version."""
        self.sops[version] = sop
        self.save_db()
        logger.info(f"Added SOP version {version} to Gene Pool.")

    def get_sop(self, version: str) -> ComplianceSOP:
        return self.sops.get(version)

    def get_latest_sop(self) -> ComplianceSOP:
        """Returns the most recent SOP version."""
        try:
            versions = sorted(
                self.sops.keys(), 
                key=lambda x: int(x[1:]) if x.startswith("v") and x[1:].isdigit() else 0
            )
            return self.sops[versions[-1]]
        except Exception:
            return self.sops.get("v0")

    def get_latest_version_id(self) -> str:
        """Returns the version ID of the latest SOP."""
        try:
            versions = sorted(
                self.sops.keys(),
                key=lambda x: int(x[1:]) if x.startswith("v") and x[1:].isdigit() else 0
            )
            return versions[-1]
        except Exception:
            return "v0"

    def save_db(self):
        """Saves all SOPs to JSON."""
        data = {}
        for v, sop in self.sops.items():
            if hasattr(sop, "model_dump"):
                data[v] = sop.model_dump()
            else:
                data[v] = sop.dict()
                
        with open(SOP_DB_PATH, "w") as f:
            json.dump(data, f, indent=2)
