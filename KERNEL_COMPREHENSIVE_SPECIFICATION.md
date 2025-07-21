# AIRTBench Kernel.py Comprehensive Specification

## Table of Contents
1. [Overview](#overview)
2. [External Dependencies](#external-dependencies)
3. [Type Definitions](#type-definitions)
4. [Data Models](#data-models)
5. [Exception Classes](#exception-classes)
6. [PythonKernel Class](#pythonkernel-class)
7. [Utility Functions](#utility-functions)
8. [Control Flow Analysis](#control-flow-analysis)
9. [Resource Management](#resource-management)
10. [Error Handling](#error-handling)
11. [Security Considerations](#security-considerations)

## Overview

The `kernel.py` module implements a Python kernel execution system using Docker containers and Jupyter server infrastructure. It provides complete management of containerized Python execution environments with WebSocket-based communication for real-time code execution.

**Core Purpose**: Execute Python code in isolated Docker containers through Jupyter kernels with full notebook support.

**Key Capabilities**:
- Docker container lifecycle management
- Jupyter server orchestration  
- WebSocket-based kernel communication
- Notebook parsing and execution
- Memory and resource management
- Comprehensive error handling and logging

## External Dependencies

### Core Dependencies
- **asyncio**: Asynchronous programming support for concurrent operations
- **shutil**: File system utilities for cleanup operations
- **tempfile**: Temporary directory creation for container bind mounts
- **types**: Type annotations for proper exception handling
- **typing**: Type hints and generic type support
- **uuid**: Unique identifier generation for tokens and message IDs
- **pathlib.Path**: Modern file path handling

### Third-Party Dependencies
- **aiodocker**: Async Docker client for container management
  - `aiodocker.Docker`: Main Docker client class
  - `aiodocker.containers.DockerContainer`: Container object interface
  - `aiodocker.types.JSONObject`: Type hints for Docker API payloads
  - `aiodocker.exceptions.DockerError`: Docker-specific exceptions
- **aiohttp**: Async HTTP client for Jupyter API communication
  - `aiohttp.ClientSession`: HTTP session management
  - `aiohttp.ClientTimeout`: Request timeout configuration
- **tenacity**: Retry logic for robust service startup
  - `tenacity.retry`: Decorator for retry behavior
  - `tenacity.stop_after_delay`: Stop condition by time
  - `tenacity.wait_fixed`: Fixed wait interval between retries
- **loguru**: Structured logging with automatic exception capture
- **pydantic**: Data validation and serialization with BaseModel

### Internal Dependencies
- **util.strip_ansi_codes**: ANSI escape sequence removal from output text

## Type Definitions

### Core Type Aliases
```python
AnyDict = dict[str, t.Any]
```
- **Purpose**: Flexible dictionary type for JSON-like data structures
- **Usage**: Jupyter message content, notebook metadata, API responses
- **Validation**: No runtime validation, relies on external API contracts

```python
KernelState = t.Literal["starting", "idle", "busy"]
```
- **Purpose**: Represents current execution state of Jupyter kernel
- **States**:
  - `"starting"`: Kernel is initializing (transitional state)
  - `"idle"`: Kernel ready to execute code
  - `"busy"`: Kernel actively executing code
- **Source**: Jupyter kernel protocol specification

## Data Models

### NotebookCell Class

```python
class NotebookCell(BaseModel):
    cell_type: t.Literal["code", "markdown", "raw"]
    source: str | list[str]
    metadata: AnyDict = {}
    outputs: list[AnyDict] = []
    execution_count: int | None = None
```

**Purpose**: Represents a single cell in a Jupyter notebook with full type safety.

**Attributes Analysis**:

#### cell_type: t.Literal["code", "markdown", "raw"]
- **Type**: Restricted string literal
- **Validation**: Pydantic ensures only valid cell types
- **Purpose**: Determines cell rendering and execution behavior
- **Required**: Yes (no default value)

#### source: str | list[str]
- **Type**: Single string or list of strings
- **Purpose**: Contains the actual cell content (code, markdown, or raw text)
- **Format**: List format preserves line-by-line structure from .ipynb files
- **Conversion**: Handled automatically during execution (joined to single string)
- **Required**: Yes (no default value)

#### metadata: AnyDict = {}
- **Type**: Dictionary with string keys and any values
- **Default**: Empty dictionary
- **Purpose**: Stores cell-specific metadata (execution timing, cell IDs, etc.)
- **Mutability**: Can be modified after creation
- **Jupyter Integration**: Preserved during notebook operations

#### outputs: list[AnyDict] = []
- **Type**: List of dictionaries representing execution outputs
- **Default**: Empty list
- **Purpose**: Stores execution results, stream output, errors, and display data
- **Format**: Follows Jupyter notebook format specification
- **Lifecycle**: Cleared before execution, populated during execution

#### execution_count: int | None = None
- **Type**: Optional integer
- **Default**: None (unexecuted cells)
- **Purpose**: Sequential number assigned by Jupyter kernel
- **Behavior**: Increments with each successful code execution
- **Reset**: Set to None when notebook is cleared

**Class Methods**:

#### from_source(cls, source: str | list[str]) -> "NotebookCell"
- **Purpose**: Factory method for creating code cells
- **Input**: Source code as string or list of strings
- **Returns**: NotebookCell with cell_type="code" and empty outputs
- **Usage**: Programmatic cell creation without manual field specification
- **Side Effects**: None

### Notebook Class

```python
class Notebook(BaseModel):
    cells: list[NotebookCell] = field(default_factory=list)
    metadata: AnyDict = field(default_factory=dict)
    nbformat: int = 4
    nbformat_minor: int = 5
```

**Purpose**: Represents a complete Jupyter notebook with cells and metadata.

**Attributes Analysis**:

#### cells: list[NotebookCell] = field(default_factory=list)
- **Type**: List of NotebookCell objects
- **Default**: Empty list (created fresh for each instance)
- **Purpose**: Contains all notebook cells in execution order
- **Validation**: Each cell validated by NotebookCell model
- **Mutability**: Supports addition, modification, deletion

#### metadata: AnyDict = field(default_factory=dict)
- **Type**: Dictionary for notebook-level metadata
- **Default**: Empty dictionary (created fresh for each instance)
- **Purpose**: Stores kernel specifications, language info, execution metadata
- **Examples**: Kernel name, language version, execution environment

#### nbformat: int = 4
- **Type**: Integer
- **Default**: 4 (current Jupyter notebook format version)
- **Purpose**: Specifies notebook format version for compatibility
- **Immutable**: Should not be changed after creation

#### nbformat_minor: int = 5
- **Type**: Integer  
- **Default**: 5 (current minor version)
- **Purpose**: Specifies minor format version for feature compatibility
- **Immutable**: Should not be changed after creation

**Class Methods**:

#### from_source(cls, source: str | list[str]) -> "Notebook"
- **Purpose**: Factory method for creating single-cell notebooks
- **Input**: Source code as string or list of strings
- **Returns**: Notebook containing one code cell with the provided source
- **Usage**: Quick notebook creation for code execution
- **Implementation**: Uses NotebookCell.from_source internally

#### load(cls, path: Path | str) -> "Notebook"
- **Purpose**: Load notebook from .ipynb file
- **Input**: File path as Path object or string
- **Returns**: Fully validated Notebook object
- **Validation**: Full Pydantic validation of loaded JSON
- **Error Handling**: 
  - FileNotFoundError: If file doesn't exist
  - JSONDecodeError: If file contains invalid JSON
  - ValidationError: If JSON doesn't match notebook schema
- **Side Effects**: File system read operation

#### save(self, path: Path | str) -> None
- **Purpose**: Save notebook to .ipynb file
- **Input**: File path as Path object or string
- **Output**: JSON file written to disk
- **Format**: Standard Jupyter notebook format
- **Error Handling**:
  - PermissionError: If insufficient write permissions
  - OSError: If path is invalid or disk full
- **Side Effects**: File system write operation, creates parent directories

#### __add__(self, other: "Notebook | NotebookCell | str") -> "Notebook"
- **Purpose**: Operator overloading for notebook composition
- **Input Types**:
  - NotebookCell: Adds single cell to notebook
  - Notebook: Concatenates all cells from other notebook
  - str: Creates new code cell from string and adds it
- **Returns**: New Notebook object (original unchanged)
- **Error Handling**: TypeError for unsupported types
- **Usage**: Enables `notebook + cell` and `notebook + "code"` syntax

#### to_markdown(self) -> str
- **Purpose**: Convert notebook to markdown representation
- **Returns**: Markdown string with code blocks and text
- **Format**: 
  - Code cells wrapped in ```python blocks
  - Markdown cells included as-is
  - Raw cells ignored
  - Empty cells skipped
- **Output Processing**: Strips whitespace, adds proper spacing
- **Usage**: Documentation generation, export functionality

### KernelExecution Class

```python
class KernelExecution(BaseModel):
    source: str
    outputs: list[AnyDict] = []
    error: str | None = None
    execution_count: int | None = None
```

**Purpose**: Represents the result of executing code in a kernel with complete execution context.

**Attributes Analysis**:

#### source: str
- **Type**: String containing the executed code
- **Purpose**: Preserves original source for debugging and notebook creation
- **Format**: Multi-line code preserved with original formatting
- **Required**: Yes (no default value)

#### outputs: list[AnyDict] = []
- **Type**: List of output dictionaries following Jupyter format
- **Default**: Empty list
- **Purpose**: Contains all execution outputs (results, streams, displays, errors)
- **Format**: Each output has "output_type" field and type-specific data
- **Population**: Filled during WebSocket message processing

#### error: str | None = None
- **Type**: Optional string containing error message
- **Default**: None (successful execution)
- **Purpose**: Human-readable error description for failed executions
- **Format**: ANSI codes stripped, traceback joined
- **Usage**: Error checking and user feedback

#### execution_count: int | None = None
- **Type**: Optional integer from Jupyter kernel
- **Default**: None (before execution)
- **Purpose**: Sequential execution number assigned by kernel
- **Behavior**: Increments only for successful executions

**Properties and Methods**:

#### success: bool (property)
- **Purpose**: Quick success/failure check
- **Implementation**: `return not self.error`
- **Usage**: Control flow for error handling
- **Performance**: O(1) operation

#### to_cell(self) -> NotebookCell
- **Purpose**: Convert execution result to notebook cell
- **Returns**: NotebookCell with source, outputs, and execution count
- **Format**: Source split into list of lines for .ipynb compatibility
- **Usage**: Building notebooks from execution results

#### to_notebook(self) -> Notebook
- **Purpose**: Convert execution result to single-cell notebook
- **Returns**: Notebook containing one cell with execution result
- **Implementation**: Uses to_cell() internally
- **Usage**: Quick notebook creation from execution

#### to_str(self) -> str
- **Purpose**: Extract human-readable text output
- **Returns**: Concatenated string from all text outputs plus any error
- **Processing**:
  - Stream outputs: Direct text extraction
  - Execute results: Extract "text/plain" data
  - Display data: Extract "text/plain" data
  - Errors: Appended at end
- **Usage**: Text-based result processing

## Exception Classes

### PythonKernelNotRunningError

```python
class PythonKernelNotRunningError(Exception):
    def __init__(self, message: str = "Kernel is not running") -> None:
        super().__init__(message)
```

**Purpose**: Raised when operations require a running kernel but none is available.

**Trigger Conditions**:
- Accessing `base_url` property when `_base_url` is None
- Accessing `ws_url` property when kernel not initialized
- Accessing `container` property when `_container` is None
- Calling `get_kernel_state()` when `_kernel_id` is None

**Usage Pattern**: Fail-fast validation for kernel-dependent operations
**Recovery**: Call `init()` or use async context manager

### PythonKernelStartError

```python
class PythonKernelStartError(Exception):
    def __init__(self, message: str = "Failed to start kernel") -> None:
        super().__init__(message)
```

**Purpose**: Raised when kernel initialization fails.

**Trigger Conditions**:
- Container fails to start or stay running
- Jupyter server fails to become ready within timeout
- Docker image pull failures
- Resource allocation failures

**Usage Pattern**: Indicates infrastructure problems requiring intervention
**Recovery**: Check Docker daemon, image availability, system resources

## PythonKernel Class

### Constructor and Initialization

```python
def __init__(
    self,
    image: str = "jupyter/datascience-notebook:latest",
    *,
    memory_limit: str = "4g",
    kernel_name: str = "python3",
    cleanup: bool = True,
    force_remove: bool = True,
) -> None:
```

**Parameter Analysis**:

#### image: str = "jupyter/datascience-notebook:latest"
- **Type**: String (Docker image reference)
- **Default**: Official Jupyter datascience notebook image
- **Purpose**: Specifies Docker image for container execution
- **Format**: Supports registry/image:tag format
- **Validation**: None at construction (validated during container creation)
- **Examples**: "python:3.11", "jupyter/minimal-notebook:latest"

#### memory_limit: str = "4g"
- **Type**: String with memory unit suffix
- **Default**: 4 gigabytes
- **Purpose**: Sets container memory limit for resource management
- **Format**: Number followed by unit (g/G, m/M, k/K) or raw bytes
- **Validation**: Parsed by `_parse_memory_limit()` method
- **Error Handling**: ValueError for invalid formats

#### kernel_name: str = "python3"
- **Type**: String identifying kernel type
- **Default**: "python3" (standard Python kernel)
- **Purpose**: Specifies which Jupyter kernel to start in container
- **Validation**: Must be available in the Docker image
- **Alternatives**: "python2", custom kernel names

#### cleanup: bool = True
- **Type**: Boolean flag
- **Default**: True (automatic cleanup enabled)
- **Purpose**: Controls whether resources are cleaned up on shutdown
- **Usage**: Set to False for debugging or manual resource management
- **Impact**: Affects container and temporary directory removal

#### force_remove: bool = True
- **Type**: Boolean flag
- **Default**: True (force container removal)
- **Purpose**: Controls Docker container removal behavior
- **Effect**: When True, uses docker force remove even if container is running
- **Safety**: Ensures cleanup even with hung containers

**Instance Variables**:

#### self._token: str = uuid.uuid4().hex
- **Type**: String (32-character hex UUID)
- **Purpose**: Authentication token for Jupyter server access
- **Security**: Unique per kernel instance, prevents unauthorized access
- **Usage**: Included in all HTTP requests and WebSocket connections
- **Lifetime**: Generated at construction, used until destruction

#### self._client: aiodocker.Docker | None = None
- **Type**: Optional Docker client instance
- **Purpose**: Manages Docker API communication
- **Lifecycle**: Created in init(), closed in shutdown()
- **Thread Safety**: Async-safe for single event loop

#### self._container: aiodocker.containers.DockerContainer | None = None
- **Type**: Optional Docker container object
- **Purpose**: Represents running Jupyter container
- **Lifecycle**: Created in _start_container(), removed in _delete_container()
- **State**: Only set when container is successfully running

#### self._temp_dir: Path | None = None
- **Type**: Optional Path to temporary directory
- **Purpose**: Host directory mounted into container for file operations
- **Lifecycle**: Created in init(), removed in shutdown()
- **Mount Point**: Bound to /home/jovyan/work in container

#### self._kernel_id: str | None = None
- **Type**: Optional kernel identifier from Jupyter
- **Purpose**: Unique identifier for active kernel session
- **Usage**: Required for kernel-specific API calls
- **Format**: UUID string assigned by Jupyter server

#### self._base_url: str | None = None
- **Type**: Optional HTTP URL string
- **Purpose**: Base URL for Jupyter server HTTP API
- **Format**: "http://localhost:PORT" where PORT is dynamically assigned
- **Usage**: All HTTP requests prefixed with this URL

### Property Methods

#### base_url: str (property)
```python
@property
def base_url(self) -> str:
    if not self._base_url:
        raise PythonKernelNotRunningError
    return self._base_url
```
- **Purpose**: Safe access to Jupyter server URL
- **Error Handling**: Raises exception if kernel not running
- **Usage**: HTTP API request construction
- **Thread Safety**: Read-only, thread-safe

#### ws_url: str (property)
```python
@property
def ws_url(self) -> str:
    if not self._base_url or not self._kernel_id:
        raise PythonKernelNotRunningError
    return f"{self._base_url.replace('http', 'ws')}/api/kernels/{self._kernel_id}/channels?token={self._token}"
```
- **Purpose**: WebSocket URL for kernel communication
- **Dependencies**: Requires both base_url and kernel_id
- **Format**: WebSocket protocol with kernel-specific endpoint
- **Authentication**: Includes token parameter for security
- **Error Handling**: Raises exception if dependencies not met

#### client: aiodocker.Docker (property)
```python
@property
def client(self) -> aiodocker.Docker:
    if not self._client:
        self._client = aiodocker.Docker()
    return self._client
```
- **Purpose**: Lazy initialization of Docker client
- **Pattern**: Singleton pattern within instance
- **Thread Safety**: Assumes single event loop usage
- **Resource Management**: Client requires explicit closure

#### container: aiodocker.containers.DockerContainer (property)
```python
@property
def container(self) -> aiodocker.containers.DockerContainer:
    if not self._container:
        raise PythonKernelNotRunningError
    return self._container
```
- **Purpose**: Safe access to running container
- **Error Handling**: Ensures container exists before access
- **Usage**: Container management operations
- **State Validation**: Confirms container object availability

### Memory Management

#### _parse_memory_limit(self, limit: str) -> int
```python
def _parse_memory_limit(self, limit: str) -> int:
    if limit.lower().endswith("g"):
        return int(float(limit[:-1]) * 1024 * 1024 * 1024)
    if limit.lower().endswith("m"):
        return int(float(limit[:-1]) * 1024 * 1024)
    if limit.lower().endswith("k"):
        return int(float(limit[:-1]) * 1024)
    return int(float(limit))
```

**Purpose**: Converts human-readable memory limits to bytes for Docker API.

**Input Validation**:
- Accepts floating-point numbers (e.g., "1.5g")
- Case-insensitive unit suffixes (g/G, m/M, k/K)
- Raw numbers interpreted as bytes

**Conversion Logic**:
- Gigabytes: multiply by 1024³ 
- Megabytes: multiply by 1024²
- Kilobytes: multiply by 1024¹
- No suffix: assume bytes

**Error Conditions**:
- ValueError: Invalid number format
- ValueError: Non-numeric input

**Return Value**: Integer bytes suitable for Docker HostConfig.Memory

### Container Management

#### _start_container(self) -> None
```python
@logger.catch(message="Failed to start container", reraise=True)
async def _start_container(self) -> None:
```

**Purpose**: Creates and starts Docker container with Jupyter server.

**Execution Flow**:

1. **Image Availability Check**:
   ```python
   try:
       await self.client.images.inspect(self.image)
   except aiodocker.exceptions.DockerError:
       await self.client.images.pull(self.image)
   ```
   - Checks if image exists locally
   - Pulls image if not found
   - Handles registry authentication automatically

2. **Memory Limit Processing**:
   ```python
   mem_bytes = self._parse_memory_limit(self.memory_limit)
   ```
   - Converts string format to bytes
   - Validates format and range

3. **Container Configuration**:
   ```python
   container_config: aiodocker.types.JSONObject = {
       "Image": self.image,
       "ExposedPorts": {"8888/tcp": {}},
       "HostConfig": {
           "Memory": mem_bytes,
           "MemorySwap": -1,  # Disable swap
           "PortBindings": {"8888/tcp": [{"HostPort": "0"}]},
           "Binds": [f"{self._temp_dir}:/home/jovyan/work"],
       },
       "Env": [
           f"JUPYTER_TOKEN={self._token}",
           "JUPYTER_ALLOW_INSECURE_WRITES=true",
       ],
       "Cmd": ["jupyter", "server", "--ip=0.0.0.0", "--no-browser"],
   }
   ```

**Configuration Analysis**:

- **Image**: Docker image to run
- **ExposedPorts**: Exposes port 8888 for Jupyter server
- **Memory**: Hard memory limit (no swap allowed)
- **MemorySwap**: -1 disables swap usage
- **PortBindings**: Dynamic port allocation (Docker chooses available port)
- **Binds**: Mount temp directory for file persistence
- **Environment Variables**:
  - `JUPYTER_TOKEN`: Authentication token
  - `JUPYTER_ALLOW_INSECURE_WRITES`: Permits file modifications
- **Command**: Starts Jupyter server with network access

4. **Container Creation and Startup**:
   ```python
   self._container = await self.client.containers.create(config=container_config)
   await self._container.start()
   ```
   - Creates container from configuration
   - Starts container (begins Jupyter server process)

5. **Port Discovery**:
   ```python
   container_info = await self._container.show()
   host_port = container_info["NetworkSettings"]["Ports"]["8888/tcp"][0]["HostPort"]
   self._base_url = f"http://localhost:{host_port}"
   ```
   - Retrieves dynamically assigned port
   - Constructs base URL for API access

6. **Service Readiness**:
   ```python
   await self._wait_for_jupyter()
   ```
   - Waits for Jupyter server to become ready
   - Validates container health

**Error Handling**:
- Docker errors logged and re-raised
- Automatic retry for transient failures
- Container cleanup on failure

**Side Effects**:
- Sets `_container`, `_base_url` instance variables
- Creates running Docker container
- Initiates Jupyter server process

#### _wait_for_jupyter(self) -> None
```python
@logger.catch(message="Jupyter server did not start", reraise=True)
@tenacity.retry(stop=tenacity.stop_after_delay(30), wait=tenacity.wait_fixed(1))
async def _wait_for_jupyter(self) -> None:
```

**Purpose**: Waits for Jupyter server to become ready with robust retry logic.

**Retry Configuration**:
- **Stop Condition**: 30-second maximum wait time
- **Wait Strategy**: Fixed 1-second intervals between attempts
- **Failure Handling**: Raises exception after timeout

**Health Checks**:

1. **Container Status Verification**:
   ```python
   container_info = await self.container.show()
   if container_info["State"]["Status"] != "running":
       raise PythonKernelStartError("Container did not stay running")
   ```
   - Ensures container remains in running state
   - Detects container crashes or exits

2. **HTTP API Availability**:
   ```python
   async with (
       aiohttp.ClientSession() as session,
       session.get(
           f"{self.base_url}/api/status",
           params={"token": self._token},
           timeout=aiohttp.ClientTimeout(total=1),
       ) as response,
   ):
       response.raise_for_status()
   ```
   - Tests Jupyter API responsiveness
   - Validates authentication token
   - Short timeout for quick failure detection

**Error Conditions**:
- Container stops running
- HTTP request timeout (1 second)
- HTTP error responses (4xx, 5xx)
- Network connectivity issues

**Success Criteria**:
- Container status "running"
- HTTP 200 response from /api/status
- Successful token authentication

#### _start_kernel(self) -> None
```python
@logger.catch(message="Failed to start kernel", reraise=True)
async def _start_kernel(self) -> None:
```

**Purpose**: Starts a Python kernel within the running Jupyter server.

**Execution Process**:

1. **Kernel Creation Request**:
   ```python
   async with (
       aiohttp.ClientSession() as session,
       session.post(
           f"{self._base_url}/api/kernels",
           params={"token": self._token},
           json={"name": self.kernel_name},
       ) as response,
   ):
       response.raise_for_status()
   ```
   - POST request to Jupyter kernels API
   - Specifies kernel type (e.g., "python3")
   - Includes authentication token

2. **Kernel ID Extraction**:
   ```python
   kernel_info = await response.json()
   self._kernel_id = kernel_info["id"]
   ```
   - Parses JSON response for kernel information
   - Extracts unique kernel identifier
   - Stores ID for future kernel operations

**API Response Format**:
```json
{
    "id": "kernel-uuid-string",
    "name": "python3",
    "last_activity": "2024-01-01T12:00:00.000000Z",
    "execution_state": "starting",
    "connections": 0
}
```

**Error Handling**:
- HTTP errors from Jupyter API
- JSON parsing failures
- Missing kernel ID in response

**Side Effects**:
- Sets `_kernel_id` instance variable
- Creates active kernel session in Jupyter
- Enables code execution capabilities

**Logging**: Debug message with kernel name and ID

#### _delete_kernel(self) -> None
```python
@logger.catch(message="Failed to delete kernel")
async def _delete_kernel(self) -> None:
```

**Purpose**: Gracefully shuts down and removes the active kernel.

**Execution Logic**:

1. **Kernel Existence Check**:
   ```python
   if not self._kernel_id:
       return
   ```
   - Early return if no kernel exists
   - Prevents unnecessary API calls

2. **Kernel Deletion Request**:
   ```python
   async with (
       aiohttp.ClientSession() as session,
       session.delete(
           f"{self._base_url}/api/kernels/{self._kernel_id}",
           params={"token": self._token},
       ) as response,
   ):
       response.raise_for_status()
   ```
   - DELETE request to kernel-specific endpoint
   - Includes kernel ID in URL path
   - Authenticated with token parameter

3. **State Cleanup**:
   ```python
   self._kernel_id = None
   ```
   - Clears kernel ID to prevent reuse
   - Marks kernel as no longer available

**Error Handling**:
- Logger.catch prevents exceptions from propagating
- Continues cleanup even if deletion fails
- Logs errors for debugging

**API Effects**:
- Terminates kernel execution
- Closes all kernel connections
- Frees kernel resources in Jupyter

#### _delete_container(self) -> None
```python
async def _delete_container(self) -> None:
```

**Purpose**: Stops and removes Docker container with comprehensive error handling.

**Execution Sequence**:

1. **Container Existence Check**:
   ```python
   if not self._container:
       return
   ```

2. **Container Information Retrieval**:
   ```python
   container_info = await self._container.show()
   container_id = container_info["Id"]
   logger.debug(f"Stopping container {container_id[:12]}...")
   ```
   - Gets current container state
   - Extracts container ID for logging
   - Uses short ID format for readability

3. **Graceful Container Stop**:
   ```python
   try:
       await self._container.stop(timeout=5)
   except aiodocker.exceptions.DockerError as e:
       logger.debug(f"Container stop error (continuing): {e!s}")
   ```
   - Attempts graceful shutdown with 5-second timeout
   - Logs but continues on stop failures
   - Sends SIGTERM then SIGKILL if timeout exceeded

4. **Container Removal**:
   ```python
   try:
       await self._container.delete(
           force=self.force_remove,
           v=True,
       )  # v=True to remove volumes
       logger.debug(f"Removed container {container_id[:12]}")
   except aiodocker.exceptions.DockerError as e:
       logger.error(f"Failed to remove container: {e!s}")
   ```
   - Removes container and associated volumes
   - Force removal if configured
   - Logs success/failure

5. **State Cleanup**:
   ```python
   self._container = None
   ```

**Error Resilience**:
- Multiple try-catch blocks for different failure points
- Continues cleanup even with partial failures
- Comprehensive exception handling for Docker and OS errors

### Lifecycle Management

#### init(self) -> "PythonKernel"
```python
async def init(self) -> "PythonKernel":
    """Initialize the container and kernel server."""
    await self.shutdown()

    self._temp_dir = Path(tempfile.mkdtemp())
    self._client = aiodocker.Docker()

    await self._start_container()
    await self._start_kernel()
    return self
```

**Purpose**: Complete initialization of kernel execution environment.

**Initialization Sequence**:

1. **Clean Slate Setup**:
   - Calls shutdown() to ensure clean state
   - Removes any existing resources
   - Prevents resource conflicts

2. **Resource Allocation**:
   - Creates temporary directory for file operations
   - Initializes Docker client
   - Prepares infrastructure components

3. **Service Startup**:
   - Starts Docker container with Jupyter
   - Initializes Python kernel within container
   - Establishes communication channels

**Return Value**: Self-reference for method chaining

**Error Propagation**: All setup errors bubble up to caller

**State Guarantee**: Either fully initialized or clean shutdown

#### shutdown(self) -> None
```python
async def shutdown(self) -> None:
    """Clean up resources and reset state."""
```

**Purpose**: Comprehensive cleanup of all allocated resources.

**Cleanup Sequence**:

1. **Early Exit Check**:
   ```python
   if self._client is None:
       return
   ```
   - Skips cleanup if never initialized
   - Prevents redundant operations

2. **Kernel Shutdown**:
   ```python
   try:
       await self._delete_kernel()
   except (aiodocker.exceptions.DockerError, OSError, ConnectionError) as e:
       logger.error(f"Error during kernel shutdown: {e!s}")
   ```
   - Gracefully stops active kernel
   - Logs but continues on errors

3. **Container Cleanup**:
   ```python
   try:
       await self._delete_container()
   except (aiodocker.exceptions.DockerError, OSError) as e:
       logger.error(f"Error during container deletion: {e!s}")
   ```
   - Stops and removes Docker container
   - Handles container deletion failures

4. **Docker Client Closure**:
   ```python
   if self._client:
       try:
           await self._client.close()
       except (aiodocker.exceptions.DockerError, OSError, ConnectionError) as e:
           logger.error(f"Error closing Docker client: {e!s}")
       self._client = None
   ```
   - Closes Docker API connection
   - Frees client resources

5. **Temporary Directory Cleanup**:
   ```python
   if self._temp_dir:
       shutil.rmtree(self._temp_dir, ignore_errors=True)
       self._temp_dir = None
   ```
   - Removes temporary files and directories
   - Uses ignore_errors for robustness

**Error Handling Strategy**:
- Individual try-catch for each cleanup step
- Logs errors but continues cleanup
- Ensures all resources are freed even with failures

**State Reset**: All instance variables set to None/cleaned

#### Async Context Manager Support
```python
async def __aenter__(self) -> "PythonKernel":
    """Start a Jupyter server and kernel."""
    return await self.init()

async def __aexit__(
    self,
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
    exc_tb: types.TracebackType | None,
) -> None:
    await self.shutdown()
```

**Purpose**: Enables `async with` syntax for automatic resource management.

**Usage Pattern**:
```python
async with PythonKernel() as kernel:
    result = await kernel.execute("print('Hello World')")
    # Automatic cleanup on exit
```

**Benefits**:
- Guaranteed cleanup even with exceptions
- Cleaner code structure
- Exception propagation after cleanup

### Code Execution

#### execute() Method - Core Execution Engine
```python
async def execute(
    self,
    source: str | list[str],
    *,
    format: t.Literal["str", "cell", "notebook"] | None = None,
    timeout: int = 30,
    log_output: bool = False,
) -> KernelExecution | Notebook | NotebookCell | str:
```

**Purpose**: Executes Python code in kernel with comprehensive output handling.

**Parameter Analysis**:

#### source: str | list[str]
- **Type**: Python code as string or list of lines
- **Processing**: List format joined to single string
- **Validation**: No syntax validation (handled by kernel)
- **Examples**: `"print('hello')"`, `["x = 1", "print(x)"]`

#### format: Optional output format specifier
- **None**: Returns KernelExecution object (default)
- **"str"**: Returns concatenated text output
- **"cell"**: Returns NotebookCell object
- **"notebook"**: Returns single-cell Notebook object
- **Usage**: Determines return type for different use cases

#### timeout: int = 30
- **Type**: Integer seconds
- **Default**: 30 seconds
- **Purpose**: Maximum execution time before interruption
- **Behavior**: Sends interrupt signal on timeout
- **Range**: Positive integers, practical limit ~600 seconds

#### log_output: bool = False
- **Type**: Boolean flag
- **Default**: False (no logging)
- **Purpose**: Controls whether execution output is logged
- **Effect**: Logs text/plain outputs at INFO level

**Execution Flow**:

1. **Source Preparation**:
   ```python
   source = "".join(source) if isinstance(source, list) else source
   execute_request = self._create_execute_request(source)
   msg_id = execute_request["header"]["msg_id"]
   ```
   - Normalizes source to string format
   - Creates Jupyter protocol message
   - Generates unique message ID for tracking

2. **Output Collection Initialization**:
   ```python
   outputs: list[AnyDict] = []
   error: str | None = None
   execution_count: int | None = None
   start_time = asyncio.get_event_loop().time()
   ```
   - Initializes result containers
   - Records start time for timeout calculation

3. **WebSocket Communication**:
   ```python
   async with aiohttp.ClientSession() as session, session.ws_connect(self.ws_url) as ws:
       await ws.send_json(execute_request)
   ```
   - Establishes WebSocket connection to kernel
   - Sends execution request message

4. **Message Processing Loop**:
   ```python
   while (start_time + timeout) > asyncio.get_event_loop().time():
       try:
           msg = await asyncio.wait_for(ws.receive_json(), timeout=1.0)
       except asyncio.TimeoutError:
           continue
   ```
   - Processes messages until timeout or completion
   - 1-second receive timeout for responsiveness
   - Continues on receive timeouts

5. **Message Filtering**:
   ```python
   if msg.get("parent_header", {}).get("msg_id") != msg_id:
       continue
   ```
   - Ensures message belongs to current execution
   - Filters out unrelated kernel messages

6. **Message Type Handling**:
   - **execute_result**: Final execution result
   - **display_data**: Rich display outputs (plots, HTML)
   - **stream**: stdout/stderr text streams
   - **error**: Exception and traceback information
   - **execute_reply**: Execution completion signal

7. **Result Assembly**:
   ```python
   execution = KernelExecution(
       source=source,
       outputs=outputs,
       error=error,
       execution_count=execution_count,
   )
   ```
   - Creates result object with all collected data
   - Preserves original source code

8. **Format Conversion**:
   ```python
   match format:
       case "str": return execution.to_str()
       case "cell": return execution.to_cell()
       case "notebook": return execution.to_notebook()
       case _: return execution
   ```
   - Converts to requested format
   - Default returns raw execution object

**Timeout Handling**:
```python
else:  # While loop timeout
    await self.interrupt()
    raise asyncio.TimeoutError("Execution timed out")
```
- Interrupts kernel on timeout
- Raises exception with clear message

#### _create_execute_request(self, source: str) -> dict[str, t.Any]
```python
def _create_execute_request(self, source: str) -> dict[str, t.Any]:
    msg_id = str(uuid.uuid4())
    return {
        "header": {
            "msg_id": msg_id,
            "username": "user",
            "session": str(uuid.uuid4()),
            "msg_type": "execute_request",
            "version": "5.0",
        },
        "parent_header": {},
        "metadata": {},
        "content": {
            "code": source,
            "silent": False,
            "store_history": True,
            "user_expressions": {},
            "allow_stdin": False,
        },
    }
```

**Purpose**: Creates Jupyter protocol message for code execution.

**Message Structure Analysis**:

#### Header Section
- **msg_id**: Unique identifier for message tracking
- **username**: Static "user" identifier
- **session**: Unique session ID (new per request)
- **msg_type**: "execute_request" message type
- **version**: Jupyter protocol version "5.0"

#### Content Section
- **code**: Source code to execute
- **silent**: False (show outputs)
- **store_history**: True (save in kernel history)
- **user_expressions**: Empty (no custom expressions)
- **allow_stdin**: False (no interactive input)

#### Message Handlers

#### _handle_execute_result()
```python
def _handle_execute_result(
    self,
    content: dict[str, t.Any],
    *,
    log_output: bool,
) -> dict[str, t.Any]:
```

**Purpose**: Processes final execution result from kernel.

**Content Processing**:
- Extracts result data in multiple formats (text, HTML, images)
- Preserves metadata (display hints, styling)
- Records execution count from kernel

**Output Format**:
```python
{
    "output_type": "execute_result",
    "metadata": {...},
    "data": {
        "text/plain": "42",
        "text/html": "<div>...</div>",
        "image/png": "base64-data..."
    },
    "execution_count": 1
}
```

**Logging**: Logs text/plain data if log_output enabled

#### _handle_display_data()
```python
def _handle_display_data(
    self,
    content: dict[str, t.Any],
    *,
    log_output: bool,
) -> dict[str, t.Any]:
```

**Purpose**: Processes rich display outputs (plots, widgets, HTML).

**Similar to execute_result but**:
- No execution_count field
- Used for side-effect displays (plt.show(), display())
- Multiple displays possible per execution

#### _handle_stream()
```python
def _handle_stream(
    self,
    content: dict[str, t.Any],
    outputs: list[t.Any],
    *,
    log_output: bool,
) -> None:
```

**Purpose**: Processes stdout/stderr stream outputs with aggregation.

**Stream Processing**:

1. **ANSI Code Removal**:
   ```python
   clean_text = strip_ansi_codes(content.get("text", ""))
   ```
   - Removes terminal escape sequences
   - Ensures clean text output

2. **Stream Identification**:
   ```python
   stream_name = content.get("name", "stdout")
   ```
   - Identifies output stream (stdout/stderr)
   - Defaults to stdout for unknown streams

3. **Stream Aggregation**:
   ```python
   for i, output in enumerate(outputs):
       if output["output_type"] == "stream" and output["name"] == stream_name:
           outputs[i]["text"] += clean_text
           break
   else:
       # Create new stream output
   ```
   - Appends to existing stream of same type
   - Creates new stream entry if none exists
   - Maintains separate stdout/stderr streams

4. **Stream Validation**:
   ```python
   if stream_name not in ("stdout", "stderr"):
       stream_name = "stdout"
   ```
   - Ensures only valid stream names
   - Defaults unknown streams to stdout

#### _handle_error()
```python
def _handle_error(self, content: dict[str, t.Any]) -> tuple[dict[str, t.Any], str]:
```

**Purpose**: Processes execution errors and exceptions.

**Error Processing**:

1. **Traceback Extraction**:
   ```python
   traceback = content.get("traceback", [])
   ```
   - Gets formatted traceback lines
   - Preserves stack trace information

2. **Error Output Structure**:
   ```python
   error_output = {
       "output_type": "error",
       "ename": content.get("ename", ""),      # Exception type
       "evalue": content.get("evalue", ""),    # Exception message
       "traceback": traceback,                 # Full traceback
   }
   ```

3. **Error Message Cleanup**:
   ```python
   error = strip_ansi_codes("\n".join(traceback))
   ```
   - Joins traceback lines
   - Removes ANSI formatting codes
   - Creates human-readable error string

**Return Values**: 
- Error output dictionary for notebook storage
- Clean error string for quick access

### High-Level Execution Methods

#### execute_cell(self, cell: NotebookCell) -> NotebookCell
```python
async def execute_cell(self, cell: NotebookCell) -> NotebookCell:
    cell = cell.model_copy(deep=True)
    
    if cell.cell_type != "code":
        return cell
    
    result = await self.execute(cell.source)
    
    cell.outputs = result.outputs
    cell.execution_count = result.execution_count or cell.execution_count
    
    return cell
```

**Purpose**: Executes a single notebook cell with result integration.

**Execution Logic**:
1. **Deep Copy**: Creates independent cell copy to avoid mutation
2. **Type Check**: Only executes code cells, returns others unchanged
3. **Execution**: Runs cell source through execute() method
4. **Result Integration**: Updates cell with outputs and execution count
5. **Count Preservation**: Keeps existing count if execution doesn't provide one

**Use Cases**:
- Interactive notebook execution
- Single cell testing
- Incremental notebook building

#### execute_notebook()
```python
async def execute_notebook(
    self,
    notebook: Notebook,
    *,
    stop_on_error: bool = True,
    log_output: bool = True,
) -> Notebook:
```

**Purpose**: Executes all code cells in a notebook sequentially.

**Parameter Analysis**:

#### stop_on_error: bool = True
- **Default**: True (stop on first error)
- **False**: Continue executing remaining cells after errors
- **Usage**: False for comprehensive testing, True for normal execution

#### log_output: bool = True
- **Default**: True (log execution outputs)
- **Purpose**: Provides execution feedback for long-running notebooks

**Execution Process**:

1. **Notebook Preparation**:
   ```python
   notebook = notebook.model_copy(deep=True)
   
   for cell in notebook.cells:
       if cell.cell_type == "code":
           cell.outputs = []
           cell.execution_count = None
   ```
   - Creates independent notebook copy
   - Clears all existing outputs and execution counts
   - Resets to clean execution state

2. **Sequential Execution**:
   ```python
   logger.info(f"Executing notebook with {len(notebook.cells)} cells")
   for i, cell in enumerate(notebook.cells):
       if cell.cell_type != "code":
           continue
       
       result = await self.execute(cell.source, log_output=log_output)
   ```
   - Logs execution start with cell count
   - Skips non-code cells
   - Executes each code cell in order

3. **Error Handling**:
   ```python
   if not result.success and stop_on_error:
       logger.error(f"Error in cell {i}: {result.error}")
       break
   ```
   - Checks execution success
   - Logs error with cell number
   - Stops execution if stop_on_error enabled

4. **Result Integration**:
   ```python
   cell.outputs = result.outputs
   cell.execution_count = result.execution_count or cell.execution_count
   ```
   - Updates cell with execution results
   - Preserves execution count progression

**State Management**: Each cell execution builds on previous cell state
**Error Recovery**: Partial results available even with errors
**Logging**: Progress feedback for long notebooks

### Kernel State Management

#### get_kernel_state(self) -> KernelState
```python
async def get_kernel_state(self) -> KernelState:
    if not self._kernel_id:
        raise PythonKernelNotRunningError
    
    async with (
        aiohttp.ClientSession() as session,
        session.get(
            f"{self._base_url}/api/kernels/{self._kernel_id}",
            params={"token": self._token},
        ) as response,
    ):
        response.raise_for_status()
        kernel_info = await response.json()
    
    return t.cast("KernelState", kernel_info["execution_state"])
```

**Purpose**: Queries current kernel execution state from Jupyter.

**API Integration**:
- GET request to kernel-specific endpoint
- Authenticated with token parameter
- Returns kernel information including execution state

**State Values**:
- `"starting"`: Kernel initializing
- `"idle"`: Ready for execution
- `"busy"`: Currently executing code

**Error Handling**:
- Validates kernel existence before request
- HTTP error propagation for API failures
- Type casting for return value safety

#### busy(self) -> bool
```python
async def busy(self) -> bool:
    return await self.get_kernel_state() == "busy"
```

**Purpose**: Simple boolean check for kernel busy state.

**Usage**: 
- Wait loops for kernel availability
- Execution scheduling decisions
- UI state updates

#### interrupt(self) -> None
```python
async def interrupt(self) -> None:
    if not self._kernel_id:
        return
    
    async with (
        aiohttp.ClientSession() as session,
        session.post(
            f"{self._base_url}/api/kernels/{self._kernel_id}/interrupt",
            params={"token": self._token},
        ) as response,
    ):
        response.raise_for_status()
    
    logger.debug(f"Kernel {self._kernel_id} interrupted")
```

**Purpose**: Sends interrupt signal to stop kernel execution.

**Mechanism**:
- POST request to interrupt endpoint
- Sends SIGINT to kernel process
- Graceful execution termination

**Use Cases**:
- Timeout handling in execute() method
- User-initiated execution cancellation
- Infinite loop prevention

#### restart(self) -> None
```python
async def restart(self) -> None:
    if not self._kernel_id:
        return
    
    async with (
        aiohttp.ClientSession() as session,
        session.post(
            f"{self._base_url}/api/kernels/{self._kernel_id}/restart",
            params={"token": self._token},
        ) as response,
    ):
        response.raise_for_status()
    
    logger.debug(f"Kernel {self._kernel_id} restarted")
```

**Purpose**: Restarts kernel, clearing all execution state.

**Effects**:
- Clears all variables and imports
- Resets execution count to 1
- Maintains kernel ID and connections
- Fresh Python interpreter state

**Use Cases**:
- Memory cleanup after heavy operations
- State reset between test runs
- Recovery from corrupted kernel state

### Utility Methods

#### get_container_logs(self) -> str
```python
async def get_container_logs(self) -> str:
    if not self._container:
        return ""
    
    logs = await self._container.log(stdout=True, stderr=True)
    return "\n".join(logs)
```

**Purpose**: Retrieves Docker container logs for debugging.

**Log Content**:
- Jupyter server startup messages
- Kernel initialization logs
- Container runtime errors
- System-level diagnostics

**Format**: Combined stdout/stderr streams joined with newlines

**Use Cases**:
- Debugging startup failures
- Monitoring container health
- Troubleshooting execution issues

## Utility Functions

### cleanup_routine()
```python
async def cleanup_routine() -> None:
    try:
        client = aiodocker.Docker()
        containers = await client.containers.list(all=True)
        for container in containers:
            container_info = await container.show()
            if container_info.get("State", {}).get("Status") == "exited":
                try:
                    await container.delete(force=True)
                    logger.debug(f"Cleaned up exited container {container_info['Id'][:12]}")
                except (aiodocker.exceptions.DockerError, OSError) as e:
                    logger.debug(f"Could not clean up container: {e}")
        await client.close()
        logger.debug("Cleanup routine completed")
    except (aiodocker.exceptions.DockerError, OSError, ConnectionError) as e:
        logger.warning(f"Cleanup routine failed: {e}")
```

**Purpose**: Global cleanup function for orphaned Docker containers.

**Cleanup Logic**:
1. **Container Discovery**: Lists all Docker containers (running and stopped)
2. **Status Filtering**: Identifies containers in "exited" state
3. **Force Removal**: Deletes exited containers with force flag
4. **Error Resilience**: Continues cleanup despite individual failures
5. **Resource Cleanup**: Closes Docker client connection

**Use Cases**:
- Application shutdown cleanup
- Periodic maintenance routines
- Development environment reset
- CI/CD pipeline cleanup

**Error Handling**:
- Individual container failures logged but don't stop cleanup
- Top-level failures logged as warnings
- Ensures Docker client closure

## Control Flow Analysis

### Initialization Sequence
1. `PythonKernel.__init__()` - Object creation with configuration
2. `init()` or `__aenter__()` - Resource allocation and startup
3. `_start_container()` - Docker container creation and startup
4. `_wait_for_jupyter()` - Service readiness verification  
5. `_start_kernel()` - Python kernel initialization

### Execution Sequence
1. `execute()` - Main execution entry point
2. `_create_execute_request()` - Jupyter message creation
3. WebSocket connection establishment
4. Message sending and response processing
5. Output aggregation and error handling
6. Result formatting and return

### Shutdown Sequence
1. `shutdown()` or `__aexit__()` - Cleanup initiation
2. `_delete_kernel()` - Kernel termination
3. `_delete_container()` - Container cleanup
4. Docker client closure
5. Temporary directory removal

### Error Recovery Flows
- **Container startup failure**: Full cleanup and re-raise
- **Kernel startup failure**: Container cleanup and re-raise  
- **Execution timeout**: Kernel interrupt and timeout exception
- **WebSocket failure**: Connection cleanup and re-raise
- **Shutdown errors**: Log errors but continue cleanup

## Resource Management

### Memory Management
- **Container Memory Limits**: Configurable per instance (default 4GB)
- **Memory Swap**: Disabled to prevent performance degradation
- **Memory Monitoring**: No automatic monitoring (relies on Docker limits)
- **Memory Cleanup**: Automatic cleanup on container removal

### File System Management
- **Temporary Directories**: Created per kernel instance
- **Container Mounts**: Host temp directory mounted to `/home/jovyan/work`
- **File Persistence**: Files persist until kernel shutdown
- **Cleanup**: Recursive removal with error ignoring

### Network Resource Management
- **Port Allocation**: Dynamic port assignment by Docker
- **WebSocket Connections**: Automatic cleanup on context exit
- **HTTP Sessions**: Scoped to individual requests
- **Connection Pooling**: Default aiohttp connection pooling

### Docker Resource Management
- **Image Management**: Automatic pull if not available locally
- **Container Lifecycle**: Full lifecycle management with cleanup
- **Volume Management**: Automatic volume removal on container deletion
- **Registry Authentication**: Handled by Docker daemon

## Error Handling

### Exception Hierarchy
- **PythonKernelNotRunningError**: State validation failures
- **PythonKernelStartError**: Initialization failures
- **asyncio.TimeoutError**: Execution timeout
- **aiodocker.exceptions.DockerError**: Docker API errors
- **aiohttp.ClientError**: HTTP communication errors

### Error Recovery Strategies
- **Retry Logic**: Tenacity-based retry for service startup
- **Graceful Degradation**: Continue cleanup despite individual failures
- **Resource Cleanup**: Guaranteed cleanup even with errors
- **Error Propagation**: Meaningful error messages with context

### Logging Strategy
- **Debug Level**: Operational details (container IDs, kernel IDs)
- **Info Level**: Execution progress and major operations
- **Error Level**: Recoverable errors and cleanup failures
- **Exception Catching**: Automatic exception logging with loguru

## Security Considerations

### Authentication
- **Token-Based**: UUID tokens for Jupyter server access
- **Token Scope**: Per-kernel instance, not shared
- **Token Transmission**: URL parameters and HTTP headers
- **Token Lifecycle**: Generated at creation, valid until shutdown

### Container Security
- **User Isolation**: Runs as jovyan user in container
- **File System**: Limited to mounted temporary directory
- **Network Isolation**: Only exposes necessary ports
- **Resource Limits**: Memory and CPU constraints

### Code Execution Security
- **Sandboxing**: Limited to container environment
- **Input Validation**: No input sanitization (trusts caller)
- **Output Sanitization**: ANSI code removal only
- **Privilege Escalation**: Prevented by container user restrictions

### Network Security
- **Local Binding**: Jupyter server bound to localhost only
- **Token Authentication**: Required for all API access
- **WebSocket Security**: Token-based authentication
- **TLS**: Not implemented (local communication only)

### Data Security
- **Temporary Data**: Cleaned up on shutdown
- **Log Sanitization**: No sensitive data filtering
- **Memory Dumps**: Not prevented or encrypted
- **Persistence**: No permanent data storage

---

This comprehensive specification covers every aspect of the AIRTBench kernel.py implementation, providing detailed analysis of functionality, data flow, error handling, and resource management. The document serves as both technical documentation and implementation reference for understanding the complete Python kernel execution system.