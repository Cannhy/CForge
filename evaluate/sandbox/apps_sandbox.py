import sys
import os
import json
import argparse
from io import StringIO  # For original Python part
# from unittest.mock import patch, mock_open # Needed for full original Python part
import signal  # For original Python part
import faulthandler  # For original Python part
from datetime import datetime  # For debug prints
from typing import List, Tuple, Dict, Any  # For type hints
from entity import apps

# For C execution
import subprocess
import tempfile
import shutil
import numpy as np  # For np.allclose in C output comparison, ensure it's installed
import sandbox


# --- Assume these are defined from your original code ---
# You'll need to ensure these are available in your full script.

class Capturing(list):  # Your original Capturing class
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        self._stringio.close = lambda x: 1  # type: ignore
        return self

    def __exit__(self, *args: Any) -> None:
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


# Dummy CODE_TYPE if not fully defined elsewhere for the example
class CODE_TYPE:
    standard_input = 1
    call_based = 2


# Dummy reliability_guard (original was Python specific)
def reliability_guard() -> None:
    # For C, this might involve setting resource limits if possible via `prlimit` (Linux)
    # or ensuring the execution environment is constrained.
    # For now, subprocess timeout is the main guard for C.
    # For Python, it might have involved other checks.
    pass


# Dummy RuntimeModule for Python part (if it was a custom class)
class RuntimeModule:
    @staticmethod
    def from_string(module_name: str, source_name: str, source_code: str) -> Any:
        # This is a placeholder. Your actual RuntimeModule would compile/exec Python code.
        # For this example to run without the full original context, it's simplified.
        print(f"Warning: RuntimeModule.from_string called with: {module_name}, {source_name}")

        # In a real scenario, this would return a module object or a class instance.
        # We'll return a dummy object that might have a 'Solution' attribute or be directly callable.
        class MockSolution:
            pass

        mock_module = MockSolution()
        # Attempt to exec the source_code into the mock_module's namespace
        # This is a very basic way to simulate it for the example
        try:
            namespace = {}
            exec(source_code, namespace)
            for name, value in namespace.items():
                setattr(mock_module, name, value)
            if "Solution" in namespace:  # type: ignore
                setattr(mock_module, "Solution", namespace["Solution"])  # type: ignore
        except Exception as e:
            print(f"Error in dummy RuntimeModule exec: {e}")
        return mock_module


# Your original custom_compare_ and stripped_string_compare functions
def custom_compare_(output: List[str], ground_truth: str) -> bool:
    if isinstance(output, list):
        output_1 = "\n".join(output)
        if stripped_string_compare(output_1, ground_truth):
            return True
    if isinstance(output, list):
        output_2 = [o.lstrip().rstrip() for o in output]
        output_2 = "\n".join(output_2)
        if stripped_string_compare(output_2, ground_truth):
            return True
    return False


def stripped_string_compare(s1: str, s2: str) -> bool:
    s1 = s1.lstrip().rstrip()
    s2 = s2.lstrip().rstrip()
    return s1 == s2


# Dummy call_method for Python standard_input (original used unittest.mock)
def call_method(method: Any, inputs: str) -> Any:
    # This is a highly simplified placeholder.
    # The original uses unittest.mock to patch sys.stdin, builtins.input etc.
    # For a standalone example, we can't easily replicate that without the mocks.
    print(f"Warning: call_method is a simplified dummy. Input: '{inputs[:50]}...'")
    # Try to simulate by providing input via a temporary patch if possible,
    # or just call the method and hope it handles input in a testable way.
    original_stdin = sys.stdin
    sys.stdin = StringIO(inputs)
    try:
        result = method()
    finally:
        sys.stdin = original_stdin
    return result


# Global timeout variable (as implied by original Python code)
timeout: int = 5  # Default timeout in seconds


# --- Helper for processing expected output for C comparison ---
def process_expected_output_for_comparison(expected_output_raw: Any, target_format: str = "list_of_strings") -> Any:
    if target_format == "list_of_strings":
        if isinstance(expected_output_raw, list):
            return [str(e).strip() for e in expected_output_raw if
                    str(e).strip() or str(e) == ""]  # Keep intentionally empty strings
        elif isinstance(expected_output_raw, str):
            return [line.strip() for line in expected_output_raw.splitlines() if line.strip() or line == ""]
        else:
            s = str(expected_output_raw)
            return [line.strip() for line in s.splitlines() if line.strip() or line == ""]
    elif target_format == "string_for_custom_compare":
        if isinstance(expected_output_raw, list):
            return "\n".join(map(str, expected_output_raw))
        else:
            return str(expected_output_raw)
    return []


