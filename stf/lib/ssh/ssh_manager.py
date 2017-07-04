"""
This library manages the SSH connections

There are two distincts cases :
    #. SSH connection to a lab  (connection with user ainet and root)
       connection to lab : this is the easiest case because users and pw are known.
       Even if the first connection is with two users (ainet - root) it is transparent for the tester.
       Once the instance is created you can call immediatly the public methods:
       getClient(), run(), sendStringAndExpect(), scpGet(), scpPut()
       The first call to one of those methods will ssh-connect, install the ssh keys if needed
       and store the connection. The subsequent calls will just fetch the ssh connection already stored.

    #. SSH connection to any computer "not-lab" with a specified user and pw.
       Connection to a non-lab. There are 2 differences
          * The very first call (to create the SSH connection) must be done with a user and pw via getClient()
          * The user must be specified in the public methods

usage for lab:

>>> sshManager = SshManager()   # creates the instance
>>> localPath = sshManager.scpGet(LAB,filename)  # get a file on remote lab. SSH connection is created and stored in the instance of SshManager. \
                                                it is not necessary to store the returned (paramiko) SSH connection

>>> sshManager.run(LAB, 'whoami')      # run() could also be called immediatly after instance creation

>>> SshManager().run(LAB, 'pwd')    # a "one-shot" call is possible without storing the instance

>>> sshManager.getClient(LAB)             # can be used to explicitly create the connection without doing more.
>>> sshCn = sshManager.getClient(LAB)     # The same as previous one but we store the paramiko SSH client

usage for non-lab:

>>> sshManager = SshManager()     # creates the instance
>>> sshconn = sshManager.scpGet(LAB, user='nx', filename)      # NOT POSSIBLE now because not yet ssh-connected
>>> sshManager.run(LAB, 'whoami', user='nx')                   # idem : NOT POSSIBLE now because not yet ssh-connected
>>> sshManager.getClient(LAB, user='nx', pw='anything')        # OK: creates the connection which is stored into instance
>>> sshManager.run(LAB, user='nx', cmd='whoami')               # connection already created, we can run a command
"""

# ===== fix  Pylint bug. See http://stackoverflow.com/questions/20553551/how-do-i-get-pylint-to-recognize-numpy-members
# pylint: disable=no-name-in-module
from collections import namedtuple
from datetime import datetime
from datetime import timedelta
from operator import xor
import os
import re
import time
import socket
from subprocess import Popen, PIPE
from subprocess import call
import sys
import threading
import stat

import paramiko
from paramiko.ssh_exception import SSHException, AuthenticationException
from scp import SCPClient

from stf.lib.common import Utils
import stf.lib.exceptions_messages as msgExc
from stf.lib.logging.logger import Logger
import traceback
from stf.lib.exceptions_messages import CONNECTION_DOWN, LOST_CONNECTION, \
    CONNECTION_NOT_FOUND, NO_INTERACTIVE_SESSION
import random
import string
from random import randint

# pylint: enable=no-name-in-module
class SshManagerError(BaseException):
    """If error, raise it."""
    pass

class SshManagerTimeoutError(BaseException):
    """If error, raise it."""
    pass


# very verbose mode of paramiko :
# paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
LOGGER = Logger.getLogger(__name__)

# ---- init CONSTANTS
BUFF_SIZE = 8192

ROOT_DIR = '/root'
ROOT_PRPT = 'root-#'
PW_PRPT = 'Password:'
CMD_KEYGEN = 'ssh-keygen'
CMD_KEYSCAN = 'ssh-keyscan'
CMD_SU = 'su -'
CMD_WHO = 'whoami'
WHO_RESP = os.linesep + 'root' + os.linesep
PRIV_KEY_FILE = '/id_rsa'
SSH_DIR = '.ssh/'
AUTHK_FIL = 'authorized_keys'
MAX_CONNECTION_ATTEMPTS = 15
CONNECTION_ATTEMPTS_INTERVAL = 60  # seconds
SSH_DEFAULT_PORT = 22
MAX_PROMPT_ATTEMPTS = 10
PROMPT_CONNECTION_INTERVAL = 2
INTERVAL_ATTEMPTS = 0.1  # seconds, time to wait to verify if the command returns an exit status
SSH_CMD_TIMEOUT = 20  # in minutes max time to attempt to verify if the command returns an exit status


