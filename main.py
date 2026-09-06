import os
import sys
import argparse
from pathlib import Path
from typing import Optional, List

# Ensure Windows UTF-8 terminal handling
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from features import default_registry, SocialMediaDownloader


def run_convert(args: argparse.Namespace) -> int:
    """
    Execute batch or single-file conversion in Current Working Directory (CWD).
    """
    cwd = Path.cwd()

    # Determine source and target from positional args or flags
    pos_args: List[str] = [a for a in (args.args or []) if a.lower() != "to"]

    source_spec: Optional[str] = args.input
    target_spec: Optional[str] = args.to

    if not target_spec:
        if len(pos_args) == 1:
            target_spec = pos_args[0]
        elif len(pos_args) >= 2:
            source_spec = pos_args[0]
            target_spec = pos_args[1]

    if not target_spec:
        print("[!] Target format is required.")
        print("    Usage: afeat cvt <target_format>              (converts all matching files)")
        print("       or: afeat cvt <source_ext> <target_format> (converts matching extension)")
        print("       or: afeat cvt <file_name> <target_format>  (converts specific file)")
        return 1

    target_ext = target_spec.lower().lstrip(".")

    # Determine destination directory
    output_dir = Path(args.output) if args.output else cwd
    output_dir.mkdir(parents=True, exist_ok=True)

    # Mode A: Specific single file provided
    if source_spec and (cwd / source_spec).is_file():
        target_files = [cwd / source_spec]
    elif source_spec and Path(source_spec).is_file():
        target_files = [Path(source_spec)]
    else:
        # Mode B: Extension filter or all compatible files in CWD
        pattern = f"*.{source_spec.lstrip('.')}" if source_spec else "*"
        search_method = cwd.rglob if args.recursive else cwd.glob
        all_candidates = [p for p in search_method(pattern) if p.is_file()]

        # Filter candidates by compatibility with target_ext
        target_files = []
        for p in all_candidates:
            src_ext = p.suffix.lower().lstrip(".")
            if src_ext and src_ext != target_ext:
                conv = default_registry.get_converter(src_ext, target_ext)
                if conv:
                    target_files.append(p)

    if not target_files:
        if source_spec:
            print(f"[!] No files matching '{source_spec}' found in: {cwd}")
        else:
            print(f"[!] No files convertible to '.{target_ext}' found in: {cwd}")
        return 0

    print(f"[*] Found {len(target_files)} file(s) to convert to '.{target_ext}' in: {cwd}")
    success_count = 0
    fail_count = 0

    for src_file in target_files:
        src_ext = src_file.suffix.lower().lstrip(".")
        conv = default_registry.get_converter(src_ext, target_ext)

        if not conv:
            print(f"[-] Skipped {src_file.name}: no converter for .{src_ext} -> .{target_ext}")
            fail_count += 1
            continue

        # Determine target file path
        if output_dir == cwd:
            dest_file = src_file.with_suffix(f".{target_ext}")
        else:
            dest_file = output_dir / f"{src_file.stem}.{target_ext}"

        # Prevent overwriting same file
        if dest_file.resolve() == src_file.resolve():
            dest_file = dest_file.with_name(f"{src_file.stem}_converted.{target_ext}")

        print(f"  -> Converting: {src_file.name} -> {dest_file.name} ...", end=" ", flush=True)

        ok = conv.convert(
            source_path=src_file,
            target_path=dest_file,
            quality=args.quality,
        )

        if ok:
            print("[OK]")
            success_count += 1
            if args.delete_source and dest_file.exists() and dest_file.resolve() != src_file.resolve():
                try:
                    src_file.unlink()
                    print(f"     [Deleted original: {src_file.name}]")
                except Exception as e:
                    print(f"     [!] Could not delete {src_file.name}: {e}")
        else:
            print("[FAILED]")
            fail_count += 1

    print("=" * 60)
    print(f"[+] Finished: {success_count} succeeded, {fail_count} failed.")
    print(f"[*] Output directory: {output_dir}")
    return 0 if fail_count == 0 else 1