def run_c_test(problem_json: Dict[str, Any], c_code: str, debug: bool, timeout_seconds: int) -> List[Any]:
    # The timeout_seconds parameter from run_c_test is not directly used by
    # run_code_snip_provided_by_user, as it has hardcoded timeouts.
    # This could be a point of future enhancement for run_code_snip_provided_by_user.

    if problem_json.get("signature") is not None:
        # "signature" mode: runs c_code + problem_json["test"] via the provided sandbox function.

        combined_code = c_code
        test_harness_code = problem_json.get("test")  # Test harness or main function
        if isinstance(test_harness_code, str) and test_harness_code.strip():
            combined_code += test_harness_code
        elif debug and ("test" not in problem_json or not problem_json.get("test")):
            print("DEBUG [C Signature]: 'problem_json[\"test\"]' is missing or empty. "
                  "Running `c_code` which is expected to be a complete program for the sandbox.")

        # Call the user-provided run_code_snip function
        res = sandbox.run_code_snip(combined_code)

        compile_details = res.get("compile_result", {})
        execute_details = res.get("execute_result", {})

        # Check compilation result (return_code is a string "0" for success)
        if compile_details.get("return_code") != "0":
            if debug:
                print(f"DEBUG [C Signature]: Compilation FAILED.")
                print(f"  Compiler stdout: {compile_details.get('stdout', '')}")
                print(f"  Compiler stderr: {compile_details.get('stderr', '')}")
            return [-2]  # Compile error

        # Compilation succeeded, check execution result
        exec_return_code = execute_details.get("return_code")

        if exec_return_code == "0":
            # Execution successful (program exited with 0)
            expected_sig_output_str = problem_json.get("expected_signature_output")
            actual_stdout = execute_details.get("stdout", "")

            if expected_sig_output_str is not None:
                # Validate stdout if expected output is provided
                actual_lines_stripped = [line.strip() for line in actual_stdout.splitlines()]
                actual_lines_for_comparison = [line for line in actual_lines_stripped if
                                               line]  # Keep only non-empty stripped lines

                expected_lines_for_sig_cmp: List[str] = []
                if isinstance(expected_sig_output_str, list):
                    expected_lines_for_sig_cmp = [str(e).strip() for e in expected_sig_output_str if str(e).strip()]
                elif isinstance(expected_sig_output_str, str):
                    expected_lines_for_sig_cmp = [line.strip() for line in expected_sig_output_str.splitlines() if
                                                  line.strip()]

                # Perform comparison
                passed = (actual_lines_for_comparison == expected_lines_for_sig_cmp)
                # You could also use your custom_compare_ here if it's more appropriate:
                # expected_str_for_custom = expected_sig_output_str if isinstance(expected_sig_output_str, str) else "\n".join(expected_sig_output_str)
                # passed = custom_compare_(actual_lines_stripped, expected_str_for_custom)

                if debug:
                    print(f"DEBUG [C Signature]: Execution SUCCEEDED. Validating output.")
                    print(f"  Actual stdout (processed for cmp): {actual_lines_for_comparison}")
                    print(f"  Expected signature output (processed for cmp): {expected_lines_for_sig_cmp}")
                    print(f"  Comparison result: {passed}")
                return [passed]
            else:
                # No specific output to compare; exit code 0 from harness is considered success.
                if debug:
                    print(
                        f"DEBUG [C Signature]: Execution SUCCEEDED (exit code 0). No 'expected_signature_output' defined.")
                    print(f"  Stdout: {actual_stdout}")
                return [True]

        elif exec_return_code == "timeout":
            if debug:
                print(f"DEBUG [C Signature]: Execution TIMED OUT.")
                print(f"  Execute stderr: {execute_details.get('stderr', '')}")
            return [-1]  # Timeout error

        else:  # Any other non-"0" return_code from execution (e.g., "1", "139" for segfault)
            if debug:
                print(f"DEBUG [C Signature]: Execution FAILED (non-zero exit code or other error).")
                print(f"  Execute return_code: {exec_return_code}")
                print(f"  Execute stdout: {execute_details.get('stdout', '')}")
                print(f"  Execute stderr: {execute_details.get('stderr', '')}")
            return [-1]  # Runtime error

    else:  # Original stdio-based C execution logic
        results: List[Any] = []

        if "input_output" not in problem_json:
            if debug: print("DEBUG [C stdio]: 'input_output' key missing from problem_json.")
            return [-3]
        in_outs = problem_json["input_output"]
        if not isinstance(in_outs, dict) or "inputs" not in in_outs or "outputs" not in in_outs:
            if debug: print(
                "DEBUG [C stdio]: 'inputs' or 'outputs' key missing or invalid in problem_json['input_output'].")
            return [-3]

        num_inputs = len(in_outs.get("inputs", []))  # Use .get for safety
        if num_inputs > 0 and len(in_outs.get("outputs", [])) != num_inputs:
            if debug: print("DEBUG [C stdio]: Mismatch between number of inputs and outputs.")
            return [-3]

            # Ensure c_code includes the necessary headers provided by IMPORT_HELPER,
        # similar to how run_code_snip_provided_by_user does, or assume c_code is complete.
        # For consistency with the "signature" path, we can prepend them here too if not present.
        test_set_up_stdio = ""
        for s_import in sandbox.IMPORT_HELPER["c"]:
            if s_import not in c_code:
                test_set_up_stdio += s_import + "\n"

        c_code_full = test_set_up_stdio + f"""
// User's c_code:
{c_code}
// End of user's c_code
"""
        # Rest of the stdio C execution logic (compilation, iteration through test cases)
        # This part is copied from your provided snippet in the prompt, with minor safety checks.
        temp_dir = tempfile.mkdtemp()  # Consider using the same tmp_base_dir logic as in run_code_snip
        c_file_path = os.path.join(temp_dir, "solution.c")
        executable_name = "solution_executable"
        if os.name == 'nt':
            executable_name += ".exe"
        executable_path = os.path.join(temp_dir, executable_name)

        if debug:
            print(f"DEBUG [C stdio]: Temp dir: {temp_dir}")
            print(f"DEBUG [C stdio]: Writing C code to {c_file_path} (length: {len(c_code_full)})")  # Added length

        with open(c_file_path, "w", encoding="utf-8") as f:
            f.write(c_code_full)

        # Using same compile flags as run_code_snip for consistency
        compile_command = ["gcc", "-std=c11", "-D_POSIX_C_SOURCE=200809L", c_file_path, "-lm", "-o", executable_path,
                           "-Wall", "-O2"]
        if debug:
            print(f"DEBUG [C stdio]: Compiling with: {' '.join(compile_command)}")

        try:
            # Using timeout_seconds for compile, could be max(fixed_val, timeout_seconds*2)
            compile_proc = subprocess.run(
                compile_command, capture_output=True, text=True,
                timeout=max(6, timeout_seconds * 2),  # Match run_code_snip's compile timeout or make it configurable
                encoding='utf-8', errors='replace'
            )
        except subprocess.TimeoutExpired:
            if debug: print(f"DEBUG [C stdio]: Compilation TIMED OUT.")
            shutil.rmtree(temp_dir)
            return [-2] * (num_inputs if num_inputs > 0 else 1)

        if compile_proc.returncode != 0:
            if debug:
                print(f"DEBUG [C stdio]: Compilation FAILED. RC: {compile_proc.returncode}")
                print(f"DEBUG [C stdio]: Compiler stderr:\n{compile_proc.stderr}")
            shutil.rmtree(temp_dir)
            return [-2] * (num_inputs if num_inputs > 0 else 1)

        if debug: print(f"DEBUG [C stdio]: Compilation SUCCEEDED. Executable: {executable_path}")

        # If there are no inputs, but compilation succeeded, it's ambiguous.
        # Typically, competitive programming problems have at least one test case.
        # If num_inputs is 0, this loop won't run.
        if num_inputs == 0 and compile_proc.returncode == 0:
            if debug: print("DEBUG [C stdio]: No inputs to test, but compilation succeeded.")
            # Depending on requirements, this could be [True] (if just compilation check) or an empty list.
            # For now, assume if no inputs, and signature wasn't active, it's an empty test set for stdio.
            shutil.rmtree(temp_dir)
            return []  # No tests run

        for index, current_inputs_json in enumerate(in_outs.get("inputs", [])):
            if index >= len(in_outs.get("outputs", [])):  # Safety check
                if debug: print(f"DEBUG [C stdio]: Output missing for input TC #{index + 1}")
                results.append(-3)  # Config error
                continue
            expected_output_json = in_outs["outputs"][index]

            input_str = ""
            if isinstance(current_inputs_json, list):
                input_str = "\n".join(map(str, current_inputs_json))
            else:
                input_str = str(current_inputs_json)

            if debug:
                print(f"DEBUG [C stdio]: TC #{index + 1}, Input:\n'''{input_str}'''")

            try:
                # Using timeout_seconds for execution here. run_code_snip used a fixed 4.0s.
                run_proc = subprocess.run(
                    [executable_path], input=input_str, capture_output=True, text=True,
                    timeout=timeout_seconds,  # User-defined timeout for stdio path
                    encoding='utf-8', errors='replace'
                )

                if run_proc.returncode != 0:
                    if debug: print(
                        f"DEBUG [C stdio]: TC #{index + 1} Runtime Error. RC: {run_proc.returncode}. Stderr:\n{run_proc.stderr}")
                    results.append(-1)
                    continue

                actual_output_str = run_proc.stdout
                if debug: print(f"DEBUG [C stdio]: TC #{index + 1} Raw stdout:\n'''{actual_output_str}'''")

                actual_lines_stripped = [line.strip() for line in actual_output_str.splitlines()]
                actual_lines_for_comparison = [line for line in actual_lines_stripped if
                                               line]  # Keep only non-empty stripped lines

                tmp_result = False
                expected_lines = process_expected_output_for_comparison(expected_output_json, "list_of_strings")
                expected_str_custom = process_expected_output_for_comparison(expected_output_json,
                                                                             "string_for_custom_compare")

                if custom_compare_(actual_lines_stripped,
                                   expected_str_custom):  # Compare with potentially empty lines preserved by stripping
                    tmp_result = True

                if not tmp_result and actual_lines_for_comparison == expected_lines:  # Compare with empty lines removed
                    tmp_result = True

                if not tmp_result:  # Try float comparison
                    try:
                        actual_floats = [float(x) for x in actual_lines_for_comparison]
                        expected_floats_json_p = expected_output_json
                        if isinstance(expected_output_json, (str, int, float)):
                            expected_floats_json_p = [str(expected_output_json)]

                        expected_floats = [float(x) for x in
                                           process_expected_output_for_comparison(expected_floats_json_p,
                                                                                  "list_of_strings")]

                        if len(actual_floats) == len(expected_floats) and np.allclose(actual_floats, expected_floats):
                            tmp_result = True
                    except (ValueError, TypeError) as e:
                        if debug: print(f"DEBUG [C stdio]: Float conversion/comparison failed for TC #{index + 1}: {e}")
                        pass

                results.append(tmp_result)
                if debug:
                    status = "PASSED" if tmp_result else "FAILED"
                    print(f"DEBUG [C stdio]: TC #{index + 1} {status}.")
                    if not tmp_result:
                        print(f"  Actual (cmp): {actual_lines_for_comparison}, Expected (cmp): {expected_lines}")

            except subprocess.TimeoutExpired:
                if debug: print(f"DEBUG [C stdio]: TC #{index + 1} TIMED OUT.")
                results.append(-1)
            except Exception as e:
                if debug: print(f"DEBUG [C stdio]: EXCEPTION during C TC #{index + 1}: {e}")
                results.append(-1)

        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            if debug: print(f"DEBUG [C stdio]: Error cleaning up temp_dir {temp_dir}: {e}")

        return results


