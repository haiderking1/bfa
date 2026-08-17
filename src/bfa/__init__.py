def main() -> int:
    """Run the BFA command-line interface."""
    from .cli import main as cli_main

    return cli_main()


__all__ = ["main"]
