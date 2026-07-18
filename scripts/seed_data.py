import argparse
import json
from pathlib import Path

from backend.anvaya import create_app
from backend.anvaya.services.generator import DEFAULT_SEED, generate, ground_truth_manifest

parser=argparse.ArgumentParser(description="Generate deterministic synthetic ANVAYA data")
parser.add_argument("--scale",choices=("test","full"),default="test")
parser.add_argument("--seed",type=int,default=DEFAULT_SEED)
parser.add_argument("--reset",action="store_true")
args=parser.parse_args()

database=Path("anvaya_local.db")
if args.reset and database.exists(): database.unlink()
app=create_app("development")
counts=generate(app.extensions["repository"],app.config,args.scale,args.seed)
output=Path("data/generated"); output.mkdir(parents=True,exist_ok=True)
(output/"dataset-summary.json").write_text(json.dumps(counts,indent=2,sort_keys=True),encoding="utf-8")
(output/"ground-truth-manifest.json").write_text(json.dumps(ground_truth_manifest(),indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(counts,indent=2,sort_keys=True))
app.extensions["repository"].close()