# --- Main run_test function, adapted ---
def run_test(problem: Dict[str, Any] | None = None,
             problem_list: List[str] | None = None,  # List of paths
             prob_index: int | None = None,
             test: str | None = None,  # Code string
             debug: bool = False,
             language: str = "python",  # Added language
             global_timeout: int = 5  # Used for both Python signal and C subprocess
             ) -> List[Any] | Dict[str, Any] | None:  # Return type can vary
    """
    If test is not None, it'll try to run the code.
    Otherwise, it'll just return an input and output pair (problem["input_output"]).
    """
    global timeout  # Access the global timeout for Python's signal.alarm
    timeout = global_timeout  # Set the global for Python part

    if test is None:
        if problem:
            return problem["input_output"]
        # Add logic here if you need to load 'problem' from problem_list and prob_index
        # For this example, assume 'problem' is provided if 'test' is None and data is expected.
        print("Error: 'problem' data must be provided if 'test' code is None and input_output is expected.")
        return None

    if not problem:
        print("Error: 'problem' data (including test cases) must be provided when 'test' code is given.")
        return []  # Return empty results for failure

    if language == "c":
        return run_c_test(problem_json=problem, c_code=test, debug=debug, timeout_seconds=global_timeout)

    elif language == "python":
        # ----- ORIGINAL PYTHON EXECUTION LOGIC STARTS HERE -----
        # This is your Python execution logic. Ensure all dependencies like
        # Capturing, CODE_TYPE, RuntimeModule, reliability_guard, signal, faulthandler,
        # call_method (and its mock dependencies) are correctly defined and available.
        if debug:
            print(f"PYTHON_RUN_TEST: start = {datetime.now().time()}")

        in_outs = problem["input_output"]
        reliability_guard()  # Python-specific reliability guard

        results: List[Any] = []
        # Standard library imports for the solution environment
        sol_imports = (
            "import sys\nimport time\nimport itertools\n"
            "from itertools import accumulate, product, permutations, combinations\n"
            "import collections\n"
            "from collections import Counter, OrderedDict, deque, defaultdict, ChainMap\n"
            "from functools import lru_cache\nimport math\n"
            "from math import sqrt, sin, cos, tan, ceil, fabs, floor, gcd, exp, log, log2\n"
            "import fractions\nfrom typing import List, Tuple\n"
            "import numpy as np\nimport random\nimport heapq\nfrom heapq import *\n"
        )

        if debug:
            print(f"PYTHON_RUN_TEST: loading test code = {datetime.now().time()}")

        # Determine Python code execution type (call-based or standard input)
        if in_outs.get("fn_name") is None:
            which_type = CODE_TYPE.standard_input
            method_name = "code"  # Default function name for standard input wrapper
        else:
            which_type = CODE_TYPE.call_based
            method_name = in_outs["fn_name"]

        tmp_sol_module: Any
        solution_instance_or_module: Any

        if which_type == CODE_TYPE.call_based:
            full_code = sol_imports + test
            if debug: print(f"PYTHON_RUN_TEST: Call-based full_code (first 100 chars): {full_code[:100]}...")

            signal.alarm(global_timeout)
            try:
                tmp_sol_module = RuntimeModule.from_string("tmp_sol", "", full_code)
                if "class Solution" not in test:  # Assuming direct functions in module
                    solution_instance_or_module = tmp_sol_module
                else:  # Assuming a class named Solution needs to be instantiated
                    solution_instance_or_module = tmp_sol_module.Solution()
                signal.alarm(0)  # Reset alarm after successful import/instantiation
            except Exception as e:
                signal.alarm(0)
                print(f"PYTHON_RUN_TEST: Type 0 (Call-based) compilation/instantiation error = {e}")
                # Fill results with -2 for all test cases on compilation error
                return [-2] * len(in_outs["inputs"])

        elif which_type == CODE_TYPE.standard_input:
            # Prepare the code for standard input execution
            # Original logic for wrapping stdin code into a 'code()' function
            tmp_test_lines = test.split("\n")
            new_test_lines = []
            for x_line in tmp_test_lines:
                if (not x_line.startswith("from ")) and (not x_line.startswith("import ")):
                    new_test_lines.append("\t" + x_line + "\n")
                else:
                    new_test_lines.append(x_line + "\n")

            wrapped_code_str = ""
            started_func = False
            for line_content in new_test_lines:
                if line_content.startswith("\t") and not started_func:
                    # These might not be necessary if call_method handles stdin/stdout redirection
                    # wrapped_code_str += "stdin = sys.stdin\nstdout = sys.stdout\n"
                    wrapped_code_str += "def code():\n"
                    wrapped_code_str += line_content
                    started_func = True
                # elif started_func and ((line_content.startswith("from ")) or (line_content.startswith("import "))):
                #     wrapped_code_str += "\t" + line_content # Indent imports if they are inside the function scope by mistake
                else:
                    wrapped_code_str += line_content

            # If no function was defined (e.g. test was empty or only imports)
            if not started_func:
                wrapped_code_str = "def code():\n\tpass\n" + wrapped_code_str

            full_code = sol_imports + wrapped_code_str
            if debug: print(f"PYTHON_RUN_TEST: Standard-input full_code (first 100 chars): {full_code[:100]}...")

            method_name = "code"  # The wrapper function
            signal.alarm(global_timeout)
            try:
                # For standard input, we compile the module and will call the 'code' function
                tmp_sol_module = RuntimeModule.from_string("tmp_sol", "", full_code)
                solution_instance_or_module = tmp_sol_module  # The module itself
                signal.alarm(0)
            except Exception as e:
                signal.alarm(0)
                print(f"PYTHON_RUN_TEST: Type 1 (Std-input) compilation error = {e}")
                return [-2] * len(in_outs["inputs"])

        if debug: print(f"PYTHON_RUN_TEST: get method = {datetime.now().time()}")

        try:
            method_to_call = getattr(solution_instance_or_module, method_name)
        except AttributeError as e:
            signal.alarm(0)  # Ensure alarm is off
            print(f"PYTHON_RUN_TEST: Unable to get function '{method_name}'. Error = {e}")
            return [-2] * len(in_outs["inputs"])  # Considered a setup/compilation type error

        # Loop through test cases
        for index, inputs_raw in enumerate(in_outs["inputs"]):
            current_inputs = inputs_raw  # Use directly, original processing for dict keys is kept
            expected_outputs_raw = in_outs["outputs"][index]

            # Original dict key processing (int keys)
            try:
                if isinstance(current_inputs, list) and current_inputs and isinstance(current_inputs[0], dict):
                    current_inputs = [{int(k): v for k, v in current_inputs[0].items()}]
            except:
                pass
            try:
                if isinstance(expected_outputs_raw, dict):
                    expected_outputs_raw = [{int(k): v for k, v in expected_outputs_raw.items()}]
                elif isinstance(expected_outputs_raw, list) and expected_outputs_raw and isinstance(
                        expected_outputs_raw[0], dict):
                    expected_outputs_raw = [{int(k): v for k, v in expected_outputs_raw[0].items()}]
            except:
                pass

            if debug:
                print(
                    f"PYTHON_RUN_TEST: time: {datetime.now().time()} testing index = {index}  inputs = {current_inputs}, type = {which_type}")

            actual_output: Any = None  # Stores output from Python code
            passed_this_test_case = False  # Flag for current test case

            if which_type == CODE_TYPE.call_based:
                signal.alarm(global_timeout)
                faulthandler.enable()
                try:
                    actual_output = method_to_call(*current_inputs)
                    if isinstance(actual_output, tuple):  # Convert tuples to lists for comparison
                        actual_output = list(actual_output)

                    tmp_result_compare = (actual_output == expected_outputs_raw)
                    # Original had more complex comparison logic for list vs list[list] etc.
                    if isinstance(expected_outputs_raw, list) and expected_outputs_raw:
                        # Handle cases like output being `X` vs expected `[X]`
                        if not isinstance(actual_output, list) or (
                                isinstance(actual_output, list) and len(actual_output) != len(
                                expected_outputs_raw) and len(expected_outputs_raw) == 1):
                            tmp_result_compare = tmp_result_compare or (actual_output == expected_outputs_raw[0])
                        # Handle [[1,2]] vs [1,2] if actual is [1,2] and expected is [[1,2]]
                        if isinstance(actual_output, list) and isinstance(expected_outputs_raw[0], list) and len(
                                expected_outputs_raw) == 1:
                            tmp_result_compare = tmp_result_compare or (actual_output == expected_outputs_raw[0])

                    # Ground truth sequences are not tuples (original comment)
                    try:
                        if isinstance(actual_output, list) and actual_output and isinstance(actual_output[0], tuple):
                            actual_output_list_of_lists = [list(x) for x in actual_output]
                            if isinstance(expected_outputs_raw, list) and len(expected_outputs_raw) == 1 and isinstance(
                                    expected_outputs_raw[0], list):
                                tmp_result_compare = tmp_result_compare or (
                                            actual_output_list_of_lists == expected_outputs_raw[0])
                            else:  # Compare against expected_outputs_raw directly if it's already a list of lists
                                tmp_result_compare = tmp_result_compare or (
                                            actual_output_list_of_lists == expected_outputs_raw)

                    except:
                        pass  # Ignore errors in this specific tuple conversion heuristic

                    results.append(tmp_result_compare)
                    passed_this_test_case = tmp_result_compare
                    signal.alarm(0)  # Reset alarm
                except Exception as e:
                    signal.alarm(0)
                    faulthandler.disable()
                    print(f"PYTHON_RUN_TEST (Call-based): Runtime error or time limit exceeded. Error = {e}")
                    results.append(-1)  # Runtime error or TLE
                    continue  # To next test case
                faulthandler.disable()
                if debug:
                    print(
                        f"PYTHON_RUN_TEST: Output = {actual_output}, Expected = {expected_outputs_raw}, Passed = {passed_this_test_case}")

            elif which_type == CODE_TYPE.standard_input:
                faulthandler.enable()
                signal.alarm(global_timeout)

                # Prepare inputs for standard input
                processed_input_str = ""
                if isinstance(current_inputs, list):  # Standard input is often a list of strings
                    processed_input_str = "\n".join(map(str, current_inputs))
                else:  # Or a single block of string
                    processed_input_str = str(current_inputs)

                # Prepare expected output string (original output format might be list or string)
                expected_output_str = ""
                if isinstance(expected_outputs_raw, list):
                    expected_output_str = "\n".join(map(str, expected_outputs_raw))
                else:
                    expected_output_str = str(expected_outputs_raw)

                captured_output_lines: List[str] = []
                runtime_passed = False
                try:
                    with Capturing() as captured_output_lines:  # Captures print statements
                        # call_method is a simplified dummy here.
                        # Original used unittest.mock to patch sys.stdin etc.
                        call_method(method_to_call, processed_input_str)
                    signal.alarm(0)  # Reset alarm
                    runtime_passed = True
                except Exception as e:
                    signal.alarm(0)
                    print(f"PYTHON_RUN_TEST (Std-input): Runtime error or time limit exceeded. Error = {repr(e)}")
                    results.append(-1)  # Runtime error or TLE
                    faulthandler.disable()
                    continue  # To next test case
                faulthandler.disable()

                if not runtime_passed:  # Should have been caught by except block, but as a safeguard
                    if debug: print(f"PYTHON_RUN_TEST: Not passed (runtime issue). Output: {captured_output_lines}")
                    continue

                if debug:
                    print(f"PYTHON_RUN_TEST: Captured output lines: {captured_output_lines}")
                    print(f"PYTHON_RUN_TEST: Expected output string: {expected_output_str}")

                # Comparison logic from original, using custom_compare_ and direct checks
                tmp_result_compare = False
                if custom_compare_(captured_output_lines, expected_output_str):
                    tmp_result_compare = True

                # ... (The extensive comparison logic from your original code would go here)
                # This includes various processing of `captured_output_lines` and `expected_outputs_raw`
                # (splitting, stripping, float conversion, set comparisons, etc.)
                # For brevity, I'm showing a simplified version.
                # You need to paste your full comparison chain here.
                # Example:
                if not tmp_result_compare:
                    # Convert captured_output_lines to a list of strings comparable to expected_outputs_raw (if it's a list)
                    processed_captured_output = [str(line).strip() for line in captured_output_lines]
                    processed_expected_output = []
                    if isinstance(expected_outputs_raw, list):
                        processed_expected_output = [str(line).strip() for line in expected_outputs_raw]
                    elif isinstance(expected_outputs_raw, str):  # If expected is a single string block
                        processed_expected_output = [line.strip() for line in expected_outputs_raw.splitlines()]

                    if processed_captured_output == processed_expected_output:
                        tmp_result_compare = True
                    # Try float comparison
                    elif not tmp_result_compare:
                        try:
                            actual_floats = [float(x) for x in processed_captured_output if x]  # Filter empty strings
                            expected_floats = [float(x) for x in processed_expected_output if x]
                            if len(actual_floats) == len(expected_floats) and np.allclose(actual_floats,
                                                                                          expected_floats):
                                tmp_result_compare = True
                        except (ValueError, TypeError):
                            pass  # Not float convertible

                results.append(tmp_result_compare)
                passed_this_test_case = tmp_result_compare
                if debug:
                    nl = "\\n"  # For printing newlines literally
                    print(
                        f"PYTHON_RUN_TEST: Final Cmp: Output = {nl.join(captured_output_lines)}, Expected = {expected_output_str.replace(chr(10), nl)}, Passed = {passed_this_test_case}")

        return results
        # ----- ORIGINAL PYTHON EXECUTION LOGIC ENDS HERE -----

    else:
        print(f"Error: Unsupported language '{language}'")
        return []


