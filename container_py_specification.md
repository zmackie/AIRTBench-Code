# AIRTBench container.py Comprehensive Specification

## File Overview
- **File Path**: `/Users/zander/workspace/AIRTBench-Code/airtbench/container.py`
- **Purpose**: Provides Docker container building functionality for AIRTBench
- **Lines of Code**: 50 lines
- **Module Type**: Utility module for Docker operations

## Import Dependencies Analysis

### Standard Library Imports
```python
from pathlib import Path
```
- **Purpose**: File system path manipulation with object-oriented interface
- **Usage**: Converting string paths to Path objects, checking file existence, resolving absolute paths
- **Version**: Built-in Python 3.4+ module

### Third-Party Imports
```python
import docker
```
- **Purpose**: Docker Engine API client for Python
- **Usage**: Creating Docker client connections, building images via API
- **Version**: Requires docker package installation
- **API Level**: High-level Docker SDK for Python

```python
import rich
```
- **Purpose**: Rich text and beautiful formatting in terminal
- **Usage**: Printing formatted output during build process
- **Specific Usage**: Only `rich.print()` function used for styled console output

```python
from loguru import logger
```
- **Purpose**: Advanced logging with structured output
- **Usage**: Logging build start/completion messages
- **Configuration**: Uses default loguru configuration (no custom setup in this file)

## Function: build_container

### Function Signature
```python
def build_container(
    image: str,
    docker_file: str | Path,
    build_path: str | Path = Path(),
    *,
    force_rebuild: bool = False,
) -> str:
```

### Parameter Analysis

#### Parameter: image
- **Type**: `str`
- **Purpose**: Name/tag for the Docker image to build
- **Validation**: None explicit, but processed to ensure tag format
- **Processing**: 
  - If no `:` present, `:latest` is appended
  - If `:` present, used as-is
- **Examples**: 
  - `"myapp"` becomes `"myapp:latest"`
  - `"myapp:v1.0"` remains `"myapp:v1.0"`
- **Required**: Yes (positional parameter)

#### Parameter: docker_file
- **Type**: `str | Path` (Union type)
- **Purpose**: Path to Dockerfile for building the image
- **Validation**: 
  - Converted to Path object
  - Existence check performed
  - FileNotFoundError raised if not found
- **Processing**: `Path(docker_file)` conversion
- **Required**: Yes (positional parameter)
- **Error Conditions**: Raises `FileNotFoundError` if file doesn't exist

#### Parameter: build_path
- **Type**: `str | Path` (Union type)
- **Default**: `Path()` (current working directory)
- **Purpose**: Build context directory for Docker build
- **Validation**:
  - Converted to Path object
  - Existence check performed
  - FileNotFoundError raised if not found
  - Resolved to absolute path via `.resolve()`
- **Processing**: 
  - `Path(build_path)` conversion
  - `Path(build_path).resolve()` for absolute path
- **Required**: No (has default value)
- **Error Conditions**: Raises `FileNotFoundError` if path doesn't exist

#### Parameter: force_rebuild
- **Type**: `bool`
- **Default**: `False`
- **Purpose**: Controls Docker build cache behavior
- **Usage**: 
  - When `True`: Sets `nocache=True` and `pull=True` in Docker API call
  - When `False`: Uses Docker build cache (default behavior)
- **Keyword-Only**: Yes (after `*` in signature)
- **Required**: No (has default value)

### Return Value Analysis
- **Type**: `str`
- **Content**: The complete Docker image tag that was built
- **Format**: `{image}:latest` or original `image` if already contains `:`
- **Purpose**: Allows caller to know exact tag of built image
- **Examples**:
  - Input `"myapp"` returns `"myapp:latest"`
  - Input `"myapp:v1.0"` returns `"myapp:v1.0"`

### Docker Client Initialization

#### Code Block
```python
try:
    docker_client = docker.DockerClient()
except docker.errors.DockerException as e:
    raise RuntimeError(
        "Docker connection failed: Docker is not running or not accessible",
    ) from e
```

#### Analysis
- **Purpose**: Establish connection to Docker daemon
- **Error Handling**: Catches `docker.errors.DockerException`
- **Exception Translation**: Converts Docker exceptions to `RuntimeError`
- **Error Message**: Static message about Docker not running/accessible
- **Exception Chaining**: Uses `from e` to preserve original exception
- **Failure Scenarios**:
  - Docker daemon not running
  - Docker socket not accessible
  - Insufficient permissions
  - Docker not installed

### File Path Validation

#### Dockerfile Validation
```python
docker_file = Path(docker_file)
if not docker_file.exists():
    raise FileNotFoundError(f"Dockerfile not found: {docker_file}")
```
- **Type Conversion**: Always converts to Path object
- **Validation Method**: Uses `Path.exists()` method
- **Error Type**: `FileNotFoundError`
- **Error Message**: Dynamic message including actual path
- **Path Resolution**: No absolute path resolution (uses as-provided)

#### Build Path Validation
```python
build_path = Path(build_path)
if not build_path.exists():
    raise FileNotFoundError(f"Build path not found: {build_path}")
```
- **Type Conversion**: Always converts to Path object
- **Validation Method**: Uses `Path.exists()` method
- **Error Type**: `FileNotFoundError`
- **Error Message**: Dynamic message including actual path
- **Additional Processing**: Later resolved to absolute path

