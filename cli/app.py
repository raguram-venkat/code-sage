import argparse
from cli.subcommands.clone import Clone
from cli.subcommands.initialize import Initialize

#TODO: add delete subcommand

sage_parser = argparse.ArgumentParser(prog="sage",usage="Code Sage CLI",description = "%(prog)s is used to review codebases interactively")
sage_parser.add_argument('--version', action = 'version', version = '%(prog)s 0.0.0')
subparsers = sage_parser.add_subparsers(title = "command", dest = "command")

for command_class in [Initialize, Clone]:
    command_instance = command_class()
    command_instance.register(subparsers)



 