class SshManager(object):
    """
    Manage all the SSH connections with any user. Install SSH key if needed.
    There are 2 cases to address a connection : a lab or not
    #. 'hostname': connecting to a lab in 2 steps : login 'ainet' then 'root'. pw are known.
    #. 'user@hostname': connecting directly to hostname in 1 step using the user 'user'.
    The user can be root.  pw MUST be specified as argument for the first call to getClient
    See functions 'getClient' or 'run'

    :param str gateway: store gateway information
    :param str gw_user: the gateway user
    :param str gw_pw: the gateway password
    :raises SshManagerError: if gateway missed user and password, raise exception
    """

    confDir = os.getenv("HOME") + "/.ssh"
    cacheDir = "cache" #
    if not os.path.exists(cacheDir):
        os.makedirs(cacheDir)
    privateKey = confDir + PRIV_KEY_FILE  #
    publicKey = privateKey + ".pub"  #

    tunnel = namedtuple("tunnel", ["process", "port"])
    clientAndTunnel = namedtuple("clientAndTunnel", ["client", "tunnel"])
    defaultHeartbeat = 120

    # creates conf dir if needed
    if not os.path.isdir(confDir):
        LOGGER.debug(confDir + " directory doesn't exist, creating it")
        os.makedirs(confDir)

    if not os.path.isfile(publicKey):
        LOGGER.trace(publicKey + " doesn't exist, delete " + privateKey + " and retry")
        sys.exit(1)
    pubKeyFile = open(publicKey, "r")
    publicKeyStr = pubKeyFile.read().rstrip()
    pubKeyFile.close()
 

    def __init__(self, gateway=None, gw_user=None, gw_pw=None):
        """
        Constructor
        """
        self.gateway = gateway  # store gateway information
        self.gatewayUser = gw_user
        self.gatewayPassword = gw_pw
        self.tunnelLocalPort = -1
        self.tunnelProcess = None
        self._connections = {}  # empty dictionary
        if gateway is not None:
            if gw_user is None or gw_pw is None:
                LOGGER.error(msgExc.GATEWAY_MISSING_USERPW)
                raise SshManagerError, msgExc.GATEWAY_MISSING_USERPW

        self.clientLock = threading.Lock()

    def _checkAccessAndGrantIfNecessaryIn2Steps(self, host, primaryUser, primaryPassword, finalUser, finalPw, port=SSH_DEFAULT_PORT):
        """
        Check if we have already SSH access. And copy SSH key if necessary
        twoStep=True

        :param Lab host: hostname
        :param str primaryUser: primary user to login
        :param str primaryPassword: pw of primaryUser
        :param str finalUser: final user to login
        :param str finalPw: pw of final user (= root)
        :param bool twoStep: indicate whether we are in a 2-step process to copy key via ainet then root ?
        :return: the client instance
        :rtype: str

        >>> self._checkAccessAndGrantIfNecessaryIn2Steps(host, primaryUser, primaryPassword, finalPw, port=SSH_DEFAULT_PORT)
        """
        cli = self._checkAccessUsingPw(host, primaryUser, primaryPassword, port)
        if cli is not None:
            SshManager._copyPublicKeyRootIn2Steps(cli, finalUser,  finalPw)  # copy key to root via ainet login
            return cli
        else:
            return None

    def _checkAccessAndGrantIfNecessary(self, host, user, password, port=SSH_DEFAULT_PORT):
        """
        Check if we have already SSH access. And copy SSH key if necessary
        twoStep=True

        :param Lab host: hostname
        :param str user: primary user to login
        :param bool twoStep: indicate whether we are in a 2-step process to copy key via ainet then root ?
        :return: the cli
        :rtype: str

        >>> self._checkAccessAndGrantIfNecessary(host, user, password, port=SSH_DEFAULT_PORT)
        """
        cli = self._checkAccessUsingPw(host, user, password, port)
        if cli is not None:
            exceptionMessage = ' , '.join([host, user, password])
            SshManager._copyPublicKey(cli, exceptionMessage)  # copy key directly
            return cli
        else:
            return None

    def _checkAccessUsingKey(self, host, user, port=SSH_DEFAULT_PORT):
        """
        check if we have SSH access via user by using SSH keys ?
        Having an AuthenticatioException is one of the standard ways.

        :param Lab host: hostname
        :param str user: user to login
        :return: None if no connection. Returns instance of SSH connection if OK
        :rtype: None/object

        >>> self._checkAccessUsingKey(host, user, port=SSH_DEFAULT_PORT)
        """
        #client = paramiko.SSHClient()
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #  to ignore user .ssh homedir keys : use those options  allow_agent=False, look_for_keys=False)
        # CAUTION with those option : exception is SSHException (instead of AuthenticationException)
        client.connect(host, port, user, key_filename=self.privateKey)
        client.get_transport().set_keepalive(self.__class__.defaultHeartbeat)
        return client

    def _checkAccessUsingPw(self, host, user, password, port=SSH_DEFAULT_PORT):
        """
        check if we have SSH access via user by using SSH keys ?
        Having an AuthenticatioException is one of the standard ways.

        :param Lab host: hostname
        :param str user: user to login
        :raises SshManagerError: if can't connect to host with user, raise exception
        :return: None if no connection. Returns instance of SSH connection if OK
        :rtype: None/object

        >>> self._checkAccessUsingPw(host, user, password, port=SSH_DEFAULT_PORT)
        """
        #client = paramiko.SSHClient()
        client = paramiko.client.SSHClient()
        # client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(host, port, user, password)
            client.get_transport().set_keepalive(self.__class__.defaultHeartbeat)
            return client
        except BaseException:
            msg = "Cannot connect to " + host + " with user " + user + " and password " + str(password)
            LOGGER.debug(msg)
            raise SshManagerError(msg)
        client.close()
        return None

    def _openTunnel(self, host):
        """
        open a Tunnel if using a gateway

        :param Lab host: hostname
        :return: the tunnel property
        :rtype: str

        >>> self._openTunnel(host)
        """
        # trick to find free port number
        _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _sock.bind(("", 0))
        self.tunnelLocalPort = _sock.getsockname()[1]
        _sock.close()
        tunnelArgs = ["ssh", "-oStrictHostKeyChecking=no",
                      "-oUserKnownHostsFile=/dev/null", "-i",
                      SshManager.privateKey, "-L",
                      str(self.tunnelLocalPort) + ":" + host + ":" + str(SSH_DEFAULT_PORT),
                      self.gatewayUser + "@" + self.gateway]
        process = Popen(tunnelArgs, stdout=PIPE)
        # trick: read first line of output from ssh command so that python
        # waits long enough before it tries to connect to tunnel input
        # logger.debug("popen answer first line: " + self.tunnelProcess.stdout.readline())
        process.stdout.readline()
        return SshManager.tunnel(process, self.tunnelLocalPort)

    def _runCommand(self, host, userSsh, command, client, ignoreStdStreams=False, txtToAdd="", timeout=SSH_CMD_TIMEOUT, env=None):
        """
        run command method

        :param Lab host: the lab object
        :param str userSsh: the user ssh
        :param str command: command
        :param str client: the client
        :param bool ignoreStdStreams: indicate whether to ignore std streams, default value is False
        :param str txtToAdd: txt to add
        :param int timeout: the time out for the run command, default is 20 minutes
        :param dict env: a dict of shell environment variables, to be merged into the default environment that the remote command executes within.
        :raises SshManagerError: if command not responding, raise exception
        :return: a list containing exit status and output of the command
        :rtype: list

        >>> self._runCommand(host, userSsh, command, client, ignoreStdStreams=False, txtToAdd="", timeout=SSH_CMD_TIMEOUT)
        """
        # log msg before command executed
        LOGGER.trace(' -- '.join([' ----- Run command', host, userSsh, command, txtToAdd]))

        _, stdOut, stdErr = client.exec_command(command, environment=env)
        countAttempts = 0
        stop = False
        maxTime = datetime.now() + timedelta(minutes=timeout)
        while (not stdOut.channel.exit_status_ready()) and (stop == False):
            countAttempts += 1
            if countAttempts == 100:
                if datetime.now() < maxTime:
                    countAttempts = 0
                else:
                    stop = True
            time.sleep(INTERVAL_ATTEMPTS)
        if stop == True:
            msg = "The command '%s' is not responding  within %s minutes " % (command, str(timeout))
            LOGGER.error(msg)
            raise SshManagerTimeoutError, msg
        else:
            exitStatus = stdOut.channel.recv_exit_status()

        if not ignoreStdStreams:

            out = stdOut.read().rstrip()
            err = stdErr.read().rstrip()

            # log msg after command executed
            txtHead = ' -- '.join([' ----- Run stdout ', host, userSsh, command, 'rc=' + str(exitStatus), ''])
            txtLogList = [txtHead, ' ----- stdout : ']
            if out != '':
                txtLogList.append(out)
            if err != '':
                txtLogList += [' ----- stderr : ', err]
            LOGGER.trace(os.linesep.join(txtLogList))
        else:
            out = ''
            err = ''

        return exitStatus, out.rstrip(), err.rstrip()


    def scpGet(self, host, source, user=None, localDir=None):
        """
        get a remote file and copy in localDir(default is cache Dir) . similar as 'scp  user @ remote:file localDir'
        the retruned file name is added one timestamp suffix with a underscore like filename_20160627092530123456
        The timestamp has format of 4 year + 2 month + 2 day + 2 hour + 2 minute + 2 second + 6 Microsecond 

        :param str host: IP address of the host
        :param str source: the remote file in lab which should be copy to localDir
        :param str user: the user to login on remote. default is 'root'
        :param str localDir: the full path in local to store the file, default is None, if None, use cache dir 
        :return: the path of the local file
        :rtype: str

        Note:
        At least one getClient() must have been executed before calling this proc
             i.e. connection is already stored in self._connections

        >>> sshManager.scpGet(host, source)
        """
        userSsh = 'root' if user is None else user
        client = self.getClient(host, user=userSsh)
        scpClient = SCPClient(client.get_transport(), socket_timeout=float(self.__class__.defaultHeartbeat))
        if not localDir:
            localDir = SshManager.cacheDir + os.sep + host
        if not os.path.isdir(localDir):
            os.mkdir(localDir)
        _localPath = localDir + os.sep + os.path.basename(source) + "_" + datetime.now().strftime('%Y%m%d%H%M%S%f')
        LOGGER.trace("scpClient.get(%s, %s) from %s@%s", source, _localPath,
                         userSsh, host)
        scpClient.get(source, _localPath)
        return _localPath

    def scpGetDir(self, host, source, user=None, localDir=None, pw=None):
        """
        get a remote file dir or remote file and copy in localDir(default is cache Dir)

        :param str host: IP address of the host
        :param str source: the remote file in lab which should be copy to localDir
        :param str user: the user to login on remote. default is 'root'
        :param str localDir: the full path in local to store the file, default is None, if None, use cache dir 
        :return: the path of the local file
        :rtype: str

        Note:
        At least one getClient() must have been executed before calling this proc
             i.e. connection is already stored in self._connections

        >>> sshManager.scpGetDir(host, source)
        """
        userSsh = 'root' if user is None else user
        client = self.getClient(host, user=userSsh, pw=None)
        
        sftp_client = client.open_sftp()
        try:
            sftp_client.stat(source)
        except BaseException:
            LOGGER.error("remote %s not exist", source)
            raise SshManagerError("remote %s not exist", source)
        if not localDir:
            localDir = SshManager.cacheDir + os.sep + host
        self.downloadDir(sftp_client, source, localDir)
        self.closeClient(host, user)
        return localDir

    def downloadDir(self, sftp_client, remote, local_dir):
        """
        download dir or file 
        """
        LOGGER.debug("try to download from  %s to local %s", remote, local_dir)
        if stat.S_ISDIR(sftp_client.stat(remote).st_mode):
            LOGGER.debug("try to download dir from  %s to local %s", remote, local_dir)
            remotebasedir = os.path.basename(remote)
            localdir_append1 = os.path.join(local_dir,remotebasedir)
            if not os.path.exists(localdir_append1):
                os.mkdir(localdir_append1)
            for filename in sftp_client.listdir(remote):
                filePath = os.path.join(remote, filename)
                if stat.S_ISDIR(sftp_client.stat(filePath).st_mode):
                    LOGGER.debug("try to copy %s", filePath)
                    self.downloadDir(sftp_client, filePath, localdir_append1)
                else:
                    sftp_client.get(filePath, os.path.join(localdir_append1, filename))
                
        else:
            LOGGER.debug("try to download file from  %s to local %s", remote, local_dir)
            if os.path.isfile(remote):
                sftp_client.get(remote, os.path.join(local_dir, os.path.basename(remote)))

    def scpGetAll(self, host, source, user=None, station=None):
        """
        get remote files and copy in cache Dir . similar as 'scp user @ remote:file  localfile'
        the retruned file name is added one timestamp suffix with a underscore like filename_20160627092530123456
        The timestamp has format of 4 year + 2 month + 2 day + 2 hour + 2 minute + 2 second + 6 Microsecond 
    
        :param str host: IP address of the host
        :param str source: the local files which should be in cache Dir, eg: /snlog/snmplog*
        :param str user: the user to login on remote. default is 'root'
        :param str station: string rcs host name the station to load files from
                            (default is active pilot station on lab or just host)
        :raises SSHException: if cmd failed, raise exception
        :return: the local file list with full path
        :rtype: str

        Note:
        At least one getClient() must have been executed before calling this proc
             i.e. connection is already stored in self._connections

        >>> sshManager.scpGetAll(host, source)
        """
        userSsh = 'root' if user is None else user
        client = self.getClient(host, user=userSsh)
        command = "ls " + source
        if station:
            tempDir = "/tmp/scp-" + str(randint(10000, 99999))
            mkdirCmd = "mkdir " + tempDir
            returnCode, _, _ = self.run(host, mkdirCmd, user)
            if returnCode:
                raise SSHException(mkdirCmd + " failed on target " + host)
        returnCode, stdOut, _ = self.run(host, command, user, bladeRcsHostname=station)
        if returnCode:
            raise SSHException(command + " failed on target " + host)
        fileList = stdOut.rstrip().split()
        if station:
            for fileName in fileList:
                command = "scp " + station + ":" + fileName + " " + tempDir
                returnCode, _, _ = self.run(host, command, user)
                if returnCode:
                    raise SSHException(command + " failed on target " + host)
        scpClient = SCPClient(client.get_transport())
        _localDir = SshManager.cacheDir + os.sep + host
        _localFileList = []
        if not os.path.isdir(_localDir):
            os.mkdir(_localDir)
        for fileName in fileList:
            _localPath = _localDir + os.sep + os.path.basename(fileName)
            remoteFile = fileName
            if station:
                remoteFile = tempDir + "/" + os.path.basename(fileName)
            _localPath += "_" + datetime.now().strftime('%Y%m%d%H%M%S%f')
            LOGGER.trace("scpClient.get(%s, %s) from %s@%s", remoteFile, _localPath,
                         userSsh, host)
            scpClient.get(remoteFile, _localPath)
            _localFileList.append(_localPath)
        if station:
            command = "rm -fr " + tempDir
            returnCode, _, _ = self.run(host, command, user)
            if returnCode:
                raise SSHException(command + " failed on target " + host)
        return _localFileList

    def scpPut(self, localFile, host, remoteFile, user=None):
        """
        copy a file to remote host . similar as 'scp  localfile  host:remotefile'

        :param str localFile: path of local File. absolute or relative (depending where you are)
        :param str host: the IP address of the remote host where to copy
        :param str remoteFile: path of remote file (absolute) or in homedir if relative
        :param str user: login.  user=None means 'root'
        :return: False if localFile does not exist, else True
        :rtype: bool

        NB : At least one getClient() must have been executed before calling this proc
             i.e. connection is already stored in self._connections

        >>> sshMngr.scpPut('/tmp/tototo', LX4SI3, '/tmp/tototo', user='jenkins')
        """
        userSsh = 'root' if user is None else user
        client = self.getClient(host, user=userSsh)
        scpClient = SCPClient(client.get_transport())
        scpClient.socket_timeout = 1000.0
        if os.path.isfile(localFile):
            LOGGER.trace("scpClient.put(%s, %s) to %s@%s", localFile, remoteFile,
                         userSsh, host)
            scpClient.put(localFile, remoteFile)
            return True
        else:
            return False

    def uploadDir(self, scpClient, sftp_client , local_dir, remote_dir, host, user=None, pw=None):
        """
        """
        LOGGER.debug("try to upload from server %s, user %s ,%s to  %s", host, user, local_dir, remote_dir )
        baselocaldir = os.path.basename(local_dir)
        remotedir_append = os.path.join(remote_dir, baselocaldir)
        try:
            sftp_client.stat(remotedir_append)
        except BaseException:
            mkdirCmd = "mkdir " + remotedir_append
            returnCode, _, _ = self.run(host, mkdirCmd, user)
            if returnCode:
                raise SSHException(mkdirCmd + " failed on target " + host + ", using user "+user)
                
        for filename in os.listdir(local_dir):
            localfilePath = os.path.join(local_dir, filename)
            LOGGER.debug("try to upload %s", localfilePath)
            if os.path.isdir(localfilePath):
                # uses '/' path delimiter for remote server
                self.uploadDir(scpClient, sftp_client, localfilePath , remotedir_append, host, user=None, pw=None)
            else:
                LOGGER.debug("try to upload file %s", localfilePath)
                if os.path.isfile(localfilePath):
                    scpClient.put(localfilePath, os.path.join(remotedir_append, filename))
                    
                            
    def scpPutDirOrFile(self, local, remoteDir, host, user=None, pw=None):

        """
        upload local file or dir to a remoteDir 

        :param str host: IP address of the host
        :param str local: the full path in local to store the file,or local file
        :param str user: the user to login on remote. default is 'root'
        :param str remoteDir:  path of remote dir (absolute) or in homedir if relative 
        :return: the path of the remotedir
        :rtype: str
        
        """
        
        if not local:
            raise SshManagerError("local %s not exist", local) 
        userSsh = 'root' if user is None else user
        password = '' if pw is None else pw
        client = self.getClient(host, user=userSsh, pw=password)
        scpClient = SCPClient(client.get_transport())
        sftp_client = client.open_sftp()
        
        try:
            sftp_client.stat(remoteDir)
        except BaseException:
            LOGGER.error("remote %s not exist", remoteDir)
            raise SshManagerError("remote %s not exist", remoteDir)
        
        try:
            if os.path.isfile(local):
