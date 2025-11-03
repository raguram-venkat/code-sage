import sys
import shlex
from cli.app import sage_parser

def repl():
    print("Sage Interactive CLI — type 'exit' or 'quit' to leave.")

    while True:
        try:
            command = input("sage> ").strip()
            if not command:
                continue
            if command.lower() in ("exit", "quit"):
                break

            # Parse user command
            argv = ["sage"] + shlex.split(command)
            sys.argv = argv
            
            # Dispatch through main parser
            args = sage_parser.parse_args()
            if hasattr(args, "func"):
                args.func(args)
            else:
                sage_parser.print_help()
            
        except SystemExit:
            continue
        except KeyboardInterrupt:
            print("\nInterrupted.")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    repl()


if __name__ == "__main__":
    main()