### Build Context Resolution
```python
full_path = Path(build_path).resolve()
```
- **Purpose**: Convert build path to absolute path
- **Method**: Uses `Path.resolve()` 
- **Behavior**: Resolves symlinks and converts to absolute path
- **Usage**: Passed to Docker API as build context
- **Type**: `Path` object converted to string in API call

### Image Tag Processing
```python
tag = f"{image}:latest" if ":" not in image else image
```
- **Logic**: Simple string check for colon character
- **Default Tag**: `:latest` appended if no tag specified
- **Behavior**: Preserves existing tag if colon present
- **Examples**:
  - `"myapp"` → `"myapp:latest"`
  - `"myapp:v1.0"` → `"myapp:v1.0"`
  - `"registry.com/myapp"` → `"registry.com/myapp:latest"`
  - `"registry.com/myapp:dev"` → `"registry.com/myapp:dev"`

### Logging Analysis

#### Build Start Log
```python
logger.info(f"Building container {tag} from {docker_file}")
```
- **Level**: INFO
- **Message Format**: "Building container {tag} from {docker_file}"
- **Variables**: Dynamic tag and docker_file path
- **Timing**: Called immediately before Docker build starts
- **Purpose**: Record build initiation

#### Build Success Log
```python
logger.info(f"Container {tag} built successfully")
```
- **Level**: INFO
- **Message Format**: "Container {tag} built successfully"
- **Variables**: Dynamic tag
- **Timing**: Called after successful build completion
- **Purpose**: Record build completion

### Docker API Build Call

#### API Method
```python
docker_client.api.build(
    path=str(full_path),
    dockerfile=str(docker_file),
    tag=tag,
    nocache=force_rebuild,
    pull=force_rebuild,
    decode=True,
)
```

#### Parameter Analysis
- **path**: `str(full_path)` - Build context directory as absolute path string
- **dockerfile**: `str(docker_file)` - Dockerfile path as string
- **tag**: `tag` - Image tag string (processed with :latest if needed)
- **nocache**: `force_rebuild` - Boolean controlling cache usage
- **pull**: `force_rebuild` - Boolean controlling base image pulling
- **decode**: `True` - Enables JSON decoding of build output

#### API Behavior
- **Return Type**: Generator yielding build step dictionaries
- **Streaming**: Real-time build output via generator
- **Cache Control**: `nocache=True` disables Docker layer cache
- **Base Image Updates**: `pull=True` forces pull of base images
- **Output Format**: JSON objects with various keys (stream, error, etc.)

### Build Output Processing

#### Output Stream Iteration
```python
for item in docker_client.api.build(...):
```
- **Type**: Iterates over generator of dictionaries
- **Real-time**: Processes output as build progresses
- **Item Structure**: Each item is a dictionary with various keys

#### Error Handling in Output
```python
if "error" in item:
    rich.print()
    raise RuntimeError(item["error"])
```
- **Error Detection**: Checks for "error" key in output item
- **Error Display**: Calls `rich.print()` with no arguments (prints newline)
- **Exception Type**: Raises `RuntimeError`
- **Error Message**: Uses exact error text from Docker
- **Termination**: Immediately stops build process on error

#### Stream Output Display
```python
if "stream" in item:
    rich.print("[dim]" + item["stream"].strip() + "[/]")
```
- **Stream Detection**: Checks for "stream" key in output item
- **Text Processing**: Strips whitespace from stream content
- **Formatting**: Wraps in Rich markup `[dim]...[/]` for dimmed display
- **Output Method**: Uses `rich.print()` for styled console output
- **Purpose**: Show real-time build progress to user

## Error Conditions and Exception Handling

### Docker Connection Errors
- **Exception Type**: `docker.errors.DockerException`
- **Handling**: Converted to `RuntimeError`
- **Message**: "Docker connection failed: Docker is not running or not accessible"
- **Chaining**: Original exception preserved with `from e`

### File Not Found Errors
- **Dockerfile Missing**: 
  - Exception: `FileNotFoundError`
  - Message: f"Dockerfile not found: {docker_file}"
- **Build Path Missing**:
  - Exception: `FileNotFoundError`
  - Message: f"Build path not found: {build_path}"

### Docker Build Errors
- **Detection**: "error" key in build output
- **Exception Type**: `RuntimeError`
- **Message**: Direct error text from Docker
- **Timing**: Can occur at any point during build

## Data Structure Lifecycle

### Path Objects
1. **Creation**: String parameters converted to `Path` objects
2. **Validation**: Existence checked via `.exists()`
3. **Resolution**: Build path resolved to absolute path via `.resolve()`
4. **Usage**: Converted back to strings for Docker API calls

### Docker Client
1. **Initialization**: Created via `docker.DockerClient()`
2. **Validation**: Connection tested in try/catch block
3. **Usage**: API accessed via `.api.build()` method
4. **Lifecycle**: No explicit cleanup (relies on Python garbage collection)

