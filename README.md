# immudb_wrapper

The wrapper around the SDK client `immudb-py` from project Codenotary, which expands the functionality of the original client with additional functions.

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Contribution](#contribution)

## Requirements

- python >= 3.7
- immudb-py >= 1.4.0
- GitPython >= 3.1.20

## Installation

You can easily install `immudb_wrapper` into your environment with the following command:

```
pip install git+https://git.almalinux.org/danfimov/immudb_wrapper.git@<tag|branch>#egg=immudb_wrapper
```

To run the `immudb` instance locally, you can use the options from `immudb` [documentation](https://docs.immudb.io/master/running/download.html).

If you want to use the `immudb` in `docker-compose.yml`, you can add the following in your compose file:

```
  immudb:
    image: codenotary/immudb:latest
    ports:
      - 3322:3322
      - 9497:9497
    volumes:
      - "../volumes/immudb/data:/var/lib/immudb"
      - "../volumes/immudb/config:/etc/immudb"
      - "../volumes/immudb/logs:/var/log/immudb"
```

## Usage

### Client initialization

```python3
client = ImmudbWrapper(
    username="user",
    password="password",
    database="database",
)
```

### File notarization

This method calculates the file hash and file size and inserts them with the user's metadata (if provided), into the database.

```python3
response = client.notarize_file(
    "./hello_world.sh",
     user_metadata={
        "foo": "bar",
    },
)
print(response)
{
    'id': 1,
    'key': '4db5767d4bf4221a5656b163ef1bae833095255f80d1ad5be21dfef84caf4126',
    'value': {
        'Name': 'hello_world.sh',
        'Kind': 'file',
        'Size': '2.62 KB',
        'Hash': '4db5767d4bf4221a5656b163ef1bae833095255f80d1ad5be21dfef84caf4126',
        'Metadata': {
            'sbom_api_ver': '0.2',
            'foo': 'bar',
        },
    },
    'timestamp': 1690794033,
    'verified': True,
    'refkey': None,
    'revision': 1,
}
```

### Git repo notarization

This method extracts the git metadata from a provided git directory, calculates the hash of the extracted metadata and inserts that metadata with the user's metadata (if provided), into the database. Falls with a `InvalidGitRepositoryError` when accepting non-git directories.

```python3
response = client.notarize_git_repo(
    "./immudb_wrapper/",
     user_metadata={
        "foo": "bar",
    },
)
print(response)
{
    'id': 2,
    'key': 'a87f7a948900e04812c095fb457e994926fc28c2a789471521fcc076cc4d8658',
    'value': {
        'Name': 'git@git.almalinux.org:danfimov/immudb_wrapper.git@c093e0f',
        'Kind': 'git',
        'Size': '30.52 KB',
        'Hash': 'a87f7a948900e04812c095fb457e994926fc28c2a789471521fcc076cc4d8658',
        'Metadata': {
            'git': {
                'Author': {
                    'Email': 'anfimovdan@gmail.com',
                    'Name': 'Daniil Anfimov',
                    'When': '2023-07-22T12:53:22+0200',
                },
                'Commit': 'c093e0f468c2810f76d4c09c340c58380bd965b1',
                'Committer': {
                    'Email': 'anfimovdan@gmail.com',
                    'Name': 'Daniil Anfimov',
                    'When': '2023-07-22T12:53:22+0200',
                },
                'Message': 'Initial commit\n',
                'PGPSignature': '',
                'Parents': [],
                'Tree': '4526550b9c6b77e7e10f6e57dfecfe0504c5166f',
            },
            'sbom_api_ver': '0.2',
            'foo': 'bar',
        },
    },
    'timestamp': 1690794260,
    'verified': True,
    'refkey': None,
    'revision': 1,
}
```

### Git repo authentication

This method extracts the git metadata from a provided git directory, calculates the hash of the extracted metadata, and looks up the metadata of that hash in the database. Returns a dict with an error if metadata doesn't exist in the database.

```python3
response = client.authenticate_git_repo("./immudb_wrapper/")
print(response)
{
    'id': 2,
    'key': 'a87f7a948900e04812c095fb457e994926fc28c2a789471521fcc076cc4d8658',
    'value': {
        'Name': 'git@git.almalinux.org:danfimov/immudb_wrapper.git@c093e0f',
        'Kind': 'git',
        'Size': '30.52 KB',
        'Hash': 'a87f7a948900e04812c095fb457e994926fc28c2a789471521fcc076cc4d8658',
        'Metadata': {
            'git': {
                'Author': {
                    'Email': 'anfimovdan@gmail.com',
                    'Name': 'Daniil Anfimov',
                    'When': '2023-07-22T12:53:22+0200',
                },
                'Commit': 'c093e0f468c2810f76d4c09c340c58380bd965b1',
                'Committer': {
                    'Email': 'anfimovdan@gmail.com',
                    'Name': 'Daniil Anfimov',
                    'When': '2023-07-22T12:53:22+0200',
                },
                'Message': 'Initial commit\n',
                'PGPSignature': '',
                'Parents': [],
                'Tree': '4526550b9c6b77e7e10f6e57dfecfe0504c5166f',
            },
            'sbom_api_ver': '0.2',
            'foo': 'bar',
        },
    },
    'timestamp': 1690794260,
    'verified': True,
    'refkey': None,
    'revision': 1,
}

response = client.authenticate_git_repo("./immudb_wrapper_foobar/")
print(response)
{'error': 'Traceback (most recent call last):\n'
          '  File "/code/env/bin/immudb_wrapper.py", line 247, in '
          'verified_get\n'
          '    self.verifiedGet(\n'
          '  File "/code/env/lib/python3.9/site-packages/immudb/client.py", '
          'line 667, in verifiedGet\n'
          '    return verifiedGet.call(self._stub, self._rs, key, '
          'verifying_key=self._vk, atRevision=atRevision)\n'
          '  File '
          '"/code/env/lib/python3.9/site-packages/immudb/handler/verifiedGet.py", '
          'line 30, in call\n'
          '    ventry = service.VerifiableGet(req)\n'
          '  File '
          '"/code/env/lib64/python3.9/site-packages/grpc/_interceptor.py", '
          'line 247, in __call__\n'
          '    response, ignored_call = self._with_call(request,\n'
          '  File '
          '"/code/env/lib64/python3.9/site-packages/grpc/_interceptor.py", '
          'line 290, in _with_call\n'
          '    return call.result(), call\n'
          '  File "/code/env/lib64/python3.9/site-packages/grpc/_channel.py", '
          'line 379, in result\n'
          '    raise self\n'
          '  File '
          '"/code/env/lib64/python3.9/site-packages/grpc/_interceptor.py", '
          'line 274, in continuation\n'
          '    response, call = self._thunk(new_method).with_call(\n'
          '  File "/code/env/lib64/python3.9/site-packages/grpc/_channel.py", '
          'line 1043, in with_call\n'
          '    return _end_unary_response_blocking(state, call, True, None)\n'
          '  File "/code/env/lib64/python3.9/site-packages/grpc/_channel.py", '
          'line 910, in _end_unary_response_blocking\n'
          '    raise _InactiveRpcError(state)  # pytype: '
          'disable=not-instantiable\n'
          'grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that '
          'terminated with:\n'
          '\tstatus = StatusCode.UNKNOWN\n'
          '\tdetails = "tbtree: key not found"\n'
          '\tdebug_error_string = "UNKNOWN:Error received from peer '
          'ipv4:172.18.0.2:3322 {grpc_message:"tbtree: key not found", '
          'grpc_status:2, '
          'created_time:"2023-07-31T09:13:55.947555151+00:00"}"\n'
          '>\n'}
```

### File authentication

This method calculates the file hash of the provided file and looks up the metadata of that hash in the database. Returns a dict with an error if metadata doesn't exist in the database.

```python3
response = client.authenticate_file("./hello_world.sh")
print(response)
{
    'id': 1,
    'key': '4db5767d4bf4221a5656b163ef1bae833095255f80d1ad5be21dfef84caf4126',
    'value': {
        'Name': 'hello_world.sh',
        'Kind': 'file',
        'Size': '2.62 KB',
        'Hash': '4db5767d4bf4221a5656b163ef1bae833095255f80d1ad5be21dfef84caf4126',
        'Metadata': {
            'sbom_api_ver': '0.2',
            'foo': 'bar',
        },
    },
    'timestamp': 1690794033,
    'verified': True,
    'refkey': None,
    'revision': 1,
}

response = client.authenticate_file("./hello_world1.sh")
print(response)
{'error': 'Traceback (most recent call last):\n'
          '  File "/code/env/bin/immudb_wrapper.py", line 247, in '
          'verified_get\n'
          '    self.verifiedGet(\n'
          '  File "/code/env/lib/python3.9/site-packages/immudb/client.py", '
          'line 667, in verifiedGet\n'
          '    return verifiedGet.call(self._stub, self._rs, key, '
          'verifying_key=self._vk, atRevision=atRevision)\n'
          '  File '
          '"/code/env/lib/python3.9/site-packages/immudb/handler/verifiedGet.py", '
          'line 30, in call\n'
          '    ventry = service.VerifiableGet(req)\n'
          '  File '
          '"/code/env/lib64/python3.9/site-packages/grpc/_interceptor.py", '
          'line 247, in __call__\n'
          '    response, ignored_call = self._with_call(request,\n'
          '  File '
          '"/code/env/lib64/python3.9/site-packages/grpc/_interceptor.py", '
          'line 290, in _with_call\n'
          '    return call.result(), call\n'
          '  File "/code/env/lib64/python3.9/site-packages/grpc/_channel.py", '
          'line 379, in result\n'
          '    raise self\n'
          '  File '
          '"/code/env/lib64/python3.9/site-packages/grpc/_interceptor.py", '
          'line 274, in continuation\n'
          '    response, call = self._thunk(new_method).with_call(\n'
          '  File "/code/env/lib64/python3.9/site-packages/grpc/_channel.py", '
          'line 1043, in with_call\n'
          '    return _end_unary_response_blocking(state, call, True, None)\n'
          '  File "/code/env/lib64/python3.9/site-packages/grpc/_channel.py", '
          'line 910, in _end_unary_response_blocking\n'
          '    raise _InactiveRpcError(state)  # pytype: '
          'disable=not-instantiable\n'
          'grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that '
          'terminated with:\n'
          '\tstatus = StatusCode.UNKNOWN\n'
          '\tdetails = "tbtree: key not found"\n'
          '\tdebug_error_string = "UNKNOWN:Error received from peer '
          'ipv4:172.18.0.2:3322 {grpc_message:"tbtree: key not found", '
          'grpc_status:2, '
          'created_time:"2023-07-31T09:13:55.947555151+00:00"}"\n'
          '>\n'}
```

### User creation

```python3
from immudb.constants import (
    PERMISSION_SYS_ADMIN,
    PERMISSION_ADMIN,
    PERMISSION_NONE,
    PERMISSION_R,
    PERMISSION_RW,
)

# See the "ImmudbClient.createUser" method
# https://github.com/codenotary/immudb-py/blob/master/immudb/client.py
client.createUser(
    user='username',
    password='password',
    permission=PERMISSION_RW,
)
```

### Changing password

```python3
# See the "ImmudbClient.changePassword" method
# https://github.com/codenotary/immudb-py/blob/master/immudb/client.py
client.changePassword(
    user='username',
    newPassword='new_password',
    oldPassword='old_password',
)
```

### Database creation

```python3
# See the "ImmudbClient.createDatabase" or "ImmudbClient.createDatabaseV2" methods
# https://github.com/codenotary/immudb-py/blob/master/immudb/client.py
# https://github.com/codenotary/immudb-py/blob/master/immudb/datatypesv2.py
from immudb.datatypesv2 import DatabaseSettingsV2

client.createDatabase(
    dbName=b'database',
)

client.createDatabaseV2(
    name='database',
    settings=DatabaseSettingsV2(...),
    ifNotExists=True,
)
```

## Contribution

If you wish to contribute to `immudb_wrapper`, just create a fork and make a PR.
