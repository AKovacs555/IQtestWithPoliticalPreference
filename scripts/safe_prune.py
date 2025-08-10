import argparse
import json
import pathlib
import subprocess
MUST_KEEP = {
    'frontend','backend','e2e','tests','docs','static','tools','.github',
    'render.yaml','vercel.json','Makefile','requirements.txt','.env.example',
    'questions','translations'
}

def referenced(path: str) -> bool:
    name = pathlib.Path(path).name
    try:
        res = subprocess.run(['git','grep','-n',name], capture_output=True, text=True)
        return bool(res.stdout.strip())
    except Exception:
        return True

def load_evidence():
    # ensure evidence files exist
    for fname in ['depcheck.json','ts-prune.txt','ts-unused-exports.txt','ruff_unused.json','vulture.txt']:
        pathlib.Path(fname).touch(exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    load_evidence()
    candidates = json.load(open('scripts/prune_frontend_candidates.json'))
    plan_lines = ['| path | reason | evidence |','|---|---|---|']
    to_remove = []
    for c in candidates:
        path = c['path']
        if any(path == mk or path.startswith(mk + '/') for mk in MUST_KEEP):
            continue
        if referenced(path):
            continue
        to_remove.append(c)
        plan_lines.append(f"| {path} | {c['reason']} | {'; '.join(c['evidence'])} |")
    plan_text = '\n'.join(plan_lines) + '\n'
    pathlib.Path('prune_plan.md').write_text(plan_text)
    if args.dry_run:
        print(plan_text)
    if args.apply:
        for c in to_remove:
            subprocess.run(['git','rm','-r',c['path']])
        print(plan_text)

if __name__ == '__main__':
    main()