# --- Updated parse_args ---
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Utility for testing code generation.")
    parser.add_argument("-v", "--verbosity-level", action="store", type=int, help="Verbosity level.")
    parser.add_argument("-s", "--source", type=str, default="leetcode",
                        choices=["leetcode", "atcoder", "codewars", ],
                        help="Which data source to gather from.")
    parser.add_argument("-d", "--data", type=str, default="question",
                        choices=["question", "q", "solutions", "sol", "s", "starter", "tests", "t"],
                        help="Which type of data to receive.")
    parser.add_argument("-n", "--number", type=int, default=0, help="Which problem to query.")
    parser.add_argument("-l", "--language", type=str, default="python", choices=["python", "c"],
                        help="Language of the code to test (python or c).")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout in seconds for each test case execution.")

    args = parser.parse_args()
    return args


# --- Other functions from your script (get_valid_problems, get_question, get_solutions) ---
# These would remain largely unchanged unless they need to be language-aware for loading data.
# For example, get_solutions might load a C solution file if language is C.

def get_valid_problems(data_dir: str = "leetcode", current_args: argparse.Namespace | None = None) -> List[str]:
    # This is your original get_valid_problems.
    # It might need `current_args` if `args.source` is used inside.
    # For simplicity, I'm keeping its structure as provided.
    # root = os.path.join(args.source, "data") # Original used global args
    source_dir = current_args.source if current_args else data_dir  # Use arg if provided

    # If data_dir is a specific source like "leetcode", construct path to its "data" subdir
    # If data_dir is already the root of problems, use it directly.
    # This logic might need adjustment based on your directory structure.
    problems_root = os.path.join(source_dir, "data") if not os.path.isdir(os.path.join(data_dir, "data")) else data_dir
    if not os.path.exists(problems_root):  # if data_dir was 'leetcode', try 'leetcode/data'
        problems_root = os.path.join(data_dir, "data")

    valid_problems_json_path = os.path.join(data_dir, "valid_problems.json")  # Check in the source root

    if os.path.exists(valid_problems_json_path):
        with open(valid_problems_json_path, "r") as f:
            return json.load(f)

    tmp = os.listdir(problems_root)
    valid_probs = []
    for folder in tmp:
        prob_path = os.path.join(problems_root, folder)
        if not os.path.isdir(prob_path): continue  # Skip files, only look in folders
        files = os.listdir(prob_path)
        if "input_output.json" in files or "sols.json" in files:  # Your validity check
            valid_probs.append(prob_path)  # Store path to problem folder
    valid_probs = sorted(valid_probs)
    # with open(valid_problems_json_path, "w") as f: # Save if computed
    #    json.dump(valid_probs, f)
    return valid_probs


