"""
Describes all the exceptions used

:author: zhao xia
"""

# Ssh Manager error code 1000XX
GATEWAY_MISSING_USERPW = 'Ssh_err_100000: you provided gateway, so please provide associated user and password'
LOST_CONNECTION = 'Ssh_err_100001: ssh reconnection failed after attempts: {host, attempts}: '
CONNECTION_DOWN = 'Ssh_warn_100002: ssh connection down, trying to reconnect: {host, timeout (seconds)}: '
PUBLIC_KEY_COPY_ERROR = "Ssh_err_100003: error while copying public key, return code: "
CONNECTION_NOT_FOUND = 'Ssh_warn_100004: ssh connection down: '
NO_INTERACTIVE_SESSION = 'Ssh_err_100005: cannot open interactive session'
SSH_CMD_FAILED = "Ssh_err_100006: the command running on the server through ssh failed"

# MultiTask class 1001xx
TASK_TYPE_FAILURE = "UNSUPPORTED_TASK_TYPE_100101: Unsupported task type"

if __name__ == '__main__':
    pass
