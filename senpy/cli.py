import sys
from .models import Error
from .api import parse_params, CLI_PARAMS
from .extensions import Senpy


def argv_to_dict(argv):
    '''Turns parameters in the form of '--key value' into a dict {'key': 'value'}
    '''
    cli_dict = {}

    for i in range(len(argv)):
        if argv[i][0] == '-':
            key = argv[i].strip('-')
            value = argv[i + 1] if len(argv) > i + 1 else None
            if value and value[0] == '-':
                cli_dict[key] = ""
            else:
                cli_dict[key] = value
    return cli_dict


def parse_cli(argv):
    cli_dict = argv_to_dict(argv)
    cli_params = parse_params(cli_dict, spec=CLI_PARAMS)
    return cli_params, cli_dict


def main_function(argv):
    '''This is the method for unit testing
    '''
    cli_params, cli_dict = parse_cli(argv)
    plugin_folder = cli_params['plugin_folder']
    sp = Senpy(default_plugins=False, plugin_folder=plugin_folder)
    sp.activate_all(sync=True)
    res = sp.analyse(**cli_dict)
    return res


def main():
    '''This method is the entrypoint for the CLI (as configured un setup.py)
    '''
    try:
        res = main_function(sys.argv[1:])
        print(res.to_JSON())
    except Error as err:
        print(err.to_JSON())
        sys.exit(2)


if __name__ == '__main__':
    main()