def get_question(problem_path: str) -> str:  # problem_path is path to specific problem folder
    # root = problem_list[prob_index] # Original
    question_path = os.path.join(problem_path, "question.txt")
    question_content = ""
    if os.path.exists(question_path):
        with open(question_path, "r", encoding="utf-8") as f:
            question_content = f.read()  # Read whole file is simpler
    else:
        print(f"Question prompt not found at {question_path}")
    return question_content


def get_solutions(problem_path: str) -> Dict[str, Any] | None:  # problem_path is path to specific problem folder
    # root = problem_list[prob_index] # Original
    solutions_path = os.path.join(problem_path, "solutions.json")  # Assuming Python solutions
    # Or, if C solutions are named differently, e.g., "solutions_c.json" or "main.c"
    # solutions_path_c = os.path.join(problem_path, "main.c") # Example for C source

    # This function needs to be language-aware if solution structure differs
    # For now, assumes solutions.json contains metadata or Python code
    sols = None
    if os.path.exists(solutions_path):
        with open(solutions_path, "r", encoding="utf-8") as f:
            sols = json.load(f)
    # else if language == 'c' and os.path.exists(solutions_path_c):
    #    with open(solutions_path_c, "r") as f:
    #        sols = {"c_source": f.read()} # Example structure
    return sols


