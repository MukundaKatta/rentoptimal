"""CLI for rentoptimal."""
import sys, json, argparse
from .core import Rentoptimal

def main():
    parser = argparse.ArgumentParser(description="RentOptimal — Rental Price Optimizer. ML-powered optimal rental pricing based on market analysis.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Rentoptimal()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.process(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"rentoptimal v0.1.0 — RentOptimal — Rental Price Optimizer. ML-powered optimal rental pricing based on market analysis.")

if __name__ == "__main__":
    main()