#                 remoteFile = os.path.join(remoteDir, os.path.basename(local))
                LOGGER.debug("scpClient.put(%s, %s) to %s@%s", local, remoteDir,
                         userSsh, host)
                LOGGER.info("upload from %s to %s" , local, remoteDir)
                scpClient.put(local, remoteDir)
            elif os.path.isdir(local):
                self.uploadDir(scpClient, sftp_client, local, remoteDir, host, userSsh, password)
        except Exception as err:
            LOGGER.error("scpPutDirOrFile error %s", err)
            raise SshManagerError("upload %s to %s error", local, remoteDir)
        finally:
            self.closeClient(host,user)   
        return remoteDir
    
    def getClient(self, host, user=None, pw=None, becomeUser=None, becomePasswd=None, useKey=True):
        """
        return the paramiko SSH client instance. Creates and install SSH keys if needed. Default user is root.
        There are 3 cases depending on host syntax, mixing root or ot root user, 1-step or 2-steps process

        :param str host: the IP address of the hostname used when creating the instance
        :param str user: login, "user=None" (no parameter) means it is a lab => 2 steps login
        :param str pw: password
        :param bool useKey: use public / private key to connect to this host or simple user
               password method. Default value: true (use public / private key).

        The following prameters (labCustomxxx) are useful only for lab (2-steps login):

        :param str becomeUser: to connect to a lab (in 2 steps) without the default user (not ainet)
                                  Default is 'ainet'
        :param str becomePasswd: the pw associated to labCustomUser
                                Default is the ainet pw
        :raises SshManagerError: if can't connect to host, raise exception
        :return: the paramiko SSHclient instance
        :rtype: object
        """
        # --- first set the key to check if connection already stored
        if host is None:
            msg = "host is None"
            LOGGER.error(msg)
            raise SshManagerError(msg)

        if user is None:  # is it a lab ? (a lab is a 2-steps login)
            finalUser = "root"
        else:
            finalUser = user

        if becomeUser:
            finalUser = becomeUser
            finalPw = becomePasswd
            primaryUser = user
            primaryPw = pw
            twoStep = True
        else:
            twoStep = False
            finalPw = pw
        
        
        key = finalUser + '@' + host
        self.clientLock.acquire()
        # --- if user@host already established , returns it
        if key in self._connections:
            self.clientLock.release()
            return self._connections[key].client

        destPort = SSH_DEFAULT_PORT
        try:
            # --- test gateway
            tunnel = None
            if self.gateway is not None:
                self._checkAccessAndGrantIfNecessary(self.gateway,
                                                     self.gatewayUser,
                                                     self.gatewayPassword)
                tunnel = self._openTunnel(host)
                host = "localhost"
                destPort = tunnel.port

            client = None

            if useKey:
                # test if finalUser has already grant access.  Have an exception means only
                # that we dont have access, this is a normal way
                try:
                    client = self._checkAccessUsingKey(host, finalUser, destPort)
                except (AuthenticationException, SSHException) as err:
                    LOGGER.trace(' No access, no SSH key already installed on ' + str(host) + \
                                 ' with user ' + finalUser)
                    LOGGER.trace(' Now trying SSH access via user + password')
                    useKey = False
                except Exception as err:
                    msg = "Cannot connect to " + str(host) + " as " + finalUser
                    LOGGER.error(msg)
                    LOGGER.exception(msg)
                    raise err

            if client is None:  # no access for finalUser via SSH key

                # if 2-step login (lab) : login to ainet
                try:
                    if twoStep:
                        #  ----  in 2 steps , finalUser is always root
                        self._checkAccessAndGrantIfNecessaryIn2Steps(host, primaryUser, primaryPw, finalUser, finalPw, destPort)
                        client = self._checkAccessUsingKey(host, finalUser, destPort)
                    else:
                        if useKey:
                            self._checkAccessAndGrantIfNecessary(host, finalUser, finalPw, destPort)
                            client = self._checkAccessUsingKey(host, finalUser, destPort)
                        else:
                            client = self._checkAccessUsingPw(host, finalUser, finalPw)
                except SSHException:
                    msg = "Cannot connect to " + host + " as " + (user if twoStep else finalUser)
                    LOGGER.error(msg)
                    LOGGER.exception(msg)
                    raise SshManagerError(msg)

            # --- now finalUser has access to host . We can store the connection
            clientAndTunnel = SshManager.clientAndTunnel(client, tunnel)
            self._connections[key] = clientAndTunnel
        finally:
            self.clientLock.release()

        return client

    def closeClient(self, host, user='root'):
        """
        closeClient : close connection to a host or a list of host

        :param str host: an IP Addresse of  hostname (string)
        :param str user: login

        >>> sshManager.closeClient(host, user='root')
        """
        if user is None:
            user = 'root'
        key = user + '@' + host
        self.clientLock.acquire()
        if key in self._connections:
            sshClient = self._connections[key]
            if sshClient.client:
                sshClient.client.close()
            if self.gateway is not None:
                SshManager._closeTunnel(sshClient.tunnel)
            del self._connections[key]
        self.clientLock.release()

    def closeAllClients(self):
        """
        close all Clients of this instance

        >>> sshManager.closeAllClients()
        """
        for key in self._connections.keys():
            wkey = key.split('@')
            self.closeClient(wkey[1], wkey[0])

    def _reconnect(self, client, host, userSsh):
        """
        :param str client: the client
        :param str host: the ip address of the lab
        :param str userSsh: the user ssh
        :raises BaseException: if reconnection attempt failed with timeout, raise exception
        :return: the client
        :rtype: str

        >>> self._reconnect(client, host, userSsh)
        """
        l_client = client
        timeout = CONNECTION_ATTEMPTS_INTERVAL * MAX_CONNECTION_ATTEMPTS
        LOGGER.warning(CONNECTION_DOWN + host + ", " + str(timeout))
        count = 0
        while count < MAX_CONNECTION_ATTEMPTS and \
                ((l_client is None) or (l_client.get_transport() is None) or \
                (not l_client.get_transport().is_alive())):
            self.closeClient(host, userSsh)
            time.sleep(CONNECTION_ATTEMPTS_INTERVAL)
            try:
                l_client = self.getClient(host, user=userSsh)
            except BaseException:
                LOGGER.debug("ssh reconnection attempt #" + str(count) + " failed: "
                             + traceback.format_exc())
            count = count + 1
        if count == MAX_CONNECTION_ATTEMPTS:
            self.closeClient(host, userSsh)
            msg = LOST_CONNECTION + host + ", " + str(MAX_CONNECTION_ATTEMPTS)
            LOGGER.error(msg)
            raise BaseException(msg)
        LOGGER.info("ssh connection back after " + str(count) + " attempts: " + host)
        return l_client

    def run(self, host, cmd, user=None, ignoreStdStreams=False, bladeRcsHostname=None,
            timeout=SSH_CMD_TIMEOUT, env=None):
        """
        Executes a command via paramiko exec_command and return the full stdout of the command.
        An empty string could be returned in some cases, a command in background for example.

        #. Dont rely on trailing chars of the flow (EOL).
        #. Dont suppose that there is a trailing EOL or no trailing EOL.
        #. The caller must filter the full output to find the right line.
        #. At least one getClient() must have been executed before calling this proc
           i.e. connection is already stored in self._connections
        #. If connection is dead, we try to reconnect every minute for 15 minutes. If it's still
           impossible to open a new connection after 15 minutes, an exception is raised.

        :param str host: IP address of the target lab
        :param str cmd: the command to execute
        :param str user: login
        :param str bladeRcsHostname: mcas rack-chassis-slot blade hostname, eg:0-0-2,
                                     either station or bladeRcsHostname can be used, but not both at the same time.
        :param str ignoreStdStreams: ignore stdout and stderr. Dont read them after executing command.
                                     But get an exit status. Useful for nohup command, background process, etc
        :param int timeout: in minutes. Interrupt the function if timeout reached, default value is 20 min.
        :return: the tuple (exit_status, stdout) stdout is a unique string with all EOL except trailing EOL
        :rtype: tuple

        >>> sshManager.run('hp31oam',cmd)              #executes cmd on pilot active
        >>> sshManager.run(lab, 'nohup launch_traffic &', ignoreStdStreams=True)  #launch traffic in background. Don't wait the output of the command
        """
        client = None
        try:
            client = self.getClient(host, user=user)
        except BaseException:
            LOGGER.debug("Get client failure and will reconnect")

        userSsh = 'root' if user is None else user
        if client is None or (client.get_transport() is None) or (not client.get_transport().is_alive()):
            client = self._reconnect(client, host, userSsh)

        if bladeRcsHostname:
            LOGGER.debug('blade is: %s' % bladeRcsHostname)
            command = cmd.replace("\"", "\\\"").replace("$", "\\$")
            command = "ssh -q " + bladeRcsHostname + " \"" + command + "\""
        else:
            command = cmd

        txtToAdd = '[ignore stdout stderr]' if ignoreStdStreams else ''

        return self._runCommand(host, userSsh, command, client, ignoreStdStreams, txtToAdd, timeout=timeout, env=env)
    
    def sendStringAndExpect(self, host, strToSend, expectString, user=None, timeout=1200, env=None):
        """
        run a string or command and expect a string to terminate the function. The string to wait can be
        located at end of flow (like a prompt) and in the middle of the flow (useful with subshl).
        Trailing spaces are removed to get an easier comparison.

        :param str host: the IP address of the host where execute the cmd
        :param str strToSend: the command to execute
        :param str-list expectString: the string to detect in  stdout to quit the function. Case sensistive
                                      You can use multiple a string or a list of string
        :param str user: default is 'root'
        :param int timeout: in seconds. interrupt the function if timeout reached. Useful if expectString
                            is not found. Default value is 20 min (1200 seconds)
        :return: a list containing timeoutReached, stdout, stderr: if timeout reached, timeoutReached is True;
                 the stdout of the command, the stderr as 2 unique string (including EOL)
        :rtype: list

        warning:
        The parameter expectString "must not be empty"

        >>> sshManager.sendStringAndExpect(spa20oam.oamIpAddress,'scp backup_xxx.tar.gz','#')
        """
        userSsh = 'root' if user is None else user
        client = self.getClient(host, user=userSsh)
        if not client.get_transport().is_alive():
            return None, None
        shl = client.invoke_shell(width=120, environment=env)
        time.sleep(0.5)
        shl.settimeout(timeout)
        _res = SshManager.sendStringRoutine(shl, strToSend, expectString, timeout)
        return _res

    def checkConnections(self, testenv):
        """
        check connections

        :param object testenv: the test env
        :raises BaseException: If the connectionis not found, raise exception

        >>> sshManager.checkConnections(testenv)
        """
        for lab in testenv.testBed.labs.values():
            client = self.getClient(lab.oamIpAddress)
            if client is None or not client.get_transport().is_alive():
                raise BaseException(CONNECTION_NOT_FOUND + lab.oamIpAddress)

    def isAlive(self, host, user=None):
        """
        check if connection still alive.

        :param str host: the remote host (IP adrs)
        :param str user: the user
        :return: value depending of the connection status
        :rtype: bool

        >>> sshManager.isALive ('lalx03si3',user='jenkins')
        """
        user = 'root' if user is None else user
        return self.getClient(host, user=user).get_transport().is_alive()

    def isDead(self, host, user=None, pw=None, heartbeat=None, timeout=120, interval=5):
        """
        Check the ssh connection down within timeout

        :param str host: the remote host (IP adrs)
        :param str user: the user
        :param str heartbeat: ssh connection keepalive value
        :param int timeout: timeout to wait the connection down
        :param int interval: sleep interval before next check
        :return: the status of the host
        :rtype: bool

        >>> sshManager.isDead(host)
        """
        dead = True
        if heartbeat:
            self.getClient(host, user, pw).get_transport().set_keepalive(heartbeat)
        while timeout > 0:
            if self.isAlive(host, user):
                LOGGER.debug("Host %s: connection alive (%d)", host, timeout)
                time.sleep(interval)
                timeout -= interval
                continue
            LOGGER.debug("Host %s: connection down (%d)", host, timeout)

            # Close the connection, so ssh lib will create it again.
            self.closeClient(host, user)
            break
        else:
            LOGGER.debug("Host %s: connection still alive (%d)", host, timeout)
            dead = False
            if heartbeat:
                self.getClient(host, user, pw).get_transport().set_keepalive(self.__class__.defaultHeartbeat)
        return dead

    @staticmethod
    def readBuffers(shl):
        """
        read stdout and stderr buffer

        :param object shl: the shl object
        :return: buff, buffErr
        :rtype: list

        >>> sshManager.readBuffers(shl)
        """
        buff = shl.recv(BUFF_SIZE) if shl.recv_ready() else ''
        buffErr = shl.recv_stderr(BUFF_SIZE)if shl.recv_stderr_ready() else ''
        return buff, buffErr


    @staticmethod
    def sendStringRoutine(channel, strToSend, expectString, timeout=1200):
        """
        run a string or command and expect a string to terminate the function. The string to wait can be
        located at end of flow (like a prompt) and in the middle of the flow (useful with subshl).
        Trailing spaces are removed to get an easier comparison.

        :param Channel channel: paramiko Channel (interactive shell)
        :param str strToSend: the command to execute or the string to send (could be a password)
        :param str-list expectString: the string to detect in  stdout to quit the function. Case sensistive
                                    You can use multiple a string or a list of string
        :param int timeout: in seconds. interrupt the function if timeout reached. Useful if expectString 
                            is not found. Default value is 20 min (1200 seconds)
        :return: a list containing timeoutReached, stdout, stderr: if timeout reached, timeoutReached is True;
                the stdout of the command, the stderr. Each one is a unique string (including EOL). 
                **A normal behaviour is timeoutReached = False**
        :rtype: list

        warning:
        The parameter expectString **must not be empty**

        Typically sendStringRoutine is used in conjonction with getClient() and a shell (or channel) 
        in order to run a command where you have to answer a question.

        Example of a scp which can last a few minutes and where you have to enter the a password.

            * we instantiate a shell with the remote client :

            >>> client = sshMgr.getClient(hp18oam.oamIpAddress)
            >>> shell = client.invoke_shell()

            * we run the scp command and we wait for the password prompt, waiting max 10 seconds for the prompt :

            >>> rcT, _out, _err = sshMgr.sendStringRoutine(shell,'scp backup_xxx.tar.gz destination:/tmp','password:', timeout=10)

            * We answer with the password and wait for the shell prompt. the scp is actually executed at this moment
            and it can last until  20 minutes. Timeout is set to half an hour.

            * if rcT (rc for timeout) is False it means that timeout has NOT been reached and thus that we got the 
            prompt line with the password input.

            if not rcT:

            >>> sshMgr.sendStringRoutine(shell,'the_password_to_enter','the_prompt', timeout=1800)
        """

        # exepectString could be a string or a list of string
        # if type(expectString)  == str:
        #    expectString = [expectString]                               # list of one elt
        if type(expectString) == list:
            expectString = [exStr.rstrip() for exStr in expectString]  # remove trailing spaces and other
            expectString = '|'.join(expectString)
        else:
            expectString = expectString.rstrip()
        patt = re.compile(expectString)

        SshManager._voidBuffers(channel)  # empty the stdout and stderr buffers
        # delete multiple trailing EOL if any. And add trailing \n if needed :
        strToSend = strToSend.rstrip() + os.linesep

        peerName = channel.getpeername()
        LOGGER.trace("send string \"" + strToSend + "\" on terminal "
                     + str(peerName) + " expecting \"" + expectString
                     + "\"")
        channel.send(strToSend)  # send the string
        time.sleep(0.5)
        time0 = int(datetime.now().strftime('%s')) + timeout
        deltaTim = 0
        # --- while loop : depending on stringAtEnd test comparison is not the same.
        # we loop while :
        #       - time is lower than timeout
        #  AND  - we dont have the expected String

        timeoutReached = False
        buff, buffErr = SshManager.readBuffers(channel)  # first, init buffer
        while deltaTim <= time0 and not re.search(patt, buff):
            buffAdd, buffErrAdd = SshManager.readBuffers(channel)
            buff += buffAdd
            buffErr += buffErrAdd
            deltaTim = int(datetime.now().strftime('%s'))
        # --- if timeout has been reached : better to empty the buffers
        if deltaTim > time0:
            SshManager._voidBuffers(channel)
            msg = "timeout " + str(timeout) + " reached for command: " + strToSend
            LOGGER.debug(msg)
            timeoutReached = True
            # raise exception and update calling methods
            # raise BaseException(msg)
        msg = "sent string \"" + strToSend + "\" on terminal "\
                + str(peerName) + ", expected \"" + expectString + "\""\
                + ", received:\nstdout: " + buff + "\nstderr: " + buffErr
        if timeoutReached:
            msg += "\nexpected string not found after a timeout of " + str(timeout) + "s"
        else:
            msg += "\nexpected string found"
        LOGGER.trace(msg)
        return [timeoutReached, buff, buffErr]

    @staticmethod
    def _closeTunnel(tunnel):
        """
        close the current tunnel

        :param str tunnel: the tunnel to be closed

        >>> self._closeTunnel(tunnel)
        """
        tunnel.process.terminate()
        # del tunnel.process
        # del tunnel.port

    @staticmethod
    def _checkTerminalReady(channel):
        """
        Check if the terminal is ready

        :param str channel: the channel
        :raises SSHException: if no interactive session was found, raise exception

        >>> self._closeTunnel(tunnel)
        """
        randomString = SshManager._generateRandomString()
        attempts = 0
        while attempts < MAX_PROMPT_ATTEMPTS:
            (_, stdout, _) = SshManager.sendStringRoutine(channel, "echo " + randomString,
                                                       randomString,
                                                       timeout=PROMPT_CONNECTION_INTERVAL)
            if randomString in stdout:
                break
        if attempts == MAX_PROMPT_ATTEMPTS:
            raise SSHException(NO_INTERACTIVE_SESSION)

    @staticmethod
    def _copyPublicKeyRootIn2Steps(client, finalUser, finalPw):
        """
        to copy public key for root to remote host. we need to login first as ainet

        :param str host: the remote host
        :param str finalUser: the final user
        :param str finalPw: pw of final User in 2 steps login (= root)

        >>> self._copyPublicKeyRootIn2Steps(client, finalUser, finalPw)
        """
        channel = client.invoke_shell()

        SshManager._checkTerminalReady(channel)

        SshManager.sendStringRoutine(channel, CMD_SU + " " + finalUser, PW_PRPT)
        SshManager.sendStringRoutine(channel, finalPw, "#")
        SshManager.sendStringRoutine(channel, 'echo ' + SshManager.publicKeyStr + ' >> '
                                   + SSH_DIR + AUTHK_FIL, ROOT_PRPT)
        SshManager.sendStringRoutine(channel, 'chmod 600 ' + SSH_DIR + AUTHK_FIL, ROOT_PRPT)

        client.close()

    @staticmethod
    def _generateRandomString():
        """
        generate Random String

        :return: the random string
        :rtype: str

        >>> self._generateRandomString()
        """
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

    @staticmethod
    def _copyPublicKey(client, exceptionMsg):
        """
        to copy public key for specified user to remote host.

        :param str client: the remote client
        :param str exceptionMsg: the exception messages
        :raises Exception: if there is public key copy error, raise exception

        >>> self._copyPublicKey(client, exceptionMsg)
        """
        LOGGER.trace("_copyPublicKey " + str(client) + ", " + SshManager.publicKeyStr)

        authFile = SSH_DIR + AUTHK_FIL
        cmd = "mkdir -p %s && echo %s >> %s && chmod 600 %s" % (SSH_DIR, SshManager.publicKeyStr, authFile, authFile)
        LOGGER.trace(cmd)
        _, stdout, stdErr = client.exec_command(cmd)
        err = stdErr.read().rstrip()
        rc = stdout.channel.recv_exit_status()
        client.close()
        if rc != 0:
            LOGGER.error(msgExc.PUBLIC_KEY_COPY_ERROR + str(rc) + " " + err + " ( " + exceptionMsg + " )")
            raise Exception(msgExc.PUBLIC_KEY_COPY_ERROR + str(rc) + " " + err + " ( " + exceptionMsg + " )")

    @staticmethod
    def _voidBuffers(chann):
        """
        void the buffers : stdout and stderr. Useful  just before a loop with a new command

        :param str chann: the channel

        >>> self._voidBuffers(chann)
        """
        while chann.recv_stderr_ready():
            chann.recv_stderr(BUFF_SIZE)
        while chann.recv_ready():
            chann.recv(BUFF_SIZE)