# --- Example Main Execution ---
if __name__ == '__main__':
    # This is a dummy main for illustration.
    # Your actual main would call parse_args() and then use its values.
    current_args = parse_args()  # Get arguments from command line

    # --- Create Dummy Files and Folders for Testing ---
    # This setup is for the example to run.
    # You would have your actual LeetCode/AtCoder directory structure.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_source_dir = os.path.join(current_dir, current_args.source)  # e.g., ./leetcode
    dummy_data_dir = os.path.join(dummy_source_dir, "data")  # e.g., ./leetcode/data
    dummy_problem_folder = os.path.join(dummy_data_dir,
                                        f"problem_{current_args.number}")  # e.g., ./leetcode/data/problem_0

    os.makedirs(dummy_problem_folder, exist_ok=True)

    # Dummy input_output.json for the problem
    dummy_problem_data = {
        "input_output": {
            "inputs": [
                ["5", "1 2 3 4 5"],  # TC1: N, then N numbers for C; or single string "5\n1 2 3 4 5" for Python stdin
                ["3", "10 20 30"]  # TC2
            ],
            "outputs": [
                ["Sum: 15"],  # Expected for TC1
                ["Sum: 60"]  # Expected for TC2
            ],
            # "fn_name": None # For Python std_input or C
            "fn_name": "solve_sum"  # For Python call-based
        }
    }
    with open(os.path.join(dummy_problem_folder, "input_output.json"), "w") as f:
        json.dump(dummy_problem_data, f)

    # Dummy question.txt
    with open(os.path.join(dummy_problem_folder, "question.txt"), "w") as f:
        f.write("This is a dummy problem: sum N integers.")

    # Dummy C code to test (can be read from a file or passed as string)
    example_c_code = """
#include <stdio.h>
int main() {
    int n, i, sum = 0, val;
    // It's good practice to check scanf return values in real code
    if (scanf("%d", &n) != 1) return 1; // Basic error check
    for (i = 0; i < n; ++i) {
        if (scanf("%d", &val) != 1) return 1; // Basic error check
        sum += val;
    }
    printf("Sum: %d\\n", sum);
    return 0;
}
"""
    # Dummy Python code (call-based example)
    example_python_code_callbased = """
class Solution:
    def solve_sum(self, n_str, numbers_str): # fn_name is solve_sum
        n = int(n_str) # Input from JSON is list of strings usually
        numbers = list(map(int, numbers_str.split()))
        return [f"Sum: {sum(numbers)}"] # Output needs to match expected structure
"""
    # Dummy Python code (stdin-based example)
    example_python_code_stdin = """
n = int(input())
numbers = list(map(int, input().split()))
print(f"Sum: {sum(numbers)}")
"""

    # --- Load problem data ---
    # In a real script, you'd get a list of valid problem paths
    # valid_problem_paths = get_valid_problems(data_dir=dummy_source_dir, current_args=current_args)
    # problem_to_test_path = valid_problem_paths[current_args.number] # If 'number' is an index

    # For this example, we directly use the dummy_problem_folder path
    problem_to_test_path = dummy_problem_folder

    # Load the problem's input/output data
    # This assumes 'problem' dict is structured as {'input_output': {...}}
    # The run_test function expects 'problem' to be this dict.
    loaded_problem_dict: Dict[str, Any] = {}
    with open(os.path.join(problem_to_test_path, "input_output.json"), "r") as f:
        loaded_problem_dict = {"input_output": json.load(f)}

    # --- Select code to run based on language arg ---
    test_code_to_run = ""
    if current_args.language == "c":
        test_code_to_run = example_c_code
        # For C, fn_name is irrelevant, so ensure it's None for dummy_problem_data if testing C only.
        # Or, ensure the Python part handles fn_name: None correctly.
        # loaded_problem_dict["input_output"]["fn_name"] = None # If C test
    elif current_args.language == "python":
        # Choose between call-based or stdin for Python example
        # test_code_to_run = example_python_code_stdin
        # loaded_problem_dict["input_output"]["fn_name"] = None # For stdin Python
        test_code_to_run = example_python_code_callbased
        # fn_name is already "solve_sum" in dummy_problem_data for this example

    print(f"--- Testing Language: {current_args.language.upper()} ---")
    print(f"Problem: {problem_to_test_path}")
    # print(f"Code:\n{test_code_to_run[:200]}...\n") # Print start of code

    test_results = run_test(
        problem=loaded_problem_dict,  # Pass the loaded problem dictionary
        # problem_list=valid_problem_paths, # Not strictly needed if 'problem' is directly passed
        # prob_index=current_args.number,   # Not strictly needed if 'problem' is directly passed
        test=test_code_to_run,
        debug=True,  # current_args.verbosity_level > 0,
        language=current_args.language,
        global_timeout=current_args.timeout
    )
    print(f"\nFinal Test Results ({current_args.language.upper()}): {test_results}")

    # Clean up dummy directory
    # shutil.rmtree(dummy_source_dir)
    # print(f"Cleaned up dummy directory: {dummy_source_dir}")