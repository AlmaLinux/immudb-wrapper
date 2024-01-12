import hashlib
import json
import logging
import os
import re
from dataclasses import asdict
from functools import wraps
from pathlib import Path
from time import sleep
from traceback import format_exc
from typing import IO, Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from git import Repo
from grpc import RpcError
from grpc._channel import _InactiveRpcError
from immudb import ImmudbClient
from immudb.datatypes import SafeGetResponse
from immudb.rootService import RootService

Dict = Dict[str, Any]


class ImmudbWrapper(ImmudbClient):
    def __init__(
        self,
        username: str = 'immudb',
        password: str = 'immudb',
        database: str = 'defaultdb',
        immudb_address: Optional[str] = 'localhost:3322',
        root_service: Optional[RootService] = None,
        public_key_file: Optional[str] = None,
        timeout: Optional[int] = None,
        max_grpc_message_length: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
        max_retries: int = 5,
        retry_timeout: int = 10,
    ):
        """
        The wrapper around binary `immuclient` from Codenotary.

        Args:
            username (str): Immudb username to log in (default: "immudb").
            password (str): Immudb password to log in (default: "immudb").
            database (str): Immudb database to be used (default: "defaultdb").
            immudb_address (str, optional): url in format ``host:port``
                (e.g. ``localhost:3322``) of your immudb instance.
                Defaults to ``localhost:3322`` when no value is set.
            root_service (RootService, optional): object that implements
                RootService, allowing requests to be verified. Optional.
                By default in-memory RootService instance will be created
            public_key_file (str, optional): path of the public key to use
                for authenticating requests. Optional.
            timeout (int, optional): global timeout for GRPC requests. Requests
                will hang until the server responds if no timeout is set.
            max_grpc_message_length (int, optional): maximum size of message
                the server should send. The default (4Mb) is used if no
                value is set.
            logger (logging.Logger, optional): Logger to be used
            max_retries (int, optional): maximum number of retries (default: 5)
            retry_timeout (int, optional): timeout after a retry,
                time in seconds (default: 10)
        """
        self.username = username
        self.password = password
        self.database = database
        self.max_retries = max_retries
        self.retry_timeout = retry_timeout
        self.logger = logger
        if not logger:
            self.logger = logging.getLogger()
        super().__init__(
            immudUrl=immudb_address,
            rs=root_service,
            publicKeyFile=public_key_file,
            timeout=timeout,
            max_grpc_message_length=max_grpc_message_length,
        )
        self.login()

    def retry(possible_exc_details: Optional[List[str]] = None):
        if not possible_exc_details:
            possible_exc_details = []

        def wrapper(func):
            @wraps(func)
            def wrapped(self, *args, **kwargs):
                max_retries = self.max_retries
                last_exc = Exception()
                while max_retries:
                    try:
                        return func(self, *args, **kwargs)
                    except _InactiveRpcError as exc:
                        exc_details = exc.details()
                        last_exc = exc
                        if exc_details and any(
                            detail in exc_details
                            for detail in possible_exc_details
                        ):
                            max_retries -= 1
                            self.logger.error(
                                'Running the "%s" function again after %d'
                                ' seconds',
                                func.__name__,
                                self.retry_timeout,
                            )
                            sleep(self.retry_timeout)
                            continue
                        raise
                raise last_exc

            return wrapped

        return wrapper

    def login(self):
        encoded_database = self.encode(self.database)
        super().login(
            username=self.username,
            password=self.password,
            database=encoded_database,
        )
        self.useDatabase(encoded_database)

    @classmethod
    def get_version(cls) -> str:
        return '0.1.2'

    @classmethod
    def read_only_username(cls) -> str:
        return 'sbom_public_almalinux'

    @classmethod
    def read_only_password(cls) -> str:
        return '%VF%414Ibmsk'

    @classmethod
    def almalinux_database_address(cls) -> str:
        return 'pulpdb01.awsuseast1.almalinux.org:3322'

    @classmethod
    def almalinux_database_name(cls) -> str:
        return 'almalinux'

    def encode(
        self,
        value: Union[str, bytes, dict],
    ) -> bytes:
        if isinstance(value, str):
            result = value.encode()
        elif isinstance(value, bytes):
            result = value
        elif isinstance(value, dict):
            result = json.dumps(value).encode()
        else:
            raise ValueError(
                "Cannot encode value that isn't str, bytes or dict."
            )
        return result

    def to_dict(
        self,
        response: SafeGetResponse,
    ) -> Dict:
        result = asdict(response)
        result['key'] = result['key'].decode()
        result['value'] = json.loads(result['value'].decode())
        return result

    def get_size_format(
        self,
        value: int,
        factor: int = 1024,
        suffix: str = "B",
    ) -> str:
        """
        Scale bytes to its proper byte format
        e.g:
            1253656 => '1.20 MB'
            1253656678 => '1.17 GB'
        """
        for unit in [
            '',
            'K',
            'M',
            'G',
            'T',
            'P',
            'E',
            'Z',
        ]:
            if value < factor:
                return f'{value:.2f} {unit}{suffix}'
            value /= factor
        return f'{value:.2f} Y{suffix}'

    def get_directory_size(self, path: Union[str, os.PathLike]) -> int:
        return sum(file.stat().st_size for file in Path(path).rglob('*'))

    def get_file_size(self, file_path: Union[str, os.PathLike]) -> int:
        return Path(file_path).stat().st_size

    def get_hasher(self, checksum_type: str = 'sha256'):
        """
        Returns a corresponding hashlib hashing function for the specified
        checksum type.

        Parameters
        ----------
        checksum_type : str
            Checksum type (e.g. sha1, sha256).

        Returns
        -------
        hashlib._Hash
            Hashlib hashing function.
        """
        return hashlib.new(checksum_type)

    def hash_file(
        self,
        file_path: Union[str, IO],
        hash_type: str = 'sha256',
        buff_size: int = 1048576,
        hasher=None,
    ) -> str:
        """
        Returns checksum (hexadecimal digest) of the file.

        Parameters
        ----------
        file_path : str or file-like
            File to hash. It could be either a path or a file descriptor.
        hash_type : str
            Hash type (e.g. sha1, sha256).
        buff_size : int
            Number of bytes to read at once.
        hasher : hashlib._Hash
            Any hash algorithm from hashlib.

        Returns
        -------
        str
            Checksum (hexadecimal digest) of the file.
        """
        if hasher is None:
            hasher = self.get_hasher(hash_type)

        def feed_hasher(_fd):
            buff = _fd.read(buff_size)
            while len(buff):
                if not isinstance(buff, bytes):
                    buff = buff.encode()
                hasher.update(buff)
                buff = _fd.read(buff_size)

        if isinstance(file_path, str):
            with open(file_path, 'rb') as fd:
                feed_hasher(fd)
        else:
            file_path.seek(0)
            feed_hasher(file_path)
        return hasher.hexdigest()

    def hash_content(
        self,
        content: Union[str, bytes],
    ) -> str:
        hasher = self.get_hasher()
        if isinstance(content, str):
            content = content.encode()
        hasher.update(content)
        return hasher.hexdigest()

    @staticmethod
    def extract_git_metadata(
        repo_path: Union[str, os.PathLike],
    ) -> Dict:
        with Repo(repo_path) as repo:
            url = urlparse(repo.remote().url)
            commit = repo.commit()
            name = (
                f'git@{url.netloc}'
                f'{re.sub(r"^/", ":", url.path)}'
                f'@{commit.hexsha[:7]}'
            )
            return {
                'Name': name,
                'git': {
                    'Author': {
                        'Email': commit.author.email,
                        'Name': commit.author.name,
                        'When': commit.authored_datetime.strftime(
                            '%Y-%m-%dT%H:%M:%S%z',
                        ),
                    },
                    'Commit': commit.hexsha,
                    'Committer': {
                        'Email': commit.committer.email,
                        'Name': commit.committer.name,
                        'When': commit.committed_datetime.strftime(
                            '%Y-%m-%dT%H:%M:%S%z',
                        ),
                    },
                    'Message': commit.message,
                    'PGPSignature': commit.gpgsig,
                    'Parents': [
                        parent.hexsha for parent in commit.iter_parents()
                    ],
                    'Tree': commit.tree.hexsha,
                },
            }

    @property
    def default_metadata(self) -> Dict:
        return {
            'sbom_api_ver': '0.2',
        }

    def verified_get(
        self,
        key: Union[str, bytes],
        revision: Optional[int] = None,
    ) -> Dict:
        try:
            return self.to_dict(
                self.verifiedGet(
                    key=self.encode(key),
                    atRevision=revision,
                ),
            )
        except RpcError:
            return {'error': format_exc()}

    def verified_set(
        self,
        key: Union[str, bytes],
        value: Union[str, bytes, Dict],
    ) -> Dict:
        try:
            return asdict(
                self.verifiedSet(
                    key=self.encode(key),
                    value=self.encode(value),
                ),
            )
        except RpcError:
            return {'error': format_exc()}

    @retry(possible_exc_details=['Connection timed out'])
    def notarize(
        self,
        key: str,
        value: Union[str, bytes, Dict],
    ) -> Dict:
        self.login()
        result = self.verified_set(key, value)
        if 'error' in result:
            return result
        return self.verified_get(key)

    def notarize_file(
        self,
        file: str,
        user_metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        This method calculates the file hash and file size and inserts them
        with the user's metadata (if provided), into the database.
        """
        if not user_metadata:
            user_metadata = {}
        hash_file = self.hash_file(file)
        payload = {
            'Name': Path(file).name,
            'Kind': 'file',
            'Size': self.get_size_format(self.get_file_size(file)),
            'Hash': hash_file,
            'Signer': self.username,
            'Metadata': {
                **self.default_metadata,
                **user_metadata,
            },
        }
        return self.notarize(
            key=hash_file,
            value=payload,
        )

    def notarize_git_repo(
        self,
        repo_path: Union[str, os.PathLike],
        user_metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        This method extracts the git metadata from a provided git directory,
        calculates the hash of the extracted metadata and inserts that
        metadata with the user's metadata (if provided), into the database.
        Falls with a `InvalidGitRepositoryError` when
        accepting non-git directories.
        """
        if not user_metadata:
            user_metadata = {}
        git_metadata = self.extract_git_metadata(repo_path)
        metadata_hash = self.hash_content(json.dumps(git_metadata['git']))
        payload = {
            'Name': git_metadata['Name'],
            'Kind': 'git',
            'Size': self.get_size_format(self.get_directory_size(repo_path)),
            'Hash': metadata_hash,
            'Signer': self.username,
            'Metadata': {
                'git': git_metadata['git'],
                **self.default_metadata,
                **user_metadata,
            },
        }
        return self.notarize(
            key=metadata_hash,
            value=payload,
        )

    @retry(possible_exc_details=['Connection timed out'])
    def authenticate(
        self,
        key: Union[str, bytes],
    ) -> Dict:
        self.login()
        return self.verified_get(key)

    def authenticate_file(self, file: str) -> Dict:
        """
        This method calculates the file hash of the provided file
        and looks up the metadata of that hash in the database.
        Returns a dict with an error if metadata doesn't exist in the database.
        """
        return self.authenticate(self.hash_file(file))

    def authenticate_git_repo(
        self,
        repo_path: Union[str, os.PathLike],
    ) -> Dict:
        """
        This method extracts the git metadata from a provided git directory,
        calculates the hash of the extracted metadata, and looks up
        the metadata of that hash in the database.
        Returns a dict with an error if metadata doesn't exist in the database.
        """
        metadata_hash = self.hash_content(
            json.dumps(
                self.extract_git_metadata(repo_path)['git'],
            ),
        )
        return self.authenticate(metadata_hash)