### Build Output Items
1. **Generation**: Yielded from Docker API build generator
2. **Processing**: Each item checked for "error" and "stream" keys
3. **Display**: Stream content formatted and printed
4. **Disposal**: Items processed once and discarded

## Configuration Options and Defaults

### Function Parameters
- **build_path**: Defaults to `Path()` (current working directory)
- **force_rebuild**: Defaults to `False` (use cache)

### Docker API Parameters
- **nocache**: Controlled by `force_rebuild` parameter
- **pull**: Controlled by `force_rebuild` parameter  
- **decode**: Hardcoded to `True`

### Image Tagging
- **Default Tag**: `:latest` appended if no tag specified
- **Tag Preservation**: Existing tags preserved

## Control Flow Analysis

### Linear Execution Flow
1. **Parameter Processing**: Convert and validate inputs
2. **Docker Connection**: Establish client connection
3. **Path Validation**: Verify Dockerfile and build path exist
4. **Path Resolution**: Convert build path to absolute
5. **Tag Processing**: Ensure image has tag
6. **Logging**: Log build initiation
7. **Docker Build**: Execute build via API
8. **Output Processing**: Handle real-time build output
9. **Success Logging**: Log successful completion
10. **Return**: Return final image tag

### Decision Points
1. **Docker Connection**: Success/failure determines continuation
2. **File Existence**: Each missing file stops execution
3. **Tag Format**: Colon presence determines tag processing
4. **Build Output**: Error vs stream vs other content
5. **Build Completion**: Success vs error determines final outcome

### Error Exit Points
1. **Docker connection failure** → RuntimeError
2. **Dockerfile not found** → FileNotFoundError  
3. **Build path not found** → FileNotFoundError
4. **Docker build error** → RuntimeError (from build output)

## External Dependencies and API Usage

### Docker Engine API
- **Package**: `docker` Python package
- **Client**: `docker.DockerClient()`
- **API Level**: Low-level API via `.api.build()`
- **Authentication**: Uses default Docker configuration
- **Connection**: Local Docker socket or configured remote

### File System API
- **Package**: `pathlib.Path` (standard library)
- **Operations**: 
  - `.exists()` for validation
  - `.resolve()` for absolute paths
  - String conversion for API calls

### Logging Framework
- **Package**: `loguru`
- **Logger**: Default logger instance
- **Levels**: INFO level only
- **Configuration**: Uses default loguru setup

### Terminal Output
- **Package**: `rich`
- **Function**: `rich.print()`
- **Formatting**: Markup for dimmed text display
- **Usage**: Real-time build output and newlines

## Security Considerations

### Path Validation
- **Dockerfile Path**: Validated for existence only
- **Build Path**: Validated for existence and resolved to absolute
- **No Path Traversal Protection**: No explicit checks for path traversal attacks

### Docker API Access
- **Privileges**: Uses default Docker permissions
- **Build Context**: Entire build_path directory accessible to Docker
- **Network Access**: Docker can access network during build (if pull=True)

### Input Validation
- **Image Name**: No validation of image name format
- **Dockerfile Content**: No validation of Dockerfile content
- **Build Context**: No filtering of build context files

## Performance Characteristics

### Memory Usage
- **Streaming Output**: Build output processed incrementally
- **Path Objects**: Minimal memory footprint
- **Docker Client**: Maintains connection state

### I/O Operations
- **File System**: Multiple existence checks via `.exists()`
- **Docker Socket**: Streaming communication with Docker daemon
- **Terminal Output**: Real-time printing of build progress

### Build Performance
- **Cache Control**: Configurable via `force_rebuild` parameter
- **Base Image Pulling**: Controlled by `force_rebuild` parameter
- **Parallel Processing**: Limited to Docker daemon capabilities

## Integration Points

### Caller Interface
- **Input**: Image name, Dockerfile path, build path, rebuild flag
- **Output**: Final image tag string
- **Exceptions**: Various exception types for different failures

### Docker Integration
- **Build Context**: Directory-based build context
- **Output Streaming**: Real-time build progress
- **Error Propagation**: Docker errors converted to Python exceptions

### Logging Integration
- **Framework**: Uses loguru logger
- **Levels**: INFO level for normal operations
- **Format**: String interpolation with dynamic values

### Terminal Integration
- **Output Library**: Rich for styled output
- **Real-time Display**: Streaming build output
- **Error Display**: Newline insertion before errors

## Future Enhancement Opportunities

### Error Handling
- **More Specific Exceptions**: Different exception types for different Docker errors
- **Validation Enhancement**: Path traversal protection, image name validation
- **Retry Logic**: Automatic retry for transient Docker failures

### Configuration
- **Docker Client Options**: Timeout, base URL, TLS configuration
- **Build Options**: Additional Docker build parameters
- **Output Control**: Configurable output verbosity

### Performance
- **Build Caching**: More sophisticated cache control
- **Parallel Builds**: Support for multiple concurrent builds
- **Progress Tracking**: Percentage completion for builds

### Security
- **Input Sanitization**: Validation of all input parameters
- **Build Context Filtering**: Exclude sensitive files from build context
- **Privilege Control**: Support for rootless Docker builds