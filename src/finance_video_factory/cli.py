from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from finance_video_factory.manual import ManualActionRequired
from finance_video_factory.pipeline import FinanceVideoPipeline
from finance_video_factory.utils import load_yaml


def _latest_workspace(root: Path) -> Path:
    candidates = sorted((x for x in root.glob("*") if x.is_dir()), reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No workspace runs found under {root}")
    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a finance-news YouTube video using manual ChatGPT responses"
    )
    parser.add_argument("--config", default="config/settings.yaml")
    parser.add_argument(
        "--resume",
        nargs="?",
        const="latest",
        metavar="WORKSPACE",
        help="Resume a workspace. Omit the path to resume the latest run.",
    )
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    project_dir = Path(__file__).resolve().parents[2]
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_dir / config_path
    settings = load_yaml(config_path)
    root = Path(settings["project"]["workspace_root"])
    if not root.is_absolute():
        root = project_dir / root
    root.mkdir(parents=True, exist_ok=True)

    workspace = None
    if args.resume:
        workspace = _latest_workspace(root) if args.resume == "latest" else Path(args.resume)
        if not workspace.is_absolute():
            workspace = (project_dir / workspace).resolve()
        if not workspace.exists():
            parser.error(f"Workspace does not exist: {workspace}")

    pipeline = FinanceVideoPipeline(settings, root, project_dir)
    try:
        pipeline.run(upload=args.upload, workspace=workspace)
    except ManualActionRequired as action:
        print("\nMANUAL CHATGPT ACTION REQUIRED")
        print("=" * 31)
        print(f"Stage: {action.stage}")
        print(f"\n1. Open and copy this prompt:\n   {action.prompt_path}")
        print("\n2. Paste it into ChatGPT.")
        print(f"\n3. Save ChatGPT's JSON response here:\n   {action.response_path}")
        print("\n4. Resume with:")
        print(f'   python main.py --resume "{action.workspace}"')
        print("\nChatGPT must return plain JSON. Markdown ```json fences are also accepted and removed automatically.")
    except ValueError as exc:
        print(f"\nVALIDATION ERROR\n{exc}")
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