def run_vid(args: argparse.Namespace) -> int:
    """Download social media media directly to Current Working Directory (CWD)."""
    cwd = Path.cwd()
    output_dir = Path(args.output) if args.output else cwd

    downloader = SocialMediaDownloader(target_dir=output_dir)
    ok = downloader.download(
        url=args.url,
        is_audio=args.audio,
        media_format=args.format,
        quality=args.quality,
    )
    return 0 if ok else 1


def run_info(args: argparse.Namespace) -> int:
    """Inspect and summarize files in CWD."""
    cwd = Path.cwd()
    print(f"\n[*] Current Directory: {cwd}")
    print("=" * 60)

    counts = {}
    sizes = {}
    total_files = 0
    total_bytes = 0

    for p in cwd.iterdir():
        if p.is_file():
            ext = p.suffix.lower() or "(no ext)"
            counts[ext] = counts.get(ext, 0) + 1
            sz = p.stat().st_size
            sizes[ext] = sizes.get(ext, 0) + sz
            total_files += 1
            total_bytes += sz

    if total_files == 0:
        print("  Directory is empty.")
        return 0

    print(f"{'Extension':<15} {'Count':<10} {'Total Size'}")
    print("-" * 40)
    for ext, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        sz = sizes[ext]
        for u in ["B", "KB", "MB", "GB"]:
            if sz < 1024:
                sz_str = f"{sz:.1f} {u}"
                break
            sz /= 1024
        else:
            sz_str = f"{sz:.1f} TB"
        print(f"{ext:<15} {cnt:<10} {sz_str}")

    print("-" * 40)
    print(f"Total: {total_files} files")
    return 0


def run_list(args: argparse.Namespace) -> int:
    """Display all supported formats."""
    print("\n" + "=" * 60)
    print(" SUPPORTED FILE CONVERSIONS")
    print("=" * 60)
    summary = default_registry.list_supported_summary()
    for name, info in summary.items():
        print(f"\n[{name}]")
        print(f"  Inputs  : {', '.join(sorted(info['inputs']))}")
        print(f"  Outputs : {', '.join(sorted(info['outputs']))}")
    print("\n" + "=" * 60)
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="afeat",
        description="afeat - Universal Personal CLI Utility & Media/Document Converter",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subcommand: cvt (alias: convert)
    p_convert = subparsers.add_parser("cvt", aliases=["convert"], help="Convert files in Current Working Directory")
    p_convert.add_argument("args", nargs="*", help="[source_ext/file] <target_format>")
    p_convert.add_argument("-i", "--input", help="Specific input file or source extension")
    p_convert.add_argument("-t", "--to", help="Target output format")
    p_convert.add_argument("-q", "--quality", type=int, default=None, help="Quality / bitrate setting (1-100 for images, 64-320 for audio)")
    p_convert.add_argument("-o", "--output", help="Output directory (default: CWD)")
    p_convert.add_argument("-r", "--recursive", action="store_true", help="Process subdirectories recursively")
    p_convert.add_argument("-d", "--delete-source", action="store_true", help="Delete source file after successful conversion")

    # Subcommand: rip (alias: vid - download social media)
    p_vid = subparsers.add_parser("rip", aliases=["vid"], help="Download/rip video or audio from social media URL directly to CWD")
    p_vid.add_argument("url", help="Media URL (YouTube, TikTok, Instagram, Twitter, etc.)")
    p_vid.add_argument("-a", "--audio", action="store_true", help="Extract audio only (MP3)")
    p_vid.add_argument("-f", "--format", help="Target format (mp4, mkv, mp3, m4a)")
    p_vid.add_argument("-q", "--quality", help="Quality (resolution e.g. 1080, or audio bitrate e.g. 320)")
    p_vid.add_argument("-o", "--output", help="Output folder (default: CWD)")

    # Subcommand: info
    subparsers.add_parser("info", help="Show file statistics for Current Working Directory")

    # Subcommand: list
    subparsers.add_parser("list", help="List all supported formats and converters")

    args = parser.parse_args()

    if args.command in ("cvt", "convert"):
        sys.exit(run_convert(args))
    elif args.command in ("rip", "vid"):
        sys.exit(run_vid(args))
    elif args.command == "info":
        sys.exit(run_info(args))
    elif args.command == "list":
        sys.exit(run_list(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()