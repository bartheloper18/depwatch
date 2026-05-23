"""CLI sub-command: manage project tags."""

from __future__ import annotations

import argparse
from pathlib import Path

from depwatch.tagger import (
    add_tag,
    filter_results_by_tag,
    load_tags,
    remove_tag,
    save_tags,
    tags_for,
)

_DEFAULT_TAG_FILE = Path(".depwatch_tags.json")


def add_tagger_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("tag", help="Manage project tags")
    p.add_argument("--tag-file", default=str(_DEFAULT_TAG_FILE), help="Tag store path")
    sub = p.add_subparsers(dest="tag_action", required=True)

    add_p = sub.add_parser("add", help="Add a tag to a project")
    add_p.add_argument("project", help="Project name")
    add_p.add_argument("tag", help="Tag to add")

    rm_p = sub.add_parser("remove", help="Remove a tag from a project")
    rm_p.add_argument("project", help="Project name")
    rm_p.add_argument("tag", help="Tag to remove")

    ls_p = sub.add_parser("list", help="List tags for a project")
    ls_p.add_argument("project", help="Project name")

    p.set_defaults(func=_cmd_tagger)


def _cmd_tagger(args: argparse.Namespace) -> None:
    tag_file = Path(args.tag_file)
    store = load_tags(tag_file)

    if args.tag_action == "add":
        store = add_tag(store, args.project, args.tag)
        save_tags(tag_file, store)
        print(f"Added tag '{args.tag}' to project '{args.project}'.")

    elif args.tag_action == "remove":
        store = remove_tag(store, args.project, args.tag)
        save_tags(tag_file, store)
        print(f"Removed tag '{args.tag}' from project '{args.project}'.")

    elif args.tag_action == "list":
        tags = tags_for(store, args.project)
        if tags:
            print("\n".join(tags))
        else:
            print(f"No tags for project '{args.project}'.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-tag", description="Manage project tags")
    subparsers = parser.add_subparsers(dest="tag_action", required=True)
    add_p = subparsers.add_parser("add")
    add_p.add_argument("project")
    add_p.add_argument("tag")
    rm_p = subparsers.add_parser("remove")
    rm_p.add_argument("project")
    rm_p.add_argument("tag")
    ls_p = subparsers.add_parser("list")
    ls_p.add_argument("project")
    parser.add_argument("--tag-file", default=str(_DEFAULT_TAG_FILE))
    args = parser.parse_args()
    _cmd_tagger(args)


if __name__ == "__main__":
    main()
