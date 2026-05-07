#!/usr/bin/env python3
"""
Convert JPG/JPEG/PNG files to WebP, update references, and delete originals.

Usage examples:
  python3 scripts/optimize_images.py --dry-run
  python3 scripts/optimize_images.py
  python3 scripts/optimize_images.py --keep-originals --no-update-refs
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import shutil
import subprocess
import sys
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
TEXT_EXTENSIONS = {
    ".html",
    ".css",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".md",
}
EXCLUDED_DIRS = {".git", "node_modules"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert images to WebP and update project references."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files.",
    )
    parser.add_argument(
        "--keep-originals",
        action="store_true",
        help="Keep original JPG/JPEG/PNG files after WebP conversion.",
    )
    parser.add_argument(
        "--no-update-refs",
        action="store_true",
        help="Skip rewriting references in HTML/CSS/JS/etc.",
    )
    parser.add_argument(
        "--image-quality",
        type=int,
        default=78,
        help="WebP quality for images (0-100, default: 78).",
    )
    parser.add_argument(
        "--video-crf",
        type=int,
        default=28,
        help="Video CRF for ffmpeg re-encode (lower = better quality, default: 28).",
    )
    parser.add_argument(
        "--video-max-width",
        type=int,
        default=1280,
        help="Downscale videos wider than this width (default: 1280).",
    )
    return parser.parse_args()


def is_excluded(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRS for part in rel_parts)


def iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if is_excluded(path, root):
            continue
        yield path


def load_pillow_image_module(root: Path):
    local_deps = root / ".pydeps"
    if local_deps.exists():
        local_deps_str = str(local_deps)
        if local_deps_str not in sys.path:
            sys.path.insert(0, local_deps_str)
    try:
        image_module = importlib.import_module("PIL.Image")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Pillow is required for image optimization.\n"
            "Install it with:\n"
            "python3 -m pip install pillow --target .pydeps"
        ) from error
    return image_module


def convert_image_to_webp(src: Path, dst: Path, quality: int, dry_run: bool, image_module) -> bool:
    if dry_run:
        print(f"[dry-run] convert image: {src} -> {dst} (quality={quality})")
        return True

    try:
        with image_module.open(src) as image:
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            image.save(dst, format="WEBP", quality=quality, method=6)
        return True
    except Exception as error:
        print(f"[warn] failed to convert image {src}: {error}")
        return False


def convert_video_with_ffmpeg(
    src: Path, dst: Path, crf: int, max_width: int, dry_run: bool
) -> bool:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        print(f"[warn] ffmpeg not found; skipping video: {src}")
        return False

    filter_expr = (
        f"scale='if(gt(iw,{max_width}),{max_width},iw)':-2"
    )
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(src),
        "-vf",
        filter_expr,
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        str(crf),
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-movflags",
        "+faststart",
        str(dst),
    ]

    if dry_run:
        print("[dry-run] " + " ".join(command))
        return True

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(
            f"[warn] failed to optimize video {src}:\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        return False
    return True


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        while True:
            chunk = file_obj.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def replace_references(root: Path, mapping: dict[str, str], dry_run: bool) -> int:
    updated_files = 0
    for text_file in iter_files(root):
        if text_file.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        content = text_file.read_text(encoding="utf-8")
        original_content = content
        for old_rel, new_rel in mapping.items():
            if old_rel in content:
                content = content.replace(old_rel, new_rel)
        if content == original_content:
            continue
        updated_files += 1
        if dry_run:
            print(f"[dry-run] update refs: {text_file.relative_to(root)}")
        else:
            text_file.write_text(content, encoding="utf-8")
    return updated_files


def choose_output_path(src: Path, reserved_targets: set[Path], existing_webps: set[Path]) -> Path:
    base_candidate = src.with_suffix(".webp")
    candidate = base_candidate
    suffix_tag = src.suffix.lstrip(".").lower()

    if candidate in reserved_targets or candidate in existing_webps:
        candidate = src.with_name(f"{src.stem}-{suffix_tag}.webp")

    counter = 2
    while candidate in reserved_targets or candidate in existing_webps:
        candidate = src.with_name(f"{src.stem}-{suffix_tag}-{counter}.webp")
        counter += 1

    reserved_targets.add(candidate)
    return candidate


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    delete_originals = not args.keep_originals

    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root directory does not exist or is not a directory: {root}")

    image_files = sorted(
        [p for p in iter_files(root) if p.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda p: p.as_posix(),
    )
    video_files = sorted(
        [p for p in iter_files(root) if p.suffix.lower() in VIDEO_EXTENSIONS],
        key=lambda p: p.as_posix(),
    )

    if not image_files and not video_files:
        print("No image/video files found.")
        return 0

    image_module = load_pillow_image_module(root) if image_files else None

    existing_webps = {p for p in iter_files(root) if p.suffix.lower() == ".webp"}
    existing_mp4 = {p for p in iter_files(root) if p.suffix.lower() == ".mp4"}
    reserved_targets: set[Path] = set()
    reserved_video_targets: set[Path] = set()

    converted = 0
    video_converted = 0
    deleted = 0
    deduped = 0
    failed_images = 0
    failed_videos = 0
    mapping: dict[str, str] = {}
    canonical_by_folder_hash: dict[tuple[Path, str], Path] = {}
    file_hash_cache: dict[Path, str] = {}

    for src in image_files:
        src_hash = file_hash_cache.get(src)
        if src_hash is None:
            src_hash = hash_file(src)
            file_hash_cache[src] = src_hash

        dedupe_key = (src.parent, src_hash)
        existing_canonical = canonical_by_folder_hash.get(dedupe_key)
        if existing_canonical is not None:
            old_rel = src.relative_to(root).as_posix()
            canonical_rel = existing_canonical.relative_to(root).as_posix()
            mapping[old_rel] = canonical_rel
            deduped += 1
            if args.dry_run:
                print(
                    f"[dry-run] dedupe same-image in folder: {old_rel} -> {canonical_rel}"
                )
            if delete_originals:
                if args.dry_run:
                    print(f"[dry-run] delete duplicate original: {old_rel}")
                else:
                    src.unlink()
                deleted += 1
            continue

        dst = choose_output_path(src, reserved_targets, existing_webps)
        conversion_ok = convert_image_to_webp(
            src,
            dst,
            quality=max(0, min(100, args.image_quality)),
            dry_run=args.dry_run,
            image_module=image_module,
        )
        if not conversion_ok:
            failed_images += 1
            continue
        converted += 1

        old_rel = src.relative_to(root).as_posix()
        new_rel = dst.relative_to(root).as_posix()
        mapping[old_rel] = new_rel
        canonical_by_folder_hash[dedupe_key] = dst

        if delete_originals:
            if args.dry_run:
                print(f"[dry-run] delete original: {old_rel}")
            else:
                src.unlink()
            deleted += 1

    for src in video_files:
        if src.stat().st_size == 0:
            print(f"[warn] skipping zero-byte video: {src.relative_to(root)}")
            continue

        candidate = src.with_name(f"{src.stem}.optimized.mp4")
        if candidate in reserved_video_targets or candidate in existing_mp4:
            counter = 2
            while True:
                candidate = src.with_name(f"{src.stem}.optimized-{counter}.mp4")
                if candidate not in reserved_video_targets and candidate not in existing_mp4:
                    break
                counter += 1
        reserved_video_targets.add(candidate)

        ok = convert_video_with_ffmpeg(
            src,
            candidate,
            crf=args.video_crf,
            max_width=args.video_max_width,
            dry_run=args.dry_run,
        )
        if not ok:
            failed_videos += 1
            continue

        old_rel = src.relative_to(root).as_posix()
        new_rel = candidate.relative_to(root).as_posix()
        mapping[old_rel] = new_rel
        video_converted += 1

        if delete_originals:
            if args.dry_run:
                print(f"[dry-run] delete original video: {old_rel}")
            else:
                src.unlink()
            deleted += 1

    updated_files = 0
    if not args.no_update_refs:
        updated_files = replace_references(root, mapping, args.dry_run)

    print(
        "Done. "
        f"Images converted: {converted}, "
        f"Videos converted: {video_converted}, "
        f"Same-image duplicates collapsed: {deduped}, "
        f"Image conversion failures: {failed_images}, "
        f"Video conversion failures/skips: {failed_videos}, "
        f"Originals deleted: {deleted if delete_originals else 0}, "
        f"Reference files updated: {updated_files}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
