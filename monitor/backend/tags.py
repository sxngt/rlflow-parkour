"""Versioned research classification. Historical artifacts remain immutable."""
import json
from .store import ROOT

def catalog():
    path=ROOT/'configs/research-tags.json'
    if not path.exists():return {'schema_version':1,'tags':{},'task_defaults':{},'run_overrides':{}}
    return json.loads(path.read_text())

def annotate(item, run_id, config=None, rules=None):
    rules=rules or catalog();config=config or {}
    explicit=item.get('research_tags') or config.get('research_tags')
    tags=rules.get('run_overrides',{}).get(run_id)
    source='registry_override'
    if tags is None:
        tags=explicit;source='run_metadata'
    if not tags:
        tags=rules.get('task_defaults',{}).get(item.get('task') or config.get('task'),[])
        source='task_default' if tags else 'unclassified'
    item['research_tags']=sorted(set(tags))
    item['tag_source']=source
    return item

def matches(item, tags):return all(t in item.get('research_tags',[]) for t in tags)
