from jinja2 import Template


template_string = """
You are an expert in translating complete Python function information into equivalent C versions.
Each sample includes a function prompt, signature, implementation, and test case.
Below are {{ k }} example translations:
{% for example in examples %}
Python:
[prompt]
{{ example.python_prompt }}
{% if example.python_signature %}
[signature]
{{ example.python_signature }}
{% endif %}
[code]
{{ example.python_code }}
[test_case]
{{ example.python_test }}
C:
[prompt]
{{ example.c_prompt }}
[signature]
{{ example.c_signature }}
[code]
{{ example.c_code }}
[test_case]
{{ example.c_test }}
{% endfor %}
Now translate the following Python function into its full C equivalent.
Python:
[prompt]
{{ target_python_prompt }}
[signature]
{{ target_python_signature }}
[code]
{{ target_python_code }}
[test_case]
{{ target_python_test }}
{% if previous_c_code %}
Note: The following C code and test was previously translated from the above Python code:
[previous_c_code]
{{ previous_c_code }}
[previous_c_test]
{{ previous_c_test }}
Its execution result was:
[run_feedback]
{{ run_feedback }}
First explain why the previous C code failed based on the feedback. 
Then fix any issues and regenerate **only** the corrected C translation, including:
- [prompt]
- [signature]
- [code]
- [test_case]
{% endif %}
**Important**: Do not add any explanations or comments after the [code] or [test_case] blocks.
Only output raw C code under the specified tags. This content will be compiled and executed directly.
C:
"""

template_apps_string = """
You are an expert in translating complete Python function information into equivalent C versions.
Each sample includes a function prompt, signature, implementation, and test case.
Below are {{ k }} example translations:
{% for example in examples %}
Python:
[prompt]
{{ example.python_prompt }}
{% if example.python_signature %}
[signature]
{{ example.python_signature }}
{% endif %}
[code]
{{ example.python_code }}
[test_case]
{{ example.python_test }}
C:
[signature]
{{ example.c_signature }}
[code]
{{ example.c_code }}
[test_case]
{{ example.c_test }}
{% endfor %}
Now translate the following Python function into its full C equivalent.
Python:
[prompt]
{{ target_python_prompt }}
[signature]
{% if target_python_signature %}
{{ target_python_signature }}
{% endif %}
[code]
{{ target_python_code }}
[test_case]
{{ target_python_test }}
{% if previous_c_code %}
Note: The following C code and test was previously translated from the above Python code:
[previous_c_code]
{{ previous_c_code }}
[previous_c_test]
{{ previous_c_test }}
Its execution result was:
[run_feedback]
{{ run_feedback }}
First explain why the previous C code failed based on the feedback. 
Then fix any issues and regenerate **only** the corrected C translation, including:
- [signature]
- [code]
- [test_case]
{% endif %}
**Important**: Do not add any explanations or comments after the [code] or [test_case] blocks.
Only output raw C code under the specified tags. This content will be compiled and executed directly.
C:
"""

template_lcb_string = """
You are an expert in translating Python function signature into equivalent C versions.
Each sample includes a function prompt, signature, implementation, and test case.
Below are {{ k }} example translations:
{% for example in examples %}
Python:
[prompt]
{{ example.python_prompt }}
{% if example.python_signature %}
[signature]
{{ example.python_signature }}
{% endif %}
[test]
{{ example.test }}
C:
[signature]
{{ example.c_signature }}
[code]
{{ example.c_code }}
[config]
{{ example.c_config }}
{% endfor %}
Now translate the following Python function into its full C equivalent.
Python:
[prompt]
{{ target_python_prompt }}
[signature]
{% if target_python_signature %}
{{ target_python_signature }}
{% endif %}
[test]
{{ target_python_test }}
{% if previous_c_code %}
Note: The following C code and test was previously translated from the above Python code:
[previous_c_code]
{{ previous_c_code }}
[previous_c_config]
{{ previous_c_config }}
Its execution result was:
[run_feedback]
{{ run_feedback }}
First explain why the previous C code failed based on the feedback. 
Then fix any issues and regenerate **only** the corrected C translation, including:
- [signature]
- [code]
- [config]
{% endif %}
**Important**: Do not add any explanations or comments after the [code] or [config] blocks.
Only output raw C code without main function under the specified tags.  
This generated function will be compiled and executed directly through the C types library.

Important notes about function parameters and return types:

1. If the return value is an array, the function parameter list does NOT need to include the return size parameter.

2. For parameters:

   - If a parameter is `char*` (a C string), **do NOT** include a length parameter after it.

   - If a parameter is `long*` (a one-dimensional integer array), the next parameter **must** be the length of this array (an `int`).

   - If a parameter is `char**` (an array of strings), the next parameter **must** be the length of this array (an `int`).

   - If a parameter is `long**` (a two-dimensional integer array), the next two parameters **must** be the number of rows and number of columns respectively (both `int`s).
Important:
All integers must be represented using long long instead of int, long, or other integer types. This ensures correctness and prevents overflow in large number calculations.

When using a char[] buffer to store formatted or concatenated integers (e.g., sprintf or snprintf), make sure the buffer size is sufficient to hold all digits and the null terminator.

Estimate total digit length using log10() if necessary.

A safe size for storing three integers (up to 4 digits each) concatenated as string is at least 16 bytes.

Avoid buffer overflows. Always use snprintf instead of sprintf if the buffer size is fixed.
Make sure to follow these conventions exactly in your function signature and implementation.C:
"""


translate_all_template = Template(template_string)
translate_apps_template = Template(template_apps_string)
translate_lcb_template = Template(template_lcb_string)