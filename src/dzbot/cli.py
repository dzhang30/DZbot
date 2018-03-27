import argparse

from subprocess import Popen, PIPE, TimeoutExpired


def parse_args(message=None):
    """
    CLI parser program for users to interact with dzbot

    :param message: the action message that is sent to dzbot from hipchat
    :return: args
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    list_all_parser = subparsers.add_parser('list', help='list all specified entities or a single entity')
    list_all_parser.add_argument('--entity',
                                 choices=['users', 'eps', 'services', 'oncalls', 'schedules'],
                                 required=True,
                                 help='retrieve a list of all specified entity names')
    list_all_parser.add_argument('--name', nargs='+', help='specify either an eps name or oncalls name')

    override_parser = subparsers. \
        add_parser('override', help='override the current schedule for the specified user')
    override_parser.add_argument('--schedule', nargs='+', required=True, help='schedule name that you want to override')
    override_parser.add_argument('--user', nargs='+', required=True, help='user name')
    override_parser.add_argument('--start', required=True, help='start time')
    override_parser.add_argument('--end', required=True, help='end time')

    notify_parser = subparsers.add_parser('notify', help='send an incident to a user or escalation policy')
    notify_parser.add_argument('--entity', choices=['users', 'eps'], required=True, help='choose user or ep')
    notify_parser.add_argument('--name', nargs='+', required=True, help='user name or ep name')
    notify_parser.add_argument('--service', nargs='+', required=True, help='service name')
    notify_parser.add_argument('--title', nargs='+', required=True, help='title of incident')
    notify_parser.add_argument('--message', nargs='+', required=True, help='body of message')

    subparsers. \
        add_parser('ensure-oncalls', help='ensure that each ep has an oncall level 1 and oncall level 2 user')

    return parser.parse_args(message)


def check_stdout_stderr(message_list):
    """
    Since command line programs output '--help' and 'error' messages into stdout and stderr respectively, we need to
    have our main process read from the stdout and stderr of a child process that makes these command line --help and
    error calls

    :param message_list: the command in list format, i.e. ['list', '--entity', 'users', '--name', 'Test']
    :return: a tuple containing the stdout and stderr contents from the child process making the CL call. If the Cl
    call is correct and --help is not specified, then the tuple will contain None for both stdout and stderr
    """
    command = ["python", "src/dzbot/cli.py"]
    command.extend(message_list)
    child_process = Popen(command, stdout=PIPE, stderr=PIPE)
    try:
        out, err = child_process.communicate(timeout=5)
    except TimeoutExpired:
        child_process.kill()
        out, err = child_process.communicate()

    return out.decode('utf-8'), err.decode('utf-8')


if __name__ == '__main__':
    # This is needed for the check_stdout_stderr() method where a child process calls the command line arguments
    # (i.e. python src/dzbot/cli.py list --help, python src/dzbot/cli.py list --name Test [error example]) and
    # spits out '--help' content into stdout and 'error' content into stderr
    parse_args()
