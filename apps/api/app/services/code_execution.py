"""Code execution service — sandboxed code execution for coding interviews."""

import logging
import os
import tempfile
import subprocess
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Security limits
MAX_CODE_LENGTH = 10000
MAX_EXECUTION_TIME = 10  # seconds
MAX_OUTPUT_LENGTH = 5000


class CodeExecutionError(Exception):
    """Raised when code execution fails."""
    pass


class CodeExecutionTimeout(CodeExecutionError):
    """Raised when code execution times out."""
    pass


class CodeExecutionSecurityError(CodeExecutionError):
    """Raised when code violates security policies."""
    pass


def validate_code(code: str) -> None:
    """Validate code for security concerns."""
    if len(code) > MAX_CODE_LENGTH:
        raise CodeExecutionSecurityError(
            f"Code exceeds maximum length of {MAX_CODE_LENGTH} characters"
        )
    
    # Check for dangerous imports/patterns
    dangerous_patterns = [
        "import os",
        "import subprocess",
        "import sys",
        "import shutil",
        "__import__",
        "eval(",
        "exec(",
        "compile(",
        "open(",
        "os.system",
        "subprocess.",
        "shutil.",
    ]
    
    code_lower = code.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in code_lower:
            raise CodeExecutionSecurityError(
                f"Code contains restricted pattern: {pattern}"
            )


def execute_python_code(
    code: str,
    test_cases: Optional[list] = None,
    timeout: int = MAX_EXECUTION_TIME,
) -> Dict[str, Any]:
    """Execute Python code in a sandboxed environment.
    
    Args:
        code: The Python code to execute
        test_cases: Optional list of test cases with input/expected
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary with execution results
    """
    validate_code(code)
    
    timeout = min(timeout, MAX_EXECUTION_TIME)
    
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        # Add test case execution wrapper if test cases provided
        if test_cases:
            wrapped_code = _wrap_with_tests(code, test_cases)
        else:
            wrapped_code = code
        
        f.write(wrapped_code)
        temp_path = f.name
    
    try:
        # Execute the code
        result = subprocess.run(
            ['python', temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir(),
        )
        
        stdout = result.stdout[:MAX_OUTPUT_LENGTH] if result.stdout else ""
        stderr = result.stderr[:MAX_OUTPUT_LENGTH] if result.stderr else ""
        
        if result.returncode != 0:
            return {
                "success": False,
                "output": stdout,
                "error": stderr,
                "execution_time": 0,
                "test_results": [],
            }
        
        # Parse test results if available
        test_results = []
        if test_cases:
            test_results = _parse_test_results(stdout)
        
        return {
            "success": True,
            "output": stdout,
            "error": stderr if stderr else None,
            "execution_time": 0,
            "test_results": test_results,
        }
        
    except subprocess.TimeoutExpired:
        raise CodeExecutionTimeout(
            f"Code execution timed out after {timeout} seconds"
        )
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        raise CodeExecutionError(f"Execution failed: {str(e)}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def _wrap_with_tests(code: str, test_cases: list) -> str:
    """Wrap code with test case execution."""
    wrapper = '''
import sys
import io
from contextlib import redirect_stdout

# Capture original print
original_print = print

def capture_print(*args, **kwargs):
    kwargs['file'] = sys.stderr
    original_print(*args, **kwargs)

# User code
'''
    wrapper += code + '\n\n'
    wrapper += '''
# Test execution
test_results = []
'''
    
    for i, test in enumerate(test_cases):
        wrapper += f'''
try:
    with redirect_stdout(io.StringIO()) as output:
        result = {test.get('call', 'None')}
    expected = {repr(test.get('expected', None))}
    passed = str(result).strip() == str(expected).strip()
    test_results.append({{
        "test_case": {i + 1},
        "passed": passed,
        "expected": expected,
        "actual": str(result).strip(),
    }})
except Exception as e:
    test_results.append({{
        "test_case": {i + 1},
        "passed": False,
        "error": str(e),
    }})
'''
    
    wrapper += '''
# Print test results
import json
print(json.dumps(test_results))
'''
    
    return wrapper


def _parse_test_results(output: str) -> list:
    """Parse test results from output."""
    import json
    try:
        # Find the last line that looks like JSON
        lines = output.strip().split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                return json.loads(line)
    except (json.JSONDecodeError, IndexError):
        pass
    return []


def run_code_with_timeout(code: str, timeout: int = MAX_EXECUTION_TIME) -> Dict[str, Any]:
    """Run code with timeout and return results."""
    try:
        return execute_python_code(code, timeout=timeout)
    except CodeExecutionTimeout as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "execution_time": timeout,
            "test_results": [],
        }
    except CodeExecutionError as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "execution_time": 0,
            "test_results": [],
        }
